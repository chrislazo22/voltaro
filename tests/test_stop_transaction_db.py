#!/usr/bin/env python3
"""
Test script to verify StopTransaction database operations.
Run this after running the mock client to see if sessions were properly stopped.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.database import AsyncSessionLocal
from app.models import Session, MeterValue, IdTag
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload


async def test_stop_transaction_db():
    """Test that StopTransaction properly updates sessions in the database."""
    print("🛑 Testing StopTransaction Database Operations")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            # Get all sessions ordered by most recent first
            result = await session.execute(
                select(Session)
                .options(selectinload(Session.id_tag))  # ✅ preload related ID tags
                .order_by(desc(Session.created_at))
            )
            result = await session.execute(
                select(Session).order_by(desc(Session.created_at))
            )
            sessions = result.scalars().all()

            if not sessions:
                print("❌ No sessions found in database")
                return

            print(f"📊 Found {len(sessions)} sessions in database:")
            print()

            for sess in sessions:
                print(f"Session ID: {sess.id}")
                print(f"  Transaction ID: {sess.transaction_id}")
                print(f"  Charge Point: {sess.charge_point_id}")
                print(f"  Connector: {sess.connector_id}")
                print(f"  Status: {sess.status}")
                print(f"  Start Time: {sess.start_timestamp}")
                print(f"  Stop Time: {sess.stop_timestamp}")
                print(f"  Meter Start: {sess.meter_start} Wh")
                print(f"  Meter Stop: {sess.meter_stop} Wh")

                if sess.energy_consumed is not None:
                    print(f"  Energy Consumed: {sess.energy_consumed:.3f} kWh")
                else:
                    print("  Energy Consumed: Not calculated")

                if sess.stop_reason:
                    print(f"  Stop Reason: {sess.stop_reason}")

                print(f"  Created: {sess.created_at}")
                print(f"  Updated: {sess.updated_at}")

                # Check for meter values associated with this session
                meter_result = await session.execute(
                    select(MeterValue).where(MeterValue.session_id == sess.id)
                )
                meter_values = meter_result.scalars().all()

                if meter_values:
                    print(f"  📈 Meter Values: {len(meter_values)} records")
                    for mv in meter_values[-3:]:  # Show last 3
                        print(
                            f"    - {mv.value} {mv.unit} ({mv.measurand}) at {mv.timestamp}"
                        )
                        print(f"      Context: {mv.context}, Location: {mv.location}")
                else:
                    print("  📈 Meter Values: None")

                # Get ID tag info
                if sess.id_tag:
                    print(
                        f"  🏷️  ID Tag: {sess.id_tag.tag} (Status: {sess.id_tag.status})"
                    )

                print("-" * 40)

            # Summary statistics
            completed_sessions = [s for s in sessions if s.status == "Completed"]
            active_sessions = [s for s in sessions if s.status == "Active"]

            print(f"\n📈 Session Statistics:")
            print(f"  Total Sessions: {len(sessions)}")
            print(f"  Completed Sessions: {len(completed_sessions)}")
            print(f"  Active Sessions: {len(active_sessions)}")

            if completed_sessions:
                total_energy = sum(s.energy_consumed or 0 for s in completed_sessions)
                print(f"  Total Energy Consumed: {total_energy:.3f} kWh")

                avg_energy = total_energy / len(completed_sessions)
                print(f"  Average Energy per Session: {avg_energy:.3f} kWh")

            # Check for any transaction data (meter values with Transaction.End context)
            transaction_end_result = await session.execute(
                select(MeterValue).where(MeterValue.context == "Transaction.End")
            )
            transaction_end_values = transaction_end_result.scalars().all()

            if transaction_end_values:
                print(
                    f"\n📊 Transaction End Data: {len(transaction_end_values)} records"
                )
                for mv in transaction_end_values:
                    print(
                        f"  - Session {mv.session_id}: {mv.value} {mv.unit} ({mv.measurand})"
                    )

        except Exception as e:
            print(f"❌ Error querying database: {e}")


async def main():
    await test_stop_transaction_db()


if __name__ == "__main__":
    asyncio.run(main())

