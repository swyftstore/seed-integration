import os

SEED_ENDPOINTS = {
    "test": "https://qacore.mycantaloupe.com/VdiMicromarket.NewMarkets/SecureService.svc",
    "prod": "https://mkt.mycantaloupe.com/VdiMicromarket/SecureService.svc"
}

AUTH = {
    "username": os.getenv("SEED_USERNAME", "micromarket.swyft@cantaloupe.com"),
    "password": os.getenv("SEED_PASSWORD", "032p0rK71Q00")
}

# VDI Configuration
VDI_CONFIG = {
    "provider_id": "SWIFT",  # Provider ID for outbound messages (from Seed)
    "application_id": "SyncVdiMicromarkets.Uploader",
    "application_version": "232.0.4572.0",  # Updated to match SEED version
    "vdi_xml_version": "1",
    "encoding": "UTF-8"
}

# Default Operator ID
DEFAULT_OPERATOR_ID = "nm_swyft"

# Supported VDI Types
VDI_TYPES = {
    "markets": "mms-markets",
    "products": "mms-products", 
    "sales": "mms-sales",
    "kiosks": "mms-kiosks",
    "collections": "mms-collections"
}