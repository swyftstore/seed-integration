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
    "provider_id": "swyft",  # Provider ID for outbound messages
    "application_id": "swyft-vdi-integration",
    "application_version": "1.0",
    "vdi_xml_version": "1",
    "encoding": "utf-8"
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

# ActiveMQ Configuration - STOMP 1.0
# Note: For client connections, use "localhost" or "127.0.0.1" (not "0.0.0.0" which is for server binding)
# Protocol: STOMP 1.0
ACTIVEMQ_CONFIG = {
    "host": os.getenv("ACTIVEMQ_HOST", "localhost"),
    "stomp_port": int(os.getenv("ACTIVEMQ_PORT", "61613")),  # STOMP port (default: 61613 - standard STOMP port)
    "username": os.getenv("ACTIVEMQ_USERNAME", ""),
    "password": os.getenv("ACTIVEMQ_PASSWORD", ""),
    "topic": os.getenv("ACTIVEMQ_TOPIC", "com.zoomsystems.common.PythonConsumerTopic")
}