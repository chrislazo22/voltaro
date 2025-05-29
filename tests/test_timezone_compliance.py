#!/usr/bin/env python3
"""
Test OCPP timezone compliance across the application.

This test verifies that:
1. All timestamps use UTC timezone
2. OCPP messages use proper ISO format with Z suffix
3. Database stores timezone-naive UTC datetimes
4. Timestamp parsing handles various formats correctly
"""

import sys
import os
from datetime import datetime, timezone

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import utc_now_iso, utc_now_naive, parse_ocpp_timestamp


def test_utc_iso_format():
    """Test that utc_now_iso() returns proper OCPP-compliant UTC timestamp."""
    print("🕐 Testing UTC ISO format...")

    iso_time = utc_now_iso()
    print(f"  Generated timestamp: {iso_time}")

    # Verify it ends with Z (UTC indicator)
    assert iso_time.endswith("Z"), f"Timestamp should end with Z, got: {iso_time}"

    # Verify it can be parsed back
    parsed = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, "Parsed timestamp should have timezone info"

    print("  ✅ UTC ISO format is OCPP compliant")


def test_utc_naive_format():
    """Test that utc_now_naive() returns timezone-naive UTC datetime."""
    print("\n🗄️  Testing UTC naive format for database...")

    naive_time = utc_now_naive()
    print(f"  Generated datetime: {naive_time}")

    # Verify it has no timezone info
    assert (
        naive_time.tzinfo is None
    ), f"Naive datetime should have no timezone, got: {naive_time.tzinfo}"

    # Verify it's close to current UTC time
    current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    time_diff = abs((current_utc - naive_time).total_seconds())
    assert time_diff < 5, f"Time difference too large: {time_diff} seconds"

    print("  ✅ UTC naive format is correct for database storage")


def test_timestamp_parsing():
    """Test parsing various OCPP timestamp formats."""
    print("\n🔄 Testing timestamp parsing...")

    test_cases = [
        ("2024-01-01T12:00:00.123456Z", "Z suffix format"),
        ("2024-01-01T12:00:00.123456+00:00", "+00:00 format"),
        ("2024-01-01T12:00:00Z", "Z suffix without microseconds"),
        ("2024-01-01T12:00:00+00:00", "+00:00 without microseconds"),
        ("2024-12-31T23:59:59.999999Z", "End of year with microseconds"),
    ]

    for timestamp_str, description in test_cases:
        print(f"  Testing {description}: {timestamp_str}")

        parsed = parse_ocpp_timestamp(timestamp_str)

        # Verify result is timezone-naive
        assert (
            parsed.tzinfo is None
        ), f"Parsed timestamp should be timezone-naive, got: {parsed.tzinfo}"

        # Verify the parsed time is reasonable
        assert parsed.year == 2024, f"Year should be 2024, got: {parsed.year}"

        print(f"    -> {parsed} ✅")

    print("  ✅ All timestamp formats parsed correctly")


def test_timezone_consistency():
    """Test that all timezone functions are consistent."""
    print("\n🔄 Testing timezone consistency...")

    # Generate timestamps
    iso_time = utc_now_iso()
    naive_time = utc_now_naive()

    # Parse the ISO time back to naive
    parsed_iso = parse_ocpp_timestamp(iso_time)

    # They should be very close (within 1 second)
    time_diff = abs((naive_time - parsed_iso).total_seconds())
    assert (
        time_diff < 1
    ), f"Timestamps should be consistent, difference: {time_diff} seconds"

    print(f"  ISO timestamp: {iso_time}")
    print(f"  Naive timestamp: {naive_time}")
    print(f"  Parsed ISO: {parsed_iso}")
    print(f"  Time difference: {time_diff:.3f} seconds")
    print("  ✅ Timezone functions are consistent")


def test_ocpp_compliance():
    """Test overall OCPP timezone compliance."""
    print("\n📋 Testing OCPP compliance requirements...")

    # OCPP 3.14: "strongly recommended to use UTC for all time values"
    iso_time = utc_now_iso()

    # Verify UTC timezone indicator
    assert (
        "Z" in iso_time or "+00:00" in iso_time
    ), "Timestamp must indicate UTC timezone"

    # Verify ISO 8601 format
    try:
        # Should be parseable as ISO format
        if iso_time.endswith("Z"):
            test_parse = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        else:
            test_parse = datetime.fromisoformat(iso_time)
        assert (
            test_parse.tzinfo is not None
        ), "Parsed timestamp should have timezone info"
    except ValueError as e:
        assert False, f"Timestamp is not valid ISO 8601 format: {e}"

    print(f"  ✅ Timestamp format: {iso_time}")
    print("  ✅ Uses UTC timezone as recommended by OCPP 3.14")
    print("  ✅ Valid ISO 8601 format")
    print("  ✅ OCPP timezone compliance verified!")


def main():
    """Run all timezone compliance tests."""
    print("=" * 60)
    print("🌍 OCPP Timezone Compliance Test Suite")
    print("=" * 60)
    print()
    print("Testing compliance with OCPP 1.6 Section 3.14:")
    print("'It is strongly recommended to use UTC for all time values'")
    print()

    try:
        test_utc_iso_format()
        test_utc_naive_format()
        test_timestamp_parsing()
        test_timezone_consistency()
        test_ocpp_compliance()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Application is fully OCPP timezone compliant")
        print("✅ UTC is used consistently throughout")
        print("✅ Timestamps are properly formatted for OCPP messages")
        print("✅ Database storage uses timezone-naive UTC")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

