from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import Response
from lxml import etree
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Seed VDI Receiver", version="1.0")

security = HTTPBasic()

VALID_USER = os.getenv("VDI_USER")
VALID_PASS = os.getenv("VDI_PASS")

# ---------- BASIC AUTH ----------
def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == VALID_USER and credentials.password == VALID_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username


# ---------- SOAP HANDLER ----------
@app.post("/vdi/seed", response_class=Response)
async def receive_vdi(request: Request, user: str = Depends(verify_auth)):
    body = await request.body()
    xml_str = body.decode("utf-8")
    print(xml_str)

    try:
        root = etree.fromstring(xml_str.encode())
        vdi_type = root.attrib.get("VDIXMLType", "unknown")
        print(f"📩 Received VDI Type: {vdi_type}")

        if vdi_type == "mms-markets":
            markets = root.findall(".//Market")
            for m in markets:
                attributes = m.attrib
                market_id = attributes.get("MarketID")
                market_name = attributes.get("MarketName")
                client_id = attributes.get("ClientID")
                client_name = attributes.get("ClientName")
                print(f"  → Market: {market_id} | {market_name}")
                print(f"  → Client: {client_id} | {client_name}")

        elif vdi_type == "mms-products":
            products = root.findall(".//Product")
            print(f"  → Received {len(products)} products")

        else:
            print(f"⚠️ Unknown VDI Type: {vdi_type}")

        # Respond OK
        response_xml = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <VDIResponse>
              <ResultCode>0</ResultCode>
              <ResultDescription>OK</ResultDescription>
            </VDIResponse>
          </soap:Body>
        </soap:Envelope>"""

        return Response(content=response_xml, media_type="text/xml")

    except Exception as e:
        print("❌ XML Parse Error:", e)
        raise HTTPException(status_code=400, detail="Invalid XML")


@app.get("/")
def root():
    return {"status": "Seed VDI receiver is up"}
