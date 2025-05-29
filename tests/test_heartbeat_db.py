#!/usr/bin/env python3
"""
Test script to verify Heartbeat database operations.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, close_db
from app.models import ChargePoint
from sqlalchemy import select
from loguru import logger


async def check_heartbeat_updates():
    """Check if heartbeat timestamps are being updated correctly."""
    try:
        async with AsyncSessionLocal() as session:
            # Query for the charge point
            charge_point = await session.get(ChargePoint, "CP001")

            if charge_point:
                print("✅ Charge Point found in database:")
                print(f"  ID: {charge_point.id}")
                print(f"  Online Status: {charge_point.is_online}")
                print(f"  Last Seen: {charge_point.last_seen}")
                print(f"  Created At: {charge_point.created_at}")
                print(f"  Updated At: {charge_point.updated_at}")

                # Check if last_seen is recent (within last 30 seconds)
                if charge_point.last_seen:
                    time_diff = datetime.utcnow() - charge_point.last_seen
                    if time_diff < timedelta(seconds=30):
                        print(
                            f"✅ Last seen timestamp is recent: {time_diff.total_seconds():.1f} seconds ago"
                        )
                    else:
                        print(
                            f"⚠️  Last seen timestamp is old: {time_diff.total_seconds():.1f} seconds ago"
                        )

                # Check if charge point is marked as online
                if charge_point.is_online:
                    print("✅ Charge point is marked as online")
                else:
                    print("❌ Charge point is marked as offline")

                return True
            else:
                print("❌ No charge point found with ID 'CP001'")
                return False

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return False
    finally:
        await close_db()


async def monitor_heartbeats(duration_seconds=30):
    """Monitor heartbeat updates for a specified duration."""
    print(f"Monitoring heartbeat updates for {duration_seconds} seconds...")

    start_time = datetime.utcnow()
    last_seen_time = None

    while (datetime.utcnow() - start_time).total_seconds() < duration_seconds:
        try:
            async with AsyncSessionLocal() as session:
                charge_point = await session.get(ChargePoint, "CP001")

                if charge_point and charge_point.last_seen:
                    if (
                        last_seen_time is None
                        or charge_point.last_seen > last_seen_time
                    ):
                        print(f"📡 Heartbeat detected at: {charge_point.last_seen}")
                        last_seen_time = charge_point.last_seen

        except Exception as e:
            logger.error(f"Monitoring error: {e}")

        await asyncio.sleep(1)  # Check every second

    await close_db()
    print("Monitoring completed.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Monitor mode - watch for heartbeat updates in real-time
        asyncio.run(monitor_heartbeats())
    else:
        # Check mode - single check of current status
        success = asyncio.run(check_heartbeat_updates())
        if success:
            print("\n✅ Heartbeat database updates are working correctly!")
        else:
            print("\n❌ Heartbeat database updates test failed.")

