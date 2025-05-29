"""
Utility functions for OCPP compliance and common operations.
"""

from datetime import datetime, timezone


def utc_now_iso():
    """
    Get current UTC time in ISO format with Z suffix for OCPP compliance.

    OCPP specification strongly recommends using UTC for all time values.
    This function ensures consistent UTC timestamp formatting across the application.

    Returns:
        str: Current UTC time in ISO format with Z suffix (e.g., "2024-01-01T12:00:00.123456Z")
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now_naive():
    """
    Get current UTC time as timezone-naive datetime for database storage.

    This is used for consistent database storage where we store all times
    as timezone-naive UTC datetimes.

    Returns:
        datetime: Current UTC time as timezone-naive datetime
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_ocpp_timestamp(timestamp_str):
    """
    Parse an OCPP timestamp string to timezone-naive UTC datetime.

    Handles both Z suffix and +00:00 timezone formats.

    Args:
        timestamp_str: ISO timestamp string from OCPP message

    Returns:
        datetime: Timezone-naive UTC datetime for database storage
    """
    if timestamp_str.endswith("Z"):
        # Replace Z with +00:00 for parsing
        timestamp_str = timestamp_str[:-1] + "+00:00"

    # Parse and convert to timezone-naive UTC
    dt = datetime.fromisoformat(timestamp_str)
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        # Assume it's already UTC if no timezone info
        return dt

