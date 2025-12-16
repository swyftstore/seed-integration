from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
from utils import parse_seed_markets_soap, parse_seed_products_soap
from gcp_utils import TABLES, load_to_bigquery, bq_get_markets, bq_get_stores, save_store_market_mapping, get_store_market_mappings_current, delete_store_market_mapping

load_dotenv()

app = FastAPI(title="Seed VDI Receiver", version="1.0")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBasic()

VALID_USER = os.getenv("VDI_USER")
VALID_PASS = os.getenv("VDI_PASS")

# ---------- BASIC AUTH ----------
def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == VALID_USER and credentials.password == VALID_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

@app.get("/ui/store-market-map")
def store_market_map_page(request: Request):
    return templates.TemplateResponse(
        "store_market_map.html",
        {"request": request}
    )

@app.get("/stores")
def get_stores():
    data = bq_get_stores()
    return data

@app.get("/markets")
def get_markets():
    data = bq_get_markets()
    return data

@app.post("/store-market-map")
def save_map(payload: dict):
    estation_name = payload["estation_name"]
    market_id = payload["market_id"]
    user_email = "praveen@swyft.com" # payload["user_email"]
    user_role = "admin" # payload["user_role"]

    errors = save_store_market_mapping(estation_name, market_id, user_email, user_role)
    return errors

@app.get("/store-market-map/current")
def get_current_mappings(request: Request):
    # user = verify_token(request)

    return get_store_market_mappings_current()

@app.post("/store-market-map/delete")
def delete_mapping(request: Request, payload: dict):
    # user = verify_token(request)
    # if user["role"] != "admin":
    #     raise HTTPException(403, "Admin only")

    store_id = payload["store_name"]
    user_email = "praveen.yalal@swyft.com" # user["email"]
    user_role = "admin" # user["role"]

    return delete_store_market_mapping(store_id, user_email, user_role)


# ---------- SOAP HANDLER ----------
@app.post("/vdi/seed", response_class=Response)
async def receive_vdi(request: Request, user: str = Depends(verify_auth)):
    body = await request.body()
    xml_str = body.decode("utf-8")
    print(xml_str)

    try:
        # Ensure proper XML formatting
        xml_str = xml_str.strip()

        # Parse SOAP envelope
        root = ET.fromstring(xml_str)
            # Namespaces
        ns = {
            "s": "http://schemas.xmlsoap.org/soap/envelope/",
            "v": "urn:VDIDataExchangeService"
        }
        # Extract the inner <VDIXML> block from SOAP
        vdixml_type_el = root.find(".//v:VDIXMLType", ns)
        if vdixml_type_el is None:
            raise ValueError("Cannot find <VDIXMLType> inside SOAP response")

        vdi_type = vdixml_type_el.text
        print(f"📩 Received VDI Type: {vdi_type}")

        if vdi_type == "mms-markets":
            data = parse_seed_markets_soap(xml_str)
            markets_df = data['markets']
            table_id = TABLES.get("vdi_markets_info")
            load_to_bigquery(table_id, markets_df)

        elif vdi_type == "mms-products":
            data = parse_seed_products_soap(xml_str)
            products_df = data["products"]
            product_codes = data["product_codes"]
            product_taxes = data["product_taxes"]
            product_fees = data['product_fees']

            keys = ["MarketID", "ProductID", "TransactionID"]
            
            merge_df = products_df.merge(product_codes, on=keys, how="inner")
            merge_df = merge_df.merge(product_taxes, on=keys, how="inner")
            merge_df = merge_df.merge(product_fees, on=keys, how="inner")
            # do type-conversions
            merge_df['FeeID'] = merge_df['FeeID'].astype(str)
            merge_df['TaxID'] = merge_df['TaxID'].astype(str)
            # get table id
            table_id = TABLES.get("vdi_products")
            load_to_bigquery(table_id, merge_df)
        else:
            print(f"⚠️ Unknown VDI Type: {vdi_type}")

        # Respond OK
        response_xml = """
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <VDIDataExchangeResponse xmlns="urn:VDIDataExchangeService">
                    <VDIDataExchangeResult>SUCCESS</VDIDataExchangeResult>
                </VDIDataExchangeResponse>
            </s:Body>
        </s:Envelope>
        """

        return Response(content=response_xml, media_type="text/xml")
    except Exception as e:
        print("❌ XML Parse Error:", e)
        raise HTTPException(status_code=400, detail="Invalid XML")


@app.get("/")
def root():
    return {"status": "Seed VDI receiver is up"}
