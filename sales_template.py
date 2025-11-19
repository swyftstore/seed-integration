"""VDI template and helper functions for building VDI XML (sales, kiosks, etc.)"""
from config import VDI_CONFIG, DEFAULT_OPERATOR_ID
import uuid
from datetime import datetime
from xml.sax.saxutils import escape


def _get_field(source, candidate_keys, field_name, required=True, default=None):
    """Fetch value from dict supporting multiple candidate keys."""
    if isinstance(source, dict):
        for key in candidate_keys:
            if key in source and source[key] not in (None, ""):
                return str(source[key])
    if required:
        raise ValueError(f"Missing required field '{field_name}'")
    return default


def _normalize_list(data, singular_key):
    """Normalize data that may be a dict with a singular key or already a list."""
    if data is None:
        return []
    if isinstance(data, dict) and singular_key in data:
        values = data[singular_key]
    else:
        values = data
    if values is None:
        return []
    if isinstance(values, list):
        return values
    return [values]


def build_vdi_dataexchange(vdi_type, vdi_xml_content, request_data=None):
    """
    Generic function to build VDIDataExchange XML for any VDI type
    
    Args:
        vdi_type: VDI type (e.g., "mms-sales", "mms-kiosks")
        vdi_xml_content: The escaped VDITransaction XML content to embed in VDIXML
        request_data: Optional dict with configuration overrides
    
    Returns:
        VDIDataExchange XML string
    """
    if request_data is None:
        request_data = {}
    
    # Get configuration from request or use defaults from config.py
    operator_id = request_data.get("operator_id", DEFAULT_OPERATOR_ID)
    provider_id = request_data.get("provider_id", VDI_CONFIG["provider_id"])
    application_id = request_data.get("application_id", VDI_CONFIG["application_id"])
    application_version = request_data.get("application_version", VDI_CONFIG["application_version"])
    vdi_xml_version = request_data.get("vdi_xml_version", VDI_CONFIG["vdi_xml_version"])
    encoding = request_data.get("encoding", VDI_CONFIG["encoding"])
    
    # Generate transaction ID and time if not provided
    transaction_id = request_data.get("transaction_id", str(uuid.uuid4()))
    transaction_time = request_data.get("transaction_time", 
                                        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    
    # Build VDIDataExchange XML
    vdi_dataexchange = f"""<VDIDataExchange xmlns="urn:VDIDataExchangeService" xmlns:ns2="http://schemas.microsoft.com/2003/10/Serialization/">
    <VDIXMLVersion>{vdi_xml_version}</VDIXMLVersion>
    <VDIXMLType>{vdi_type}</VDIXMLType>
    <ProviderID>{escape_xml_attr(provider_id)}</ProviderID>
    <ApplicationID>{escape_xml_attr(application_id)}</ApplicationID>
    <ApplicationVersion>{escape_xml_attr(application_version)}</ApplicationVersion>
    <TransactionID>{escape_xml_attr(transaction_id)}</TransactionID>
    <TransactionTime>{escape_xml_attr(transaction_time)}</TransactionTime>
    <OperatorID>{escape_xml_attr(operator_id)}</OperatorID>
    <CompressionType xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
    <CompressionParam xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
    <Encoding>{escape_xml_attr(encoding)}</Encoding>
    <VDIXML xmlns:ns3="urn:VDIDataExchangeService">{vdi_xml_content}</VDIXML>
    <UserData xmlns:ns3="urn:VDIDataExchangeService" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
</VDIDataExchange>"""
    
    return vdi_dataexchange


def build_vdi_dataexchange_from_json(request_data, vdi_type):
    """Build VDIDataExchange XML from JSON payload (sales-specific)"""
    # Get configuration from request or use defaults from config.py
    operator_id = request_data.get("operator_id", DEFAULT_OPERATOR_ID)
    provider_id = request_data.get("provider_id", VDI_CONFIG["provider_id"])
    application_id = request_data.get("application_id", VDI_CONFIG["application_id"])
    application_version = request_data.get("application_version", VDI_CONFIG["application_version"])
    
    # Generate transaction ID and time if not provided
    transaction_id = request_data.get("transaction_id", str(uuid.uuid4()))
    transaction_time = request_data.get("transaction_time", 
                                        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    
    # Build VDITransaction XML from sales data
    vdi_transaction_xml = build_vdi_transaction_xml(request_data, vdi_type, provider_id, 
                                                   application_id, application_version,
                                                   operator_id, transaction_id, transaction_time)
    
    # Escape the VDITransaction XML for embedding in VDIXML
    escaped_vdi_xml = escape_xml_for_cdata(vdi_transaction_xml)
    
    # Use the generic template function
    return build_vdi_dataexchange(vdi_type, escaped_vdi_xml, request_data)


def build_vdi_transaction_xml(request_data, vdi_type, provider_id, application_id, 
                              application_version, operator_id, transaction_id, transaction_time):
    """Build VDITransaction XML from JSON payload"""
    vdi_xml_version = request_data.get("vdi_xml_version", VDI_CONFIG["vdi_xml_version"])
    
    sales_list = []
    sales_sources = [
        (request_data.get("Sales"), "Sale"),
        (request_data.get("sales"), "Sale"),
    ]
    for data, singular_key in sales_sources:
        if data is None:
            continue
        sales_list = _normalize_list(data, singular_key)
        if sales_list:
            break

    if not sales_list:
        single_sale = request_data.get("sale") or request_data.get("Sale")
        if single_sale is not None:
            sales_list = [single_sale]

    if not sales_list:
        raise ValueError("At least one sale is required (Sales.Sale or sales)")
    
    sale_blocks = []
    for sale in sales_list:
        if not isinstance(sale, dict):
            raise ValueError("Each sale must be an object")
        
        market_id = escape_xml_attr(_get_field(sale, ["MarketID", "market_id"], "Sale.MarketID"))
        kiosk_id = escape_xml_attr(_get_field(sale, ["KioskID", "kiosk_id"], "Sale.KioskID"))
        consumer_id = sale.get("ConsumerID") or sale.get("consumer_id")
        sale_id = escape_xml_attr(_get_field(sale, ["SaleID", "sale_id"], "Sale.SaleID"))
        sale_time = escape_xml_attr(_get_field(sale, ["SaleTime", "sale_time"], "Sale.SaleTime"))
        
        summary = sale.get("Summary") or sale.get("summary")
        if not isinstance(summary, dict):
            raise ValueError("Summary data is required")
        
        summary_price = escape_xml_attr(format_decimal(_get_field(summary, ["Price", "price"], "Summary.Price")))
        summary_discount = escape_xml_attr(format_decimal(_get_field(summary, ["Discount", "discount"], "Summary.Discount")))
        summary_total = escape_xml_attr(format_decimal(_get_field(summary, ["Total", "total"], "Summary.Total")))
        
        fees_obj = summary.get("Fees") or summary.get("fees")
        fees_total = escape_xml_attr(format_decimal(_get_field(fees_obj, ["Total", "total"], "Summary.Fees.Total", required=False))) if fees_obj else None
        
        taxes_obj = summary.get("Taxes") or summary.get("taxes")
        taxes_total = escape_xml_attr(format_decimal(_get_field(taxes_obj, ["Total", "total"], "Summary.Taxes.Total", required=False))) if taxes_obj else None
        
        summary_lines = [f'<Summary Price="{summary_price}" Discount="{summary_discount}" Total="{summary_total}">']
        if fees_total is not None:
            summary_lines.append(f'        <Fees Total="{fees_total}"/>')
        if taxes_total is not None:
            summary_lines.append(f'        <Taxes Total="{taxes_total}"/>')
        summary_lines.append("      </Summary>")
        summary_xml = "\n".join(summary_lines)
        
        items_data = sale.get("Items") or sale.get("items")
        items = _normalize_list(items_data, "Item")
        if not items:
            raise ValueError("At least one item is required (Items.Item)")
        
        item_entries = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each item must be an object")
            
            item_product_id = escape_xml_attr(_get_field(item, ["ProductID", "product_id"], "Item.ProductID"))
            item_code = escape_xml_attr(_get_field(item, ["Code", "code"], "Item.Code"))
            item_quantity = escape_xml_attr(_get_field(item, ["Quantity", "quantity"], "Item.Quantity"))
            item_price = escape_xml_attr(format_decimal(_get_field(item, ["Price", "price"], "Item.Price")))
            item_cost = escape_xml_attr(format_decimal(_get_field(item, ["Cost", "cost"], "Item.Cost")))
            item_total = escape_xml_attr(format_decimal(_get_field(item, ["Total", "total"], "Item.Total")))
            
            item_fees_obj = item.get("Fees") or item.get("fees")
            item_fees_total = escape_xml_attr(format_decimal(_get_field(item_fees_obj, ["Total", "total"], "Item.Fees.Total", required=False))) if item_fees_obj else None
            
            item_taxes_data = item.get("Taxes") or item.get("taxes")
            item_taxes = _normalize_list(item_taxes_data, "Tax")
            taxes_total_val = None
            if isinstance(item_taxes_data, dict):
                taxes_total_val = _get_field(item_taxes_data, ["Total", "total"], "Item.Taxes.Total", required=False)
            
            taxes_lines = []
            if item_taxes:
                if taxes_total_val is None:
                    taxes_total_val = format_decimal(sum(float(_get_field(t, ['Total', 'total'], 'Item.Taxes.Tax.Total')) for t in item_taxes))
                else:
                    taxes_total_val = format_decimal(taxes_total_val)
                taxes_lines.append(f'          <Taxes Total="{escape_xml_attr(taxes_total_val)}">')
                for tax in item_taxes:
                    tax_name = escape_xml_attr(_get_field(tax, ["Name", "name"], "Item.Taxes.Tax.Name"))
                    tax_rate = escape_xml_attr(format_decimal(_get_field(tax, ["Rate", "rate"], "Item.Taxes.Tax.Rate")))
                    tax_value = escape_xml_attr(format_decimal(_get_field(tax, ["Value", "value"], "Item.Taxes.Tax.Value")))
                    tax_count = escape_xml_attr(_get_field(tax, ["Count", "count"], "Item.Taxes.Tax.Count"))
                    tax_total = escape_xml_attr(format_decimal(_get_field(tax, ["Total", "total"], "Item.Taxes.Tax.Total")))
                    taxes_lines.append(f'            <Tax Name="{tax_name}" Rate="{tax_rate}" Value="{tax_value}" Count="{tax_count}" Total="{tax_total}"/>')
                taxes_lines.append("          </Taxes>")
            elif taxes_total_val is not None:
                taxes_lines.append(f'          <Taxes Total="{escape_xml_attr(format_decimal(taxes_total_val))}"/>')
            
            fees_line = f'\n          <Fees Total="{item_fees_total}"/>' if item_fees_total is not None else ""
            taxes_block = f'\n' + "\n".join(taxes_lines) if taxes_lines else ""
            item_entry = f"""
        <Item ProductID="{item_product_id}" Code="{item_code}" Quantity="{item_quantity}" Price="{item_price}" Cost="{item_cost}" Total="{item_total}">{fees_line}{taxes_block}
        </Item>"""
            item_entries.append(item_entry)
        
        items_xml = "".join(item_entries)
        
        tenders_data = sale.get("Tenders") or sale.get("tenders")
        tenders = _normalize_list(tenders_data, "Tender")
        if not tenders:
            raise ValueError("At least one tender is required (Tenders.Tender)")
        
        tenders_lines = []
        for tender in tenders:
            if not isinstance(tender, dict):
                raise ValueError("Each tender must be an object")
            tender_type = escape_xml_attr(_get_field(tender, ["Type", "type"], "Tender.Type"))
            tender_amount = escape_xml_attr(format_decimal(_get_field(tender, ["Amount", "amount"], "Tender.Amount")))
            tenders_lines.append(f'        <Tender Type="{tender_type}" Amount="{tender_amount}"/>')
        tenders_xml = "\n".join(tenders_lines)
        
        sale_attrs = [f'MarketID="{market_id}"', f'KioskID="{kiosk_id}"', f'SaleID="{sale_id}"', f'SaleTime="{sale_time}"']
        if consumer_id:
            sale_attrs.insert(2, f'ConsumerID="{escape_xml_attr(consumer_id)}"')
        sale_attrs_str = " ".join(sale_attrs)
        
        sale_block = f"""    <Sale {sale_attrs_str}>
      {summary_xml}

      <Items>{items_xml}
      </Items>

      <Tenders>
{tenders_xml}
      </Tenders>

    </Sale>"""
        sale_blocks.append(sale_block)
    
    sales_xml = "\n".join(sale_blocks)
    
    vdi_transaction = f"""<?xml version="1.0" encoding="utf-8"?>
<VDITransaction xmlns:xsd="http://www.w3.org/2001/XMLSchema" VDIXMLVersion="{vdi_xml_version}" VDIXMLType="{vdi_type}" ProviderID="{escape_xml_attr(provider_id)}" ApplicationID="{escape_xml_attr(application_id)}" ApplicationVersion="{escape_xml_attr(application_version)}" TransactionID="{escape_xml_attr(transaction_id)}" TransactionTime="{escape_xml_attr(transaction_time)}" OperatorID="{escape_xml_attr(operator_id)}">
    <Sales>
{sales_xml}
  </Sales>
</VDITransaction>"""
    
    return vdi_transaction


def format_decimal(value):
    """Format numeric value to 2 decimal places for currency fields"""
    if value is None:
        return "0.00"
    try:
        num = float(value)
        return f"{num:.2f}"
    except (ValueError, TypeError):
        return str(value)

def escape_xml_attr(value):
    """Escape XML attribute value"""
    if value is None:
        return ""
    return escape(str(value), {'"': '&quot;', "'": '&apos;'})


def escape_xml_for_cdata(xml_content):
    """Escape XML content for embedding in VDIXML element"""
    # Escape XML special characters
    escaped = xml_content.replace("&", "&amp;")
    escaped = escaped.replace("<", "&lt;")
    escaped = escaped.replace(">", "&gt;")
    escaped = escaped.replace('"', "&quot;")
    escaped = escaped.replace("'", "&apos;")
    return escaped

