# OCPP Timezone Compliance Implementation

## Overview

This document describes the timezone compliance implementation for Voltaro's OCPP 1.6 system, following the OCPP specification section 3.14 which states:

> "OCPP does not prescribe the use of a specific time zone for time values. However, it is strongly recommended to use UTC for all time values to improve interoperability between Central Systems and Charge Points."

## Implementation Strategy

### 1. Consistent UTC Usage

All timestamps throughout the application use UTC timezone to ensure interoperability:

- **OCPP Messages**: Use ISO 8601 format with 'Z' suffix (e.g., `2024-01-01T12:00:00.123456Z`)
- **Database Storage**: Use timezone-naive UTC datetimes for consistent storage
- **Internal Processing**: All datetime operations use UTC timezone

### 2. Utility Functions

Created standardized utility functions in `app/utils.py`:

```python
def utc_now_iso():
    """Get current UTC time in ISO format with Z suffix for OCPP compliance."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def utc_now_naive():
    """Get current UTC time as timezone-naive datetime for database storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def parse_ocpp_timestamp(timestamp_str):
    """Parse OCPP timestamp string to timezone-naive UTC datetime."""
    # Handles both 'Z' suffix and '+00:00' formats
```

### 3. Updated Components

#### Central System (`app/central_system.py`)
- Uses `utc_now_iso()` for response timestamps
- Uses `utc_now_naive()` for database comparisons
- Replaced deprecated `datetime.utcnow()` calls

#### Charge Point Handler (`app/handlers/charge_point.py`)
- Uses `utc_now_iso()` for OCPP response timestamps
- Uses `utc_now_naive()` for database storage
- Uses `parse_ocpp_timestamp()` for incoming timestamp parsing
- Consistent timezone handling across all message types

#### Connection Manager (`app/connection_manager.py`)
- Uses `utc_now_naive()` for database timestamp updates
- Consistent with charge point handler timezone approach

#### Mock Client (`tests/mock_client.py`)
- Uses `utc_now_iso()` for all outgoing OCPP messages
- Ensures test messages are OCPP compliant

## Timezone Formats

### OCPP Message Format
```
2024-01-01T12:00:00.123456Z
```
- ISO 8601 format with microsecond precision
- 'Z' suffix explicitly indicates UTC timezone
- Used in all OCPP message exchanges

### Database Storage Format
```
2024-01-01 12:00:00.123456
```
- Timezone-naive UTC datetime
- Consistent storage without timezone confusion
- All database timestamps are implicitly UTC

## Compliance Verification

### Test Suite
Created `tests/test_timezone_compliance.py` to verify:

1. **UTC ISO Format**: Timestamps end with 'Z' and are parseable
2. **Database Format**: Timezone-naive UTC datetimes
3. **Timestamp Parsing**: Handles various OCPP timestamp formats
4. **Consistency**: All timezone functions produce consistent results
5. **OCPP Compliance**: Meets OCPP 1.6 section 3.14 requirements

### Test Results
```
✅ Application is fully OCPP timezone compliant
✅ UTC is used consistently throughout
✅ Timestamps are properly formatted for OCPP messages
✅ Database storage uses timezone-naive UTC
```

## Benefits

1. **Interoperability**: UTC usage ensures compatibility with all OCPP systems
2. **Consistency**: Standardized timezone handling across all components
3. **Clarity**: Explicit UTC indication in OCPP messages
4. **Reliability**: No timezone conversion errors or ambiguity
5. **Compliance**: Follows OCPP 1.6 best practices

## Migration Notes

### Changes Made
- Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Added 'Z' suffix to OCPP message timestamps
- Standardized database storage to timezone-naive UTC
- Created utility functions for consistent usage

### Backward Compatibility
- Database timestamps remain timezone-naive (no schema changes needed)
- OCPP message format enhanced but still ISO 8601 compliant
- All existing functionality preserved

## Usage Guidelines

### For OCPP Messages
```python
from app.utils import utc_now_iso

# Use for all OCPP message timestamps
timestamp = utc_now_iso()  # "2024-01-01T12:00:00.123456Z"
```

### For Database Operations
```python
from app.utils import utc_now_naive

# Use for database timestamp fields
last_seen = utc_now_naive()  # 2024-01-01 12:00:00.123456
```

### For Parsing OCPP Timestamps
```python
from app.utils import parse_ocpp_timestamp

# Parse incoming OCPP timestamps
parsed_time = parse_ocpp_timestamp("2024-01-01T12:00:00Z")
```

## Conclusion

The timezone compliance implementation ensures that Voltaro's OCPP system follows best practices for timezone handling, improving interoperability and reliability while maintaining full compliance with OCPP 1.6 specifications. 