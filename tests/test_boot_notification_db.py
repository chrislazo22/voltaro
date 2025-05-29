#!/usr/bin/env python3
"""
Test script to verify BootNotification database operations.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.database import AsyncSessionLocal, close_db
from app.models import ChargePoint
from sqlalchemy import select
from loguru import logger


async def check_boot_notification_data():
    """Check if BootNotification data was stored correctly."""
    try:
        async with AsyncSessionLocal() as session:
            # Query for the charge point
            charge_point = await session.get(ChargePoint, "CP001")

            if charge_point:
                print("✅ Charge Point found in database:")
                print(f"  ID: {charge_point.id}")
                print(f"  Vendor: {charge_point.vendor}")
                print(f"  Model: {charge_point.model}")
                print(f"  Serial Number: {charge_point.charge_point_serial_number}")
                print(f"  Charge Box Serial: {charge_point.charge_box_serial_number}")
                print(f"  Firmware Version: {charge_point.firmware_version}")
                print(f"  Meter Type: {charge_point.meter_type}")
                print(f"  Meter Serial: {charge_point.meter_serial_number}")
                print(f"  Online Status: {charge_point.is_online}")
                print(f"  Last Seen: {charge_point.last_seen}")
                print(f"  Boot Status: {charge_point.boot_status}")
                print(f"  Created At: {charge_point.created_at}")
                print(f"  Updated At: {charge_point.updated_at}")

                return True
            else:
                print("❌ No charge point found with ID 'CP001'")
                return False

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(check_boot_notification_data())
    if success:
        print("\n✅ BootNotification database storage is working correctly!")
    else:
        print("\n❌ BootNotification database storage test failed.")

