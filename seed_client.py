import requests
import time
import uuid
from datetime import datetime
from config import SEED_ENDPOINTS, AUTH, VDI_CONFIG
from soap_helpers import wrap_in_soap, create_vdi_transaction
from requests.auth import HTTPBasicAuth

HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": ""
}

def send_soap_request(xml_data, environment="test", max_retries=3, backoff_base=0.5):
    """Send SOAP request to SEED endpoint with basic retry on transient failures."""
    url = SEED_ENDPOINTS[environment]
    wrapped = wrap_in_soap(xml_data)

    attempt = 0
    while True:
        try:
            response = requests.post(
                url,
                headers=HEADERS,
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