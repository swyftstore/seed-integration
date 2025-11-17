from google.cloud import bigquery
from google.oauth2 import service_account
from pandas_gbq import to_gbq

PROJECT_ID = "zoom-shops-dev"
DATASET_ID = "cantaloupe_seed"
KEY_PATH = "/Users/praveenkumar/Projects/Swyft/platform/misc/zoom-shops-dev-SA.json"

credentials = service_account.Credentials.from_service_account_file(KEY_PATH)

client = bigquery.Client(
    project=credentials.project_id,
    credentials=credentials
)

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
    ]

}

def load_markets_to_bigquery(dfs, if_exists="append"):
    for name, df in dfs.items():
        if df.empty:
            continue
        to_gbq(
            df,
            TABLES[name],
            project_id=PROJECT_ID,
            if_exists=if_exists
        )

def create_table(table_id: str):
    """
    Creates BigQuery table with given schema if it does not exist.
    """
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    expected_schema = SCHEMA_DATA.get(table_id)
    table = bigquery.Table(table_ref, schema=expected_schema)

    try:
        client.get_table(table_ref)
        print(f"✔ Table already exists: {table_ref}")
    except Exception:
        client.create_table(table)
        print(f"🆕 Created table: {table_ref}")

    # Existing fields
    existing_fields = {field.name.lower(): field for field in table.schema}

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
        print(f"✔ Updated schema for {table_ref}")
    else:
        print(f"✔ Schema already up to date: {table_ref}")

if __name__ == "__main__":
    create_table("vdi_markets_info")
    create_table("vdi_products")
