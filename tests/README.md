# Tests Directory

This directory contains all test files for the Voltaro OCPP backend.

## Test Files

### Core Testing
- **`mock_client.py`** - OCPP 1.6 mock charge point client for end-to-end testing
  - Tests all implemented OCPP messages: BootNotification, Heartbeat, Authorize, StartTransaction, MeterValues, StopTransaction, StatusNotification
  - Includes various scenarios (valid/invalid tags, different transaction states, connector status transitions)

### Database Verification Scripts
- **`test_db_connection.py`** - Basic database connectivity test
- **`test_models.py`** - SQLAlchemy model validation test

### OCPP Message Testing
- **`test_boot_notification_db.py`** - Verify BootNotification data storage
- **`test_heartbeat_db.py`** - Verify Heartbeat timestamp updates
- **`test_start_transaction_db.py`** - Verify StartTransaction session creation
- **`test_meter_values_db.py`** - Verify MeterValues data storage
- **`test_stop_transaction_db.py`** - Verify StopTransaction session completion
- **`test_status_notification_db.py`** - Verify StatusNotification connector status tracking

### Setup Scripts
- **`setup_test_tags.py`** - Create test ID tags in database for authorization testing

## Usage

### 1. End-to-End Testing
```bash
# Start the OCPP server
python app/main.py

# In another terminal, run the mock client
python tests/mock_client.py
```

### 2. Database Verification
```bash
# Check specific functionality
python tests/test_boot_notification_db.py
python tests/test_start_transaction_db.py
python tests/test_stop_transaction_db.py
python tests/test_status_notification_db.py
# ... etc
```

### 3. Setup Test Data
```bash
# Create test ID tags
python tests/setup_test_tags.py
```

## Test Data

The tests use these ID tags:
- `VALID001`, `VALID002` - Accepted tags
- `BLOCKED001` - Blocked tag
- `EXPIRED001` - Expired tag
- `CHILD001` - Child tag with parent relationship

## OCPP 1.6 Compliance

All tests verify OCPP 1.6 Core Profile compliance including:
- Message structure validation
- Required/optional field handling
- Error response behavior
- Database persistence
- Energy calculation accuracy 