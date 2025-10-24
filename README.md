# Smart Seed Integration - Micromarket VDI Implementation

This project implements the **Micromarket VDI For Seed - Partner Instructions V2.3** specification for integrating with Cantaloupe's SEED platform.

## Overview

The implementation supports bidirectional VDI communication:
- **Outbound**: Seed → Provider (Markets, Products)
- **Inbound**: Provider → Seed (Sales, Kiosks, Collections)

## VDI Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `mms-markets` | Seed → Provider | Market master data |
| `mms-products` | Seed → Provider | Product catalog data |
| `mms-sales` | Provider → Seed | Sales transactions |
| `mms-kiosks` | Provider → Seed | Kiosk information |
| `mms-collections` | Provider → Seed | Cash collection data |

## Project Structure

```
smart_seed_integration/
├── app.py                 # Flask web application with VDI endpoints
├── config.py              # Configuration and VDI settings
├── seed_client.py         # SEED API client with VDI support
├── soap_helpers.py        # SOAP and VDI transaction helpers
├── vdi_validator.py       # VDI message validation
├── requirements.txt       # Python dependencies
└── payloads/              # Sample VDI payloads
    ├── market.xml         # Sample markets payload
    └── products.xml       # Sample products payload
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configuration is already set up with SEED credentials:
```python
AUTH = {
    "username": "micromarket.swyft@cantaloupe.com",
    "password": "032p0rK71Q00"
}
DEFAULT_OPERATOR_ID = "nm_swyft"
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### Outbound Messages (Seed → Provider)

**Send Markets:**
```bash
curl -X POST http://localhost:5000/send/markets \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "nm_swyft"}'
```

**Send Products:**
```bash
curl -X POST http://localhost:5000/send/products \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "nm_swyft"}'
```

#### Inbound Messages (Provider → Seed)

**Receive Sales:**
```bash
curl -X POST http://localhost:5000/receive/sales \
  -H "Content-Type: text/xml" \
  --data-binary @sample_sales.xml
```

**Receive Kiosks:**
```bash
curl -X POST http://localhost:5000/receive/kiosks \
  -H "Content-Type: text/xml" \
  --data-binary @sample_kiosks.xml
```

**Receive Collections:**
```bash
curl -X POST http://localhost:5000/receive/collections \
  -H "Content-Type: text/xml" \
  --data-binary @sample_collections.xml
```

## VDI Specification Compliance

### Required Attributes

All VDI transactions must include:
- `VDIXMLVersion="1"`
- `VDIXMLType` (mms-markets, mms-products, mms-sales, mms-kiosks, mms-collections)
- `ProviderID` (CANTALOUPE for outbound, provider ID for inbound)
- `ApplicationID`
- `ApplicationVersion`
- `OperatorID`
- `TransactionID` (UUID format)
- `TransactionTime` (ISO 8601 format)

### Message Flow

1. **New Market Creation:**
   - Seed sends `mms-markets` message (without Kiosks initially)
   - Provider associates Market with SEED Market ID
   - Provider sends `mms-kiosks` message back to Seed
   - Seed includes Kiosks in subsequent `mms-markets` messages

2. **Product Catalog Updates:**
   - Seed sends `mms-products` messages with full catalog
   - Supports both scheduled intervals and automatic updates

3. **Sales Processing:**
   - Provider sends `mms-sales` messages as transactions occur
   - Includes basket details, payment methods, taxes, and fees

## Validation

The implementation includes comprehensive validation:
- VDI transaction structure validation
- Required field validation
- Data type validation (UUID, datetime, decimal)
- Field length validation

## Error Handling

- HTTP 200: Success
- HTTP 400: Validation errors
- HTTP 404: File not found
- HTTP 500: Server errors

All responses include standardized error messages with details.

## Testing

Sample payload files are provided in the `payloads/` directory:
- `market.xml`: Sample markets data
- `products.xml`: Sample products data

## Security

- Uses HTTPS with TLS 1.2+
- Basic authentication for SEED endpoints
- Input validation and sanitization
- Error handling without information disclosure

## Configuration

Key configuration options in `config.py`:

```python
SEED_ENDPOINTS = {
    "test": "https://qacore.mycantaloupe.com/VdiMicromarket.NewMarkets/SecureService.svc",
    "prod": "https://mkt.mycantaloupe.com/VdiMicromarket/SecureService.svc"
}

VDI_CONFIG = {
    "provider_id": "swift",
    "application_id": "SyncVdiMicromarkets.Uploader",
    "application_version": "1.0.0",
    "vdi_xml_version": "1",
    "encoding": "UTF-8"
}
DEFAULT_OPERATOR_ID = "nm_swyft"
```

## Support

This implementation follows the Micromarket VDI For Seed - Partner Instructions V2.3 specification. For questions about the VDI standard, refer to the official Cantaloupe documentation.
