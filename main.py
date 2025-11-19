from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import Response

import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
from utils import parse_seed_markets_soap, parse_seed_products_soap

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
        # Ensure proper XML formatting
        xml_text = xml_text.strip()

        # Parse SOAP envelope
        root = ET.fromstring(xml_text)
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
            parse_seed_markets_soap(xml_str)

        elif vdi_type == "mms-products":
            parse_seed_products_soap(xml_str)

        else:
            print(f"⚠️ Unknown VDI Type: {vdi_type}")

        # Respond OK
        response_xml = """
        <?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
            <VDIDataExchangeResponse xmlns="urn:VDIDataExchangeService">
                <VDIDataExchangeResult>
                <ResultCode>0</ResultCode>
                <ResultDescription>OK</ResultDescription>
                </VDIDataExchangeResult>
            </VDIDataExchangeResponse>
            </soap:Body>
        </soap:Envelope>
        """

        return Response(content=response_xml, media_type="text/xml")
    except Exception as e:
        print("❌ XML Parse Error:", e)
        raise HTTPException(status_code=400, detail="Invalid XML")


@app.get("/")
def root():
    return {"status": "Seed VDI receiver is up"}
