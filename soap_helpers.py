def wrap_in_soap(xml_body):
    """Wrap VDI XML in SOAP envelope according to VDI specification"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:VDIDataExchangeService">
    <soapenv:Header/>
    <soapenv:Body>
        {xml_body}
    </soapenv:Body>
</soapenv:Envelope>
"""

def wrap_with_soap_envelope(vdi_payload: str) -> str:
    """
    Wraps the VDI XML payload inside a SOAP 1.1 Envelope.
    Input:  vdi_payload (string) → <VDIDataExchange>...</VDIDataExchange>
    Output: Full SOAP envelope as string
    """
    soap_template = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:urn="urn:VDIDataExchangeService">
    <soapenv:Header/>
    <soapenv:Body>
        {vdi_payload}
    </soapenv:Body>
</soapenv:Envelope>"""

    return soap_template

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