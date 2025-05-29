#!/usr/bin/env python3
"""
Test script to verify StatusNotification database operations.
Run this after running the mock client to see if status notifications were properly stored.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.database import AsyncSessionLocal
from app.models import ConnectorStatus, ChargePoint
from sqlalchemy import select, desc


async def test_status_notification_db():
    """Test that StatusNotification properly stores connector status in the database."""
    print("📊 Testing StatusNotification Database Operations")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            # Get all status notifications ordered by most recent first
            result = await session.execute(
                select(ConnectorStatus).order_by(desc(ConnectorStatus.created_at))
            )
            status_notifications = result.scalars().all()

            if not status_notifications:
                print("❌ No status notifications found in database")
                return

            print(
                f"📊 Found {len(status_notifications)} status notifications in database:"
            )
            print()

            # Group by charge point and connector
            by_charge_point = {}
            for status in status_notifications:
                cp_id = status.charge_point_id
                if cp_id not in by_charge_point:
                    by_charge_point[cp_id] = {}

                connector_id = status.connector_id
                if connector_id not in by_charge_point[cp_id]:
                    by_charge_point[cp_id][connector_id] = []

                by_charge_point[cp_id][connector_id].append(status)

            # Display status notifications grouped by charge point and connector
            for cp_id, connectors in by_charge_point.items():
                print(f"🔌 Charge Point: {cp_id}")

                # Get charge point info
                cp_result = await session.execute(
                    select(ChargePoint).where(ChargePoint.id == cp_id)
                )
                charge_point = cp_result.scalar_one_or_none()

                if charge_point:
                    print(f"  Current Status: {charge_point.status}")
                    print(f"  Last Seen: {charge_point.last_seen}")
                    print(f"  Online: {charge_point.is_online}")

                print()

                for connector_id in sorted(connectors.keys()):
                    statuses = connectors[connector_id]
                    connector_type = (
                        "Charge Point"
                        if connector_id == 0
                        else f"Connector {connector_id}"
                    )

                    print(f"  📍 {connector_type}:")
                    print(f"    Total Status Changes: {len(statuses)}")

                    # Show current status (most recent)
                    current_status = statuses[0]
                    print(f"    Current Status: {current_status.status}")
                    print(f"    Current Error Code: {current_status.error_code}")
                    if current_status.info:
                        print(f"    Info: {current_status.info}")
                    print(
                        f"    Last Updated: {current_status.timestamp or current_status.created_at}"
                    )

                    # Show status history (last 5 changes)
                    if len(statuses) > 1:
                        print(f"    📈 Recent Status History:")
                        for i, status in enumerate(statuses[:5]):
                            timestamp = status.timestamp or status.created_at
                            info_text = f" - {status.info}" if status.info else ""
                            error_text = (
                                f" ({status.error_code})"
                                if status.error_code != "NoError"
                                else ""
                            )
                            print(
                                f"      {i+1}. {status.status}{error_text} at {timestamp}{info_text}"
                            )

                    # Show any errors
                    error_statuses = [s for s in statuses if s.error_code != "NoError"]
                    if error_statuses:
                        print(f"    ⚠️  Errors Reported: {len(error_statuses)}")
                        for error_status in error_statuses[:3]:  # Show last 3 errors
                            timestamp = (
                                error_status.timestamp or error_status.created_at
                            )
                            print(
                                f"      - {error_status.error_code}: {error_status.info or 'No details'} at {timestamp}"
                            )
                            if error_status.vendor_error_code:
                                print(
                                    f"        Vendor Code: {error_status.vendor_error_code}"
                                )

                    print()

            # Summary statistics
            total_notifications = len(status_notifications)
            error_notifications = [
                s for s in status_notifications if s.error_code != "NoError"
            ]
            unique_charge_points = len(by_charge_point)

            print(f"📈 Summary Statistics:")
            print(f"  Total Status Notifications: {total_notifications}")
            print(f"  Error Notifications: {len(error_notifications)}")
            print(f"  Charge Points: {unique_charge_points}")

            # Status distribution
            status_counts = {}
            for status in status_notifications:
                status_name = status.status
                status_counts[status_name] = status_counts.get(status_name, 0) + 1

            print(f"  Status Distribution:")
            for status_name, count in sorted(status_counts.items()):
                print(f"    {status_name}: {count}")

            # Error distribution
            if error_notifications:
                error_counts = {}
                for error in error_notifications:
                    error_code = error.error_code
                    error_counts[error_code] = error_counts.get(error_code, 0) + 1

                print(f"  Error Distribution:")
                for error_code, count in sorted(error_counts.items()):
                    print(f"    {error_code}: {count}")

        except Exception as e:
            print(f"❌ Error querying database: {e}")


async def main():
    await test_status_notification_db()


if __name__ == "__main__":
    asyncio.run(main())

