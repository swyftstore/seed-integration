import html
import xml.etree.ElementTree as ET
import pandas as pd

dry_run = True


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
    soap_input = None
    fp = "payloads/market.xml"
    # fp = "payloads/products.xml"
    with open(fp) as f:
        soap_input = f.read()

    result = parse_seed_markets_soap(soap_input)
    for name, df in result.items():
        print("\n----", name, "----")
        print(df)

    # dfs = parse_seed_products_soap(soap_input)
    # for name, df in dfs.items():
    #     print(name, df.head())
