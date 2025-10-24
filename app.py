from flask import Flask, request, jsonify
from seed_client import send_vdi_message
from config import VDI_TYPES, DEFAULT_OPERATOR_ID, VDI_CONFIG
from vdi_configs import (
    get_market_config, get_product_config, list_available_configs
)
import xml.etree.ElementTree as ET
import re

app = Flask(__name__)


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
        
        # Send VDI message
        status, response = send_vdi_message(
            vdi_type=VDI_TYPES[vdi_type],
            vdi_content=xml_payload,
            operator_id=operator_id
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
        return jsonify({"error": f"Payload file not found: {payload_file}"}), 404
    except Exception as e:
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
    elif vdi_type == "products":
        config = get_product_config(config_name)
        return {
            "MARKET_ID": request_data.get("market_id", config["market_id"]),
            "CATALOG_SIZE": request_data.get("catalog_size", config["catalog_size"]),
            "PRODUCT_ID": request_data.get("product_id", config["product_id"]),
            "PRODUCT_NAME": request_data.get("product_name", config["product_name"]),
            "PRICE": request_data.get("price", config["price"]),
            "COST": request_data.get("cost", config["cost"]),
            "PRODUCT_CODE": request_data.get("product_code", config["product_code"]),
            "CATEGORY": request_data.get("category", config["category"]),
            "BARCODE": request_data.get("barcode", config["barcode"]),
            "TAX_ID": request_data.get("tax_id", config["tax_id"]),
            "TAX_NAME": request_data.get("tax_name", config["tax_name"]),
            "TAX_RATE": request_data.get("tax_rate", config["tax_rate"]),
            "TAX_INCLUDED": request_data.get("tax_included", config["tax_included"]),
            "FEE_ID": request_data.get("fee_id", config["fee_id"]),
            "FEE_NAME": request_data.get("fee_name", config["fee_name"]),
            "FEE_VALUE": request_data.get("fee_value", config["fee_value"]),
            "FEE_TAXABLE": request_data.get("fee_taxable", config["fee_taxable"])
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
        elif vdi_type == "products":
            from vdi_configs import PRODUCT_CONFIGS
            return jsonify({"status": "success", "configs": PRODUCT_CONFIGS})
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

@app.route("/debug/soap/products", methods=["POST"])
def debug_soap_products():
    """Return the exact SOAP XML that would be sent for products"""
    try:
        request_data = request.get_json(silent=True) or {}
        operator_id = request_data.get("operator_id", DEFAULT_OPERATOR_ID)
        payload_file = request_data.get("payload_file", "payloads/products.xml")

        with open(payload_file, "r") as file:
            xml_payload = file.read()

        config_data = get_config_for_vdi_type("products", request_data)
        xml_payload = apply_config_to_payload(xml_payload, config_data)

        from soap_helpers import create_vdi_transaction, wrap_in_soap
        import uuid
        from datetime import datetime

        transaction_id = str(uuid.uuid4())
        transaction_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        vdi_transaction = create_vdi_transaction(
            vdi_type=VDI_TYPES["products"],
            provider_id=VDI_CONFIG["provider_id"],
            application_id=VDI_CONFIG["application_id"],
            application_version=VDI_CONFIG["application_version"],
            operator_id=operator_id,
            transaction_id=transaction_id,
            transaction_time=transaction_time,
            vdi_content=xml_payload
        )

        soap_xml = wrap_in_soap(vdi_transaction)
        return jsonify({
            "soap": soap_xml,
            "headers": {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/receive/sales", methods=["POST"])
def receive_sales():
    """Receive mms-sales messages from Provider to Seed"""
    try:
        # Parse incoming VDI message
        xml_data = request.get_data(as_text=True)
        root = ET.fromstring(xml_data)

        # Namespace/SOAP agnostic search for VDITransaction
        def find_by_localname(node, local):
            for el in node.iter():
                if el.tag.split('}')[-1] == local:
                    return el
            return None
        vdi_transaction = find_by_localname(root, 'VDITransaction')
        if vdi_transaction is None:
            return jsonify({"error": "Invalid VDI message format"}), 400
        
        # Process sales data
        sales_data = process_sales_message(vdi_transaction)
        
        return jsonify({
            "status": "success",
            "message": "Sales data received and processed",
            "data": sales_data
        })
        
    except ET.ParseError:
        return jsonify({"error": "Invalid XML format"}), 400
    except Exception as e:
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