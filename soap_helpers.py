def wrap_in_soap(xml_body):
    """Wrap VDI XML in SOAP envelope according to VDI specification"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        {xml_body}
    </soap:Body>
</soap:Envelope>
"""

def create_vdi_transaction(vdi_type, provider_id, application_id, application_version, 
                         operator_id, transaction_id, transaction_time, vdi_content):
    """Create a properly formatted VDI transaction according to specification"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<VDITransaction xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                VDIXMLVersion="1"
                VDIXMLType="{vdi_type}"
                ProviderID="{provider_id}"
                ApplicationID="{application_id}"
                ApplicationVersion="{application_version}"
                OperatorID="{operator_id}"
                TransactionID="{transaction_id}"
                TransactionTime="{transaction_time}">
{vdi_content}
</VDITransaction>"""