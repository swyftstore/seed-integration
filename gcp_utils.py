from google.cloud import bigquery
from google.oauth2 import service_account
from pandas_gbq import to_gbq
from datetime import datetime, timezone


PROJECT_ID = "zoom-shops-dev"
SWYFT_DATASET_ID = "zoom_dw_dev"
SEED_DATASET_ID = "cantaloupe_seed"
KEY_PATH = "/Users/praveenkumar/Projects/Swyft/platform/misc/zoom-shops-dev-SA.json"

MAKETS_TABLE = "vdi_markets_info"
PRODUCTS_TABLE = "vdi_products"

client = bigquery.Client(project=PROJECT_ID)

TABLES = {
    "vdi_markets_info": f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_markets_info",
    "vdi_products": f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_products",
    "vdi_store_market_mapping": f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping"
}

SCHEMA_DATA = {
    # ------------------------------
    # mms-markets: market info
    # ------------------------------
    "vdi_markets_info":
    [
        bigquery.SchemaField("TransactionID", "STRING"),
        bigquery.SchemaField("MarketID", "STRING"),
        bigquery.SchemaField("MarketName", "STRING"),
        bigquery.SchemaField("MarketAddress", "STRING"),
        bigquery.SchemaField("MarketLocation", "STRING"),
        bigquery.SchemaField("ClientID", "STRING"),
        bigquery.SchemaField("ClientName", "STRING"),
    ],

    # ------------------------------
    # mms-products: products
    # ------------------------------
    "vdi_products":
    [
        bigquery.SchemaField("TransactionID", "STRING"),
        bigquery.SchemaField("MarketID", "STRING"),
        bigquery.SchemaField("ProductID", "STRING"),
        bigquery.SchemaField("ProductName", "STRING"),
        bigquery.SchemaField("Price", "FLOAT"),
        bigquery.SchemaField("Cost", "FLOAT"),
        bigquery.SchemaField("ProductCode", "STRING"),
        bigquery.SchemaField("Category", "STRING"),
        bigquery.SchemaField("Code", "STRING"),
        bigquery.SchemaField("TaxID", "STRING"),
        bigquery.SchemaField("TaxName", "STRING"),
        bigquery.SchemaField("TaxRate", "FLOAT"),
        bigquery.SchemaField("IncludedInPrice", "FLOAT"),
        bigquery.SchemaField("FeeID", "STRING"),
        bigquery.SchemaField("FeeName", "STRING"),
        bigquery.SchemaField("FeeValue", "FLOAT"),
        bigquery.SchemaField("IsTaxable", "BOOLEAN")
    ],

    # ------------------------------
    # vdi_store_market_mapping: store market mapping
    # ------------------------------
    "vdi_store_market_mapping":
    [
        bigquery.SchemaField("estation_name", "STRING"),
        bigquery.SchemaField("market_id", "STRING"),
        bigquery.SchemaField("updated_at", "TIMESTAMP"),
        bigquery.SchemaField("updated_by", "STRING"),
        bigquery.SchemaField("deleted", "TIMESTAMP"),
        bigquery.SchemaField("action", "STRING")
    ]

}

def load_to_bigquery(table_id, df):
    if df.empty:
        return
    
    # ensure table exists before adding data
    create_table(table_id)

    # add the data into temp table before merging it into actual
    temp_table_id = f"{table_id}_temp"

    # STEP 1: Upload dataframe to temporary table
    df.to_gbq(
        temp_table_id,
        project_id=PROJECT_ID,
        if_exists="replace"   # <-- creates it automatically
    )

    # STEP 2: MERGE
    key_columns = None
    if MAKETS_TABLE in table_id:
        key_columns = ['MarketID']
    elif PRODUCTS_TABLE in table_id:
        key_columns = ['MarketID', 'ProductID']
    if key_columns is None:
        print("could not identify the key column for table id: %s" % table_id)
        return
    
    # Build the ON clause dynamically
    on_clause = " AND ".join([f"T.{col} = S.{col}" for col in key_columns])

    # Build MERGE SQL
    merge_sql = f"""
    MERGE `{table_id}` T
    USING `{temp_table_id}` S
    ON {on_clause}
    WHEN NOT MATCHED THEN
      INSERT ROW;
    """

    client.query(merge_sql).result()
    print("Composite-key MERGE complete.")

    client.delete_table(temp_table_id, not_found_ok=True)
    print("Deleted the temp table: %s" % temp_table_id)

