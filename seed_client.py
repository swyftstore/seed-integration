import requests
import time
import uuid
from datetime import datetime
from config import SEED_ENDPOINTS, AUTH, VDI_CONFIG
from soap_helpers import wrap_in_soap, create_vdi_transaction
from requests.auth import HTTPBasicAuth

SOAP_ACTION = "urn:VDIDataExchangeService/IVDIDataExchangeService/VDIDataExchange"

def get_soap_headers(soap_action=None):
    """
    Get SOAP headers for the request.
    Defaults to the standard SOAPAction for VDI service.
    """
    headers = {
        "Content-Type": "text/xml; charset=utf-8"
    }
    
    if soap_action is None:
        # Default to the standard VDI SOAPAction
        headers["SOAPAction"] = f'"{SOAP_ACTION}"'
    elif soap_action == "":
        headers["SOAPAction"] = '""'
    else:
        headers["SOAPAction"] = f'"{soap_action}"'
    
    return headers

def send_soap_request(xml_data, environment="test", max_retries=3, backoff_base=0.5, soap_action=None):
    """
    Send SOAP request to SEED endpoint with basic retry on transient failures.
    
    Args:
        xml_data: The XML body to send (VDIDataExchange XML)
        environment: Environment name (test/prod)
        max_retries: Maximum retry attempts
        backoff_base: Base backoff time in seconds
        soap_action: SOAPAction value. None uses default VDI action, "" uses empty string
    """
    url = SEED_ENDPOINTS[environment]
    wrapped = wrap_in_soap(xml_data)
    headers = get_soap_headers(soap_action)

    attempt = 0
    while True:
        try:
            response = requests.post(
                url,
                headers=headers,
                data=wrapped,
                auth=HTTPBasicAuth(AUTH["username"], AUTH["password"]),
                timeout=30
            )
            # Retry on 5xx
            if response.status_code >= 500 and attempt < max_retries:
                attempt += 1
                sleep_s = backoff_base * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue
            return response.status_code, response.text
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt >= max_retries:
                raise
            attempt += 1
            sleep_s = backoff_base * (2 ** (attempt - 1))
            time.sleep(sleep_s)

def send_vdi_message(vdi_type, vdi_content, operator_id, environment="test"):
    """Send VDI message to SEED endpoint with proper VDI transaction structure"""
    transaction_id = str(uuid.uuid4())
    transaction_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    vdi_transaction = create_vdi_transaction(
        vdi_type=vdi_type,
        provider_id=VDI_CONFIG["provider_id"],
        application_id=VDI_CONFIG["application_id"],
        application_version=VDI_CONFIG["application_version"],
        operator_id=operator_id,
        transaction_id=transaction_id,
        transaction_time=transaction_time,
        vdi_content=vdi_content
    )
    
    return send_soap_request(vdi_transaction, environment)

def send_vdi_dataexchange(vdi_xml, environment="test", soap_action=None):
    """
    Send VDIDataExchange XML directly to SEED endpoint (wrapped in SOAP)
    
    Args:
        vdi_xml: VDIDataExchange XML string
        environment: Environment name (test/prod)
        soap_action: SOAPAction value. None uses default VDI action, "" uses empty string
    """
    return send_soap_request(vdi_xml, environment=environment, soap_action=soap_action)