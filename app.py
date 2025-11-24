import logging
from flask import Flask, request, jsonify
from seed_client import send_vdi_message, send_vdi_dataexchange
from config import VDI_TYPES, DEFAULT_OPERATOR_ID, SEED_ENDPOINTS
from vdi_configs import (
    get_market_config, list_available_configs
)
from sales_template import build_vdi_dataexchange_from_json
import xml.etree.ElementTree as ET
import re

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


@app.route("/send/markets", methods=["POST"])
def send_markets():
    """Send markets VDI message to SEED with market-specific validation"""
    # Add market-specific validation
    request_data = request.get_json(silent=True) or {}
    
    # Validate required market fields
    if not request_data.get("market_id") and not request_data.get("config_name"):
        return jsonify({
            "error": "Market validation failed", 
            "message": "Either 'market_id' or 'config_name' must be provided",
            "required_fields": ["market_id", "market_name", "client_id", "client_name"]
        }), 400
    
    return handle_vdi_send("markets", request)

def handle_vdi_send(vdi_type, request):
    """Common handler for VDI send operations"""
    try:
        # Validate VDI type
        if vdi_type not in VDI_TYPES:
            return jsonify({"error": f"Invalid VDI type: {vdi_type}"}), 400
        
        # Get configuration from request or use defaults
        request_data = request.get_json(silent=True) or {}
        
        # Get operator_id from request or use default
        operator_id = request_data.get("operator_id", DEFAULT_OPERATOR_ID)
        
        # Check if custom payload file is specified
        payload_file = request_data.get("payload_file", f"payloads/{vdi_type}.xml")
        
        # Load payload file
        with open(payload_file, "r") as file:
            xml_payload = file.read()
        
        # Apply dynamic configuration based on VDI type
        config_data = get_config_for_vdi_type(vdi_type, request_data)
        xml_payload = apply_config_to_payload(xml_payload, config_data)
        
        app.logger.info(
            "Sending VDI message",
            extra={
                "vdi_type": vdi_type,
                "operator_id": operator_id,
                "payload_file": payload_file
            }
        )
        # Send VDI message
        status, response = send_vdi_message(
            vdi_type=VDI_TYPES[vdi_type],
            vdi_content=xml_payload,
            operator_id=operator_id
        )
        app.logger.info(
            "VDI message sent",
            extra={
                "vdi_type": vdi_type,
                "operator_id": operator_id,
                "status": status
            }
        )
        
        return jsonify({
            "status": status, 
            "response": response,
            "vdi_type": VDI_TYPES[vdi_type],
            "operator_id": operator_id,
            "payload_file": payload_file,
            "config_applied": config_data
        })
        
    except FileNotFoundError:
        app.logger.exception("Payload file not found", extra={"payload_file": payload_file})
        return jsonify({"error": f"Payload file not found: {payload_file}"}), 404
    except ValueError as ve:
        app.logger.warning("Validation error while sending VDI", extra={"error": str(ve)})
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.exception("Unexpected error while sending VDI", extra={"vdi_type": vdi_type})
        return jsonify({"error": str(e)}), 500

def get_config_for_vdi_type(vdi_type, request_data):
    """Get configuration data for specific VDI type"""
    # Get config template name from request or use default
    config_name = request_data.get("config_name", "default")
    
    if vdi_type == "markets":
        config = get_market_config(config_name)
        return {
            "MARKET_ID": request_data.get("market_id", config["market_id"]),
            "OPERATOR_ID": request_data.get("operator_id", config["operator_id"]),
            "CLIENT_ID": request_data.get("client_id", config["client_id"]),
            "CLIENT_NAME": request_data.get("client_name", config["client_name"]),
            "MARKET_NAME": request_data.get("market_name", config["market_name"]),
            "MARKET_ADDRESS": request_data.get("market_address", config["market_address"]),
            "MARKET_LOCATION": request_data.get("market_location", config["market_location"])
        }
    else:
        return {}

def apply_config_to_payload(xml_payload, config_data):
    """Apply configuration data to XML payload using template substitution"""
    pattern = re.compile(r"\{\{(\w+)\}\}")

    def replace_placeholder(match):
        key = match.group(1)
        if key in config_data:
            return str(config_data[key])
        raise KeyError(f"Missing config value for {key}")

    return pattern.sub(replace_placeholder, xml_payload)

@app.route("/configs", methods=["GET"])
def list_configs():
    """List all available configuration templates"""
    return jsonify({
        "status": "success",
        "available_configs": list_available_configs(),
        "message": "Use 'config_name' parameter in POST requests to select specific templates"
    })

