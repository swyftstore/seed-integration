from google.cloud import bigquery
from google.oauth2 import service_account
from pandas_gbq import to_gbq

PROJECT_ID = "zoom-shops-dev"
DATASET_ID = "cantaloupe_seed"
KEY_PATH = "/Users/praveenkumar/Projects/Swyft/platform/misc/zoom-shops-dev-SA.json"

MAKETS_TABLE = "vdi_markets_info"
PRODUCTS_TABLE = "vdi_products"

client = bigquery.Client(project=PROJECT_ID)

TABLES = {
    "vdi_markets_info": f"{PROJECT_ID}.{DATASET_ID}.vdi_markets_info",
    "vdi_products": f"{PROJECT_ID}.{DATASET_ID}.vdi_products"
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

if __name__ == "__main__":
    create_table("vdi_markets_info")
    create_table("vdi_products")
