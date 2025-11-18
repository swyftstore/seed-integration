import html
import xml.etree.ElementTree as ET
import pandas as pd
import xml.sax.saxutils as sax
from datetime import datetime, timezone

dry_run = True

def get_seed_timestamp():
    # datetime with microseconds → pad to 7 digits
    now = datetime.now(timezone.utc)
    # format: YYYY-MM-DDTHH:MM:SS.microseconds + one extra 0 + Z
    # return now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z"
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_kiosk_soap():
    utc_now = get_seed_timestamp()
    xml_version = 1
    xml_type = "mms-kiosks"
    provider_id = "swyft"
    application_id = "swyft-vdi-integration"
    application_version = "1.0"
    transaction_id = "e3c9a5b2-7f92-4c51-9ac9-223b7df963af"
    transaction_time = "2025-11-18T07:04:06.4288410Z"
    operator_id = "nm_swyft"
    market_id = "2"
    kiosk_id = "PY-KIOSK"
    kiosk_sn = "PY0001"
    kiosk_last_sync = "2025-11-18T07:04:06.4288410Z"
    kiosk_last_transaction = "2025-11-18T07:04:06.4288410Z"
    kiosk_catalog_version = "2025-11-18T07:04:06.4288410Z"

    soap_xml = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:VDIDataExchangeService">
        <soapenv:Header/>
        <soapenv:Body>
            <VDIDataExchange xmlns="urn:VDIDataExchangeService" xmlns:ns2="http://schemas.microsoft.com/2003/10/Serialization/">
                <VDIXMLVersion>{xml_version}</VDIXMLVersion>
                <VDIXMLType>{xml_type}</VDIXMLType>
                <ProviderID>{provider_id}</ProviderID>
                <ApplicationID>{application_id}</ApplicationID>
                <ApplicationVersion>{application_version}</ApplicationVersion>
                <TransactionID>{transaction_id}</TransactionID>
                <TransactionTime>{transaction_time}</TransactionTime>
                <OperatorID>{operator_id}</OperatorID>

                <CompressionType xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
                <CompressionParam xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
                <Encoding>utf-8</Encoding>

                <VDIXML xmlns:ns3="urn:VDIDataExchangeService">&lt;?xml version=&quot;1.0&quot; encoding=&quot;utf-8&quot;?&gt;
    &lt;VDITransaction xmlns:xsd=&quot;http://www.w3.org/2001/XMLSchema&quot; VDIXMLVersion=&quot;{xml_version}&quot; VDIXMLType=&quot;{xml_type}&quot; ProviderID=&quot;{provider_id}&quot; ApplicationID=&quot;{application_id}&quot; ApplicationVersion=&quot;{application_version}&quot; TransactionID=&quot;{transaction_id}&quot; TransactionTime=&quot;{transaction_time}&quot; OperatorID=&quot;{operator_id}&quot;&gt;
        &lt;KiosksCollection&gt;
            &lt;Kiosk MarketID=&quot;{market_id}&quot; KioskID=&quot;{kiosk_id}&quot; KioskSN=&quot;{kiosk_sn}&quot; LastSync=&quot;{kiosk_last_sync}&quot; LastTransaction=&quot;{kiosk_last_transaction}&quot; CatalogVersion=&quot;{kiosk_catalog_version}&quot; /&gt;
        &lt;/KiosksCollection&gt;
    &lt;/VDITransaction&gt;</VDIXML>

                <UserData xmlns:ns3="urn:VDIDataExchangeService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
            </VDIDataExchange>
        </soapenv:Body>
    </soapenv:Envelope>
    """
    return soap_xml


def save_df(df, name):
    """
    Save a pandas DataFrame to a CSV file with the given name.
    """
    if not name.endswith(".csv"):
        name = f"{name}.csv"
    fp = f"data/{name}"
    df.to_csv(fp, index=False)

def parse_seed_markets_soap(xml_text: str):
    """
    Parse Seed SOAP markets response:
    - Extract <VDIXML> inner escaped XML
    - Parse mms-markets VDITransaction
    Returns two DataFrames:
      1. transaction_df
      2. markets_df
    """

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
    vdi_xml_el = root.find(".//v:VDIXML", ns)
    if vdi_xml_el is None:
        raise ValueError("Cannot find <VDIXML> inside SOAP response")

    inner_xml_escaped = vdi_xml_el.text
    if inner_xml_escaped is None:
        raise ValueError("VDIXML node exists but contains no XML")

    # Unescape & parse inner VDITransaction XML
    inner_xml = html.unescape(inner_xml_escaped)
    inner_root = ET.fromstring(inner_xml)

    # Extract transaction-level info
    tx = {
        "VDIXMLVersion": inner_root.attrib.get("VDIXMLVersion"),
        "VDIXMLType": inner_root.attrib.get("VDIXMLType"),
        "ProviderID": inner_root.attrib.get("ProviderID"),
        "ApplicationID": inner_root.attrib.get("ApplicationID"),
        "ApplicationVersion": inner_root.attrib.get("ApplicationVersion"),
        "OperatorID": inner_root.attrib.get("OperatorID"),
        "TransactionID": inner_root.attrib.get("TransactionID"),
        "TransactionTime": inner_root.attrib.get("TransactionTime"),
    }

    transaction_df = pd.DataFrame([tx])
    if dry_run:
        save_df(transaction_df, 'mms-markets-transaction')

    # Extract Markets
    markets = []
    markets_el = inner_root.find("MarketsCollection")

    if markets_el is not None:
        for m in markets_el.findall("Market"):
            markets.append({
                "TransactionID": tx["TransactionID"],
                "MarketID": m.attrib.get("MarketID"),
                "MarketName": m.attrib.get("MarketName"),
                "MarketAddress": m.attrib.get("MarketAddress"),
                "MarketLocation": m.attrib.get("MarketLocation"),
                "ClientID": m.attrib.get("ClientID"),
                "ClientName": m.attrib.get("ClientName"),
            })

    markets_df = pd.DataFrame(markets)
    if dry_run:
        save_df(markets_df, 'mms-markets-markets')

    return {
        "transaction": transaction_df,
        "markets": markets_df
    }

def parse_seed_products_soap(xml_text: str):
    """
    Parse SEED SOAP response containing mms-products.
    Extracts:
      - transaction
      - per-market products
      - product codes
      - taxes
      - fees
    """

    xml_text = xml_text.strip()

    # Namespaces
    ns = {
        "s": "http://schemas.xmlsoap.org/soap/envelope/",
        "v": "urn:VDIDataExchangeService"
    }

    # Parse SOAP Envelope
    root = ET.fromstring(xml_text)

    # Extract the escaped inner VDI XML
    vdi_xml_el = root.find(".//v:VDIXML", ns)
    if vdi_xml_el is None:
        raise ValueError("Cannot find <VDIXML> inside SOAP response")

    escaped_inner_xml = vdi_xml_el.text
    if not escaped_inner_xml:
        raise ValueError("<VDIXML> exists but is empty")

    # Unescape & parse actual mms-products XML
    inner_xml = html.unescape(escaped_inner_xml)
    inner_root = ET.fromstring(inner_xml)

    # ---------------------------
    # 1) Transaction metadata
    # ---------------------------
    tx = {
        "VDIXMLVersion": inner_root.attrib.get("VDIXMLVersion"),
        "VDIXMLType": inner_root.attrib.get("VDIXMLType"),
        "ProviderID": inner_root.attrib.get("ProviderID"),
        "ApplicationID": inner_root.attrib.get("ApplicationID"),
        "ApplicationVersion": inner_root.attrib.get("ApplicationVersion"),
        "OperatorID": inner_root.attrib.get("OperatorID"),
        "TransactionID": inner_root.attrib.get("TransactionID"),
        "TransactionTime": inner_root.attrib.get("TransactionTime"),
    }

    transaction_df = pd.DataFrame([tx])
    if dry_run:
        save_df(transaction_df, 'mms-products-transaction')

    markets = []
    products = []
    product_codes = []
    product_taxes = []
    product_fees = []

    # ---------------------------
    # 2) Extract MarketsCollection
    # ---------------------------
    markets_el = inner_root.find("MarketsCollection")
    if markets_el is None:
        raise ValueError("No <MarketsCollection> in the inner VDI XML")

    for market_el in markets_el.findall("Market"):
        market_id = market_el.attrib.get("MarketID")
        catalog_size = market_el.attrib.get("CatalogSize")

        # Market row — products vary per market!
        markets.append({
            "TransactionID": tx["TransactionID"],
            "MarketID": market_id,
            "CatalogSize": catalog_size
        })

        products_update_el = market_el.find("ProductsUpdate")
        if products_update_el is None:
            continue

        # ---------------------------
        # 3) Products per market
        # ---------------------------
        for prod_el in products_update_el.findall("Product"):
            product_id = prod_el.attrib.get("ProductID")

            products.append({
                "TransactionID": tx["TransactionID"],
                "MarketID": market_id,
                "ProductID": product_id,
                "ProductName": prod_el.attrib.get("ProductName"),
                "Price": float(prod_el.attrib.get("Price")) if prod_el.attrib.get("Price") else None,
                "Cost": float(prod_el.attrib.get("Cost")) if prod_el.attrib.get("Cost") else None,
                "ProductCode": prod_el.attrib.get("ProductCode"),
                "Category": prod_el.attrib.get("Category"),
            })

            # ---------------------------
            # 4) Codes (barcodes)
            # ---------------------------
            codes_el = prod_el.find("Codes")
            if codes_el is not None:
                for code in codes_el.findall("Code"):
                    product_codes.append({
                        "TransactionID": tx["TransactionID"],
                        "MarketID": market_id,
                        "ProductID": product_id,
                        "Code": (code.text or "").strip()
                    })

            # ---------------------------
            # 5) Taxes
            # ---------------------------
            taxes_el = prod_el.find("Taxes")
            if taxes_el is not None:
                for tax in taxes_el.findall("Tax"):
                    product_taxes.append({
                        "TransactionID": tx["TransactionID"],
                        "MarketID": market_id,
                        "ProductID": product_id,
                        "TaxID": tax.attrib.get("ID"),
                        "TaxName": tax.attrib.get("Name"),
                        "TaxRate": float(tax.attrib.get("Rate")) if tax.attrib.get("Rate") else None,
                        "IncludedInPrice": int(tax.attrib.get("IncludedInPrice")) if tax.attrib.get("IncludedInPrice") else None,
                    })

            # ---------------------------
            # 6) Fees
            # ---------------------------
            fees_el = prod_el.find("Fees")
            if fees_el is not None:
                for fee in fees_el.findall("Fee"):
                    product_fees.append({
                        "TransactionID": tx["TransactionID"],
                        "MarketID": market_id,
                        "ProductID": product_id,
                        "FeeID": fee.attrib.get("ID"),
                        "FeeName": fee.attrib.get("Name"),
                        "FeeValue": float(fee.attrib.get("Value")) if fee.attrib.get("Value") else None,
                        "IsTaxable": fee.attrib.get("IsTaxable") == "true"
                    })

    # Convert to DataFrames
    markets_df = pd.DataFrame(markets)
    products_df = pd.DataFrame(products)
    product_codes_df = pd.DataFrame(product_codes)
    product_taxes_df = pd.DataFrame(product_taxes)
    product_fees_df = pd.DataFrame(product_fees)

    if dry_run:
        save_df(markets_df, 'mms-products-markets')
        save_df(products_df, 'mms-products-products')
        save_df(product_codes_df, 'mms-products-codes')
        save_df(product_taxes_df, 'mms-products-taxes')
        save_df(product_fees_df, 'mms-products-fees')

    return {
        "transaction": transaction_df,
        "markets": markets_df,
        "products": products_df,
        "product_codes": product_codes_df,
        "product_taxes": product_taxes_df,
        "product_fees": product_fees_df,
    }

# Example run
if __name__ == "__main__":
    # soap_input = None
    # fp = "payloads/market.xml"
    # # fp = "payloads/products.xml"
    # with open(fp) as f:
    #     soap_input = f.read()

    # result = parse_seed_markets_soap(soap_input)
    # for name, df in result.items():
    #     print("\n----", name, "----")
    #     print(df)

    # dfs = parse_seed_products_soap(soap_input)
    # for name, df in dfs.items():
    #     print(name, df.head())

    # data = generate_kiosk_soap()
    # with open('data/mms-kiosks.xml', 'w') as f:
    #     f.write(data)

    print(get_seed_timestamp())
