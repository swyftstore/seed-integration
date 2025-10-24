# VDI Configuration Management
# This file contains all configuration settings for different VDI message types

# Global VDI Settings
VDI_GLOBAL_CONFIG = {
    "provider_id": "CANTALOUPE",  # Provider ID for outbound messages (from Seed)
    "application_id": "SyncVdiMicromarkets.Uploader",
    "application_version": "232.0.4572.0",
    "vdi_xml_version": "1",
    "encoding": "UTF-8"
}

# Default Operator Settings
DEFAULT_OPERATOR = {
    "operator_id": "nm_swyft",
    "username": "micromarket.swyft@cantaloupe.com",
    "password": "032p0rK71Q00"
}

# Market Configuration Templates
MARKET_CONFIGS = {
    "default": {
        "market_id": "1",
        "operator_id": "nm_swyft",
        "client_id": "3436",
        "client_name": "Bob and Associates",
        "market_name": "Bobs Mufflers - Main Lunchroom",
        "market_address": "550 Granite Court, Atlanta, GA, 30033",
        "market_location": "Bobs Mufflers"
    },
    "acme_painting": {
        "market_id": "5",
        "operator_id": "nm_swyft",
        "client_id": "3441",
        "client_name": "ACME INC",
        "market_name": "Acme Painting – First Floor Breakroom",
        "market_address": "123 ABC Street, Atlanta, GA, 30033",
        "market_location": "Acme Painting"
    },
    "woodys_barrels": {
        "market_id": "2",
        "operator_id": "nm_swyft",
        "client_id": "3441",
        "client_name": "ACME INC",
        "market_name": "Woody's Premium Barrels - Lunchroom Ground Floor",
        "market_address": "321 ABC Street, Atlanta, GA, 30033",
        "market_location": "Woody's Premium Barrels"
    }
}

# Product Configuration Templates
PRODUCT_CONFIGS = {
    "default": {
        "market_id": "1",
        "catalog_size": "Full",
        "product_id": "602004053138",
        "product_name": "Hello Flawless Oxygen Wow Honey",
        "price": "1.00",
        "cost": "0.00",
        "product_code": "602004053138",
        "category": "PHYSICAL",
        "barcode": "602004053138",
        "tax_id": "9120",
        "tax_name": "Client MOR Tax",
        "tax_rate": "0.00",
        "tax_included": "0",
        "fee_id": "0",
        "fee_name": "No Fee",
        "fee_value": "0",
        "fee_taxable": "false"
    },
    "beverage": {
        "market_id": "1",
        "catalog_size": "Full",
        "product_id": "819",
        "product_name": "DIET MTN Dew Bottle",
        "price": "2.5",
        "cost": "2.35",
        "product_code": "17",
        "category": "Generic",
        "barcode": "012000001345",
        "tax_id": "1120",
        "tax_name": "11.20 % tax",
        "tax_rate": "0.11200",
        "tax_included": "0",
        "fee_id": "10000",
        "fee_name": "$1 bottle deposit",
        "fee_value": "1",
        "fee_taxable": "true"
    },
    "water": {
        "market_id": "1",
        "catalog_size": "Full",
        "product_id": "820",
        "product_name": "AQUAFINA WTR",
        "price": "2.5",
        "cost": "2.40",
        "product_code": "19",
        "category": "Generic",
        "barcode": "012000001598",
        "tax_id": "1120",
        "tax_name": "11.20 % tax",
        "tax_rate": "0.11200",
        "tax_included": "0",
        "fee_id": "10000",
        "fee_name": "$1 bottle deposit",
        "fee_value": "1",
        "fee_taxable": "true"
    }
}

# Sales Configuration (for inbound messages)
SALES_CONFIGS = {
    "default": {
        "operator_id": "nm_swyft",
        "provider_id": "swift",
        "market_id": "1",
        "kiosk_id": "1-K"
    }
}

# Kiosks Configuration (for inbound messages)
KIOSKS_CONFIGS = {
    "default": {
        "operator_id": "nm_swyft",
        "provider_id": "swift",
        "market_id": "1",
        "kiosk_id": "1-K",
        "kiosk_sn": "VSH312309"
    }
}

# Collections Configuration (for inbound messages)
COLLECTIONS_CONFIGS = {
    "default": {
        "operator_id": "nm_swyft",
        "provider_id": "swift",
        "market_id": "1",
        "kiosk_id": "1-K"
    }
}

# Configuration Helper Functions
def get_market_config(config_name="default"):
    """Get market configuration by name"""
    return MARKET_CONFIGS.get(config_name, MARKET_CONFIGS["default"])

def get_product_config(config_name="default"):
    """Get product configuration by name"""
    return PRODUCT_CONFIGS.get(config_name, PRODUCT_CONFIGS["default"])

def get_sales_config(config_name="default"):
    """Get sales configuration by name"""
    return SALES_CONFIGS.get(config_name, SALES_CONFIGS["default"])

def get_kiosks_config(config_name="default"):
    """Get kiosks configuration by name"""
    return KIOSKS_CONFIGS.get(config_name, KIOSKS_CONFIGS["default"])

def get_collections_config(config_name="default"):
    """Get collections configuration by name"""
    return COLLECTIONS_CONFIGS.get(config_name, COLLECTIONS_CONFIGS["default"])

def list_available_configs():
    """List all available configuration names"""
    return {
        "markets": list(MARKET_CONFIGS.keys()),
        "products": list(PRODUCT_CONFIGS.keys()),
        "sales": list(SALES_CONFIGS.keys()),
        "kiosks": list(KIOSKS_CONFIGS.keys()),
        "collections": list(COLLECTIONS_CONFIGS.keys())
    }