def create_table(table_id: str):
    """
    Creates BigQuery table with given schema if it does not exist.
    """
    table_name = table_id.split(".")[-1]
    expected_schema = SCHEMA_DATA.get(table_name)
    table = bigquery.Table(table_id)

    try:
        client.get_table(table_id)
        print(f"✔ Table already exists: {table_id}")
    except Exception:
        client.create_table(table)
        print(f"🆕 Created table: {table_id}")

    # Existing fields
    existing_fields = {field.name.lower(): field for field in table.schema}
    print("Existing fields: ", existing_fields)

    # Columns to add
    new_fields = []

    for field in expected_schema:
        if field.name.lower() not in existing_fields:
            print(f"➕ Adding missing column: {field.name}")
            new_fields.append(field)

    if new_fields:
        updated_schema = table.schema + new_fields
        table.schema = updated_schema
        client.update_table(table, ["schema"])
        print(f"✔ Updated schema for {table_id}")
    else:
        print(f"✔ Schema already up to date: {table_id}")

def bq_get_stores():
    query = f"SELECT concept_name, estation_name FROM {PROJECT_ID}.{SWYFT_DATASET_ID}.07_live_stores ORDER BY estation_name limit 10"
    df = client.query(query).to_dataframe()
    records = df.to_dict(orient="records")
    return records

def bq_get_markets():
    query = f"SELECT MarketID as market_id, MarketName as market_name FROM {PROJECT_ID}.{SEED_DATASET_ID}.{MAKETS_TABLE} ORDER BY market_name"
    df = client.query(query).to_dataframe()
    records = df.to_dict(orient="records")
    return records

def save_store_market_mapping(store_id, market_id):
    rows = [{
        "estation_name": store_id,
        "market_id": market_id,
        "updated_at": datetime.now(),
        "updated_by": "system"
    }]
    response = client.insert_rows_json(f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping", rows)
    return response

def get_active_store_mapping(store_id):
    query = f"""
    SELECT market_id 
    FROM `{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping` 
    WHERE estation_name = @store_id AND deleted IS NULL 
    QUALIFY ROW_NUMBER() OVER (PARTITION BY estation_name ORDER BY updated_at DESC) = 1 
    """
    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("store_id", "STRING", store_id)
    ])
    rows = list(client.query(query, job_config))
    market_id = rows[0].market_id if rows else None
    print("store: %s mapped to market: %s" % (store_id, market_id))
    return market_id

def delete_store_market_mapping(store_id, user_email, user_role):
    if user_role != "admin":
        return {"status": "blocked", "reason": "Admin only"}

    now_ts = datetime.now(timezone.utc).isoformat()

    existing_market = get_active_store_mapping(store_id)
    if not existing_market:
        return {"status": "not_found"}

    client.insert_rows_json(
        f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping",
        [{
            "estation_name": store_id,
            "market_id": existing_market,
            "updated_by": user_email,
            "updated_at": now_ts,
            "deleted": now_ts,
            "action": "DELETE"
        }]
    )
    return {"status": "deleted", "store": store_id}

def save_store_market_mapping(store_id, market_id, user_email, user_role):
    now_ts = datetime.now(timezone.utc).isoformat()

    existing_market = get_active_store_mapping(store_id)

    if existing_market and market_id == existing_market:
        return {
            "status": "Mapped Exists !!!"
        }


    # ❌ Viewer cannot overwrite
    if existing_market and user_role != 'admin':
        return {
            "status": "blocked",
            "reason": f"Store already mapped to {existing_market}"
        }

    # SOFT DELETE OLD MAPPING (append-only marker)
    if existing_market:
        client.insert_rows_json(
            f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping",
            [{
                "estation_name": store_id,
                "market_id": existing_market,
                "updated_by": user_email,
                "updated_at": now_ts,
                "deleted": now_ts,
                "action": "DELETE"
            }]
        )

    # ➕ INSERT NEW ACTIVE ROW
    client.insert_rows_json(
        f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping",
        [{
            "estation_name": store_id,
            "market_id": market_id,
            "updated_by": user_email,
            "updated_at": now_ts,
            "deleted": None,
            "action": "INSERT"
        }]
    )

    return {
        "status": "SUCCESS",
        "store": store_id,
        "market": market_id
    }

def get_store_market_mappings_current():
    query = f"""
    SELECT
      estation_name,
      market_id,
      updated_by,
      updated_at
    FROM `{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping_current`
    ORDER BY updated_at DESC
    """
    rows = client.query(query)
    return [dict(r) for r in rows]

if __name__ == "__main__":
    create_table(f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_markets_info")
    create_table(f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_products")
    create_table(f"{PROJECT_ID}.{SEED_DATASET_ID}.vdi_store_market_mapping")