@app.route("/configs/<vdi_type>", methods=["GET"])
def get_config_details(vdi_type):
    """Get details of specific VDI type configurations"""
    try:
        if vdi_type == "markets":
            from vdi_configs import MARKET_CONFIGS
            return jsonify({"status": "success", "configs": MARKET_CONFIGS})
        elif vdi_type == "sales":
            from vdi_configs import SALES_CONFIGS
            return jsonify({"status": "success", "configs": SALES_CONFIGS})
        elif vdi_type == "kiosks":
            from vdi_configs import KIOSKS_CONFIGS
            return jsonify({"status": "success", "configs": KIOSKS_CONFIGS})
        elif vdi_type == "collections":
            from vdi_configs import COLLECTIONS_CONFIGS
            return jsonify({"status": "success", "configs": COLLECTIONS_CONFIGS})
        else:
            return jsonify({"error": f"Invalid VDI type: {vdi_type}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/send/sales", methods=["POST"])
def send_sales():
    """Send sales VDI message to SEED test environment endpoint (SOAP)"""
    try:
        request_data = request.get_json(silent=True)
        if not request_data:
            return jsonify({"error": "JSON payload is required"}), 400

        sales_payload = request_data.get("Sales") or request_data.get("sales") or request_data.get("sale")
        if isinstance(sales_payload, dict) and "Sale" in sales_payload:
            sale_count = len(sales_payload["Sale"]) if isinstance(sales_payload["Sale"], list) else 1
        elif isinstance(sales_payload, list):
            sale_count = len(sales_payload)
        elif isinstance(sales_payload, dict):
            sale_count = 1e4
        else:
            sale_count = 0

        app.logger.info(
            "Received sales send request",
            extra={"sale_count": sale_count}
        )

        environment = "test"

        vdi_dataexchange_xml = build_vdi_dataexchange_from_json(request_data, "mms-sales")

        status, response = send_vdi_dataexchange(vdi_dataexchange_xml, environment)

        app.logger.info(
            "Sales message sent",
            extra={"sale_count": sale_count, "status": status}
        )

        return jsonify({
            "status": status,
            "response": response,
            "environment": environment,
            "endpoint": SEED_ENDPOINTS[environment]
        })

    except ValueError as ve:
        app.logger.warning("Invalid sales payload", extra={"error": str(ve)})
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.exception("Sales send failed")
        return jsonify({"error": str(e)}), 500


@app.route("/receive/kiosks", methods=["POST"])
def receive_kiosks():
    """Receive mms-kiosks messages from Provider to Seed"""
    try:
        xml_data = request.get_data(as_text=True)
        root = ET.fromstring(xml_data)

        def find_by_localname(node, local):
            for el in node.iter():
                if el.tag.split('}')[-1] == local:
                    return el
            return None
        vdi_transaction = find_by_localname(root, 'VDITransaction')
        if vdi_transaction is None:
            return jsonify({"error": "Invalid VDI message format"}), 400
        
        kiosks_data = process_kiosks_message(vdi_transaction)
        
        return jsonify({
            "status": "success",
            "message": "Kiosks data received and processed",
            "data": kiosks_data
        })
        
    except ET.ParseError:
        return jsonify({"error": "Invalid XML format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/receive/collections", methods=["POST"])
def receive_collections():
    """Receive mms-collections messages from Provider to Seed"""
    try:
        xml_data = request.get_data(as_text=True)
        root = ET.fromstring(xml_data)

        def find_by_localname(node, local):
            for el in node.iter():
                if el.tag.split('}')[-1] == local:
                    return el
            return None
        vdi_transaction = find_by_localname(root, 'VDITransaction')
        if vdi_transaction is None:
            return jsonify({"error": "Invalid VDI message format"}), 400
        
        collections_data = process_collections_message(vdi_transaction)
        
        return jsonify({
            "status": "success",
            "message": "Collections data received and processed",
            "data": collections_data
        })
        
    except ET.ParseError:
        return jsonify({"error": "Invalid XML format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_sales_message(vdi_transaction):
    """Process incoming sales VDI message"""
    sales_data = []
    
    # Extract sales information
    sales_collection = vdi_transaction.find('.//Sales')
    if sales_collection is not None:
        for sale in sales_collection.findall('Sale'):
            sale_data = {
                "market_id": sale.get('MarketID'),
                "kiosk_id": sale.get('KioskID'),
                "sale_id": sale.get('SaleID'),
                "sale_time": sale.get('SaleTime'),
                "consumer_id": sale.get('ConsumerID')
            }
            
            # Extract summary
            summary = sale.find('Summary')
            if summary is not None:
                sale_data["summary"] = {
                    "price": summary.get('Price'),
                    "discount": summary.get('Discount'),
                    "total": summary.get('Total')
                }
            
            sales_data.append(sale_data)
    
    return sales_data

def process_kiosks_message(vdi_transaction):
    """Process incoming kiosks VDI message"""
    kiosks_data = []
    
    kiosks_collection = vdi_transaction.find('.//KiosksCollection')
    if kiosks_collection is not None:
        for kiosk in kiosks_collection.findall('Kiosk'):
            kiosk_data = {
                "market_id": kiosk.get('MarketID'),
                "kiosk_id": kiosk.get('KioskID'),
                "kiosk_sn": kiosk.get('KioskSN'),
                "last_sync": kiosk.get('LastSync'),
                "last_transaction": kiosk.get('LastTransaction'),
                "catalog_version": kiosk.get('CatalogVersion')
            }
            kiosks_data.append(kiosk_data)
    
    return kiosks_data

def process_collections_message(vdi_transaction):
    """Process incoming collections VDI message"""
    collections_data = []
    
    collections_collection = vdi_transaction.find('.//CashCollections')
    if collections_collection is not None:
        for collection in collections_collection.findall('CashCollection'):
            collection_data = {
                "market_id": collection.get('MarketID'),
                "kiosk_id": collection.get('KioskID'),
                "collection_time": collection.get('CollectionTime'),
                "amount": collection.get('Amount'),
                "collected_by": collection.get('CollectedBy')
            }
            collections_data.append(collection_data)
    
    return collections_data

if __name__ == "__main__":
    app.run(debug=True)