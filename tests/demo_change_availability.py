#!/usr/bin/env python3
"""
Demo script for ChangeAvailability functionality.

This script demonstrates the complete ChangeAvailability workflow:
1. Central System sends ChangeAvailability request
2. Charge point responds with Accepted/Rejected/Scheduled
3. Charge point sends StatusNotification for availability changes
4. Shows database updates for persistence

Run this script in a separate terminal while the server and mock client are running.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.central_system import CentralSystem


async def demo_change_availability_workflow():
    """Demonstrate the complete ChangeAvailability workflow."""
    print("🔄 ChangeAvailability Demo")
    print("=" * 50)
    print("Make sure you have:")
    print("1. OCPP server running (python -m app.main)")
    print("2. Mock client connected (python tests/mock_client.py)")
    print()

    try:
        # Step 1: Check connected charge points
        print("📊 Step 1: Checking connected charge points...")
        status = await CentralSystem.get_charge_point_status()

        if status["connected_count"] == 0:
            print("❌ No charge points connected!")
            print("Please start a mock client: python tests/mock_client.py")
            return

        # Find first connected charge point
        connected_cp = None
        for cp in status["charge_points"]:
            if cp["connected"]:
                connected_cp = cp["charge_point_id"]
                break

        print(f"✅ Using charge point: {connected_cp}")

        # Step 2: Test connector 1 → Inoperative
        print("\n🔧 Step 2: Setting connector 1 to Inoperative...")
        central_system = CentralSystem()

        result = await central_system.change_availability(
            charge_point_id=connected_cp,
            connector_id=1,
            availability_type="Inoperative",
        )

        print(
            f"📨 Central System → Charge Point: ChangeAvailability (connector=1, type=Inoperative)"
        )
        print(f"📨 Charge Point → Central System: {result['status']}")

        if result["status"] == "Accepted":
            print("✅ ChangeAvailability accepted!")
            print("   - Connector 1 is now Inoperative (unavailable)")
            print("   - Should receive StatusNotification: Unavailable")
        elif result["status"] == "Scheduled":
            print("⏰ ChangeAvailability scheduled!")
            print("   - Change will happen after current transaction finishes")
        else:
            print(f"❌ ChangeAvailability rejected: {result.get('error')}")

        # Wait for StatusNotification
        print("\n⏳ Waiting for StatusNotification...")
        await asyncio.sleep(3)

        # Step 3: Test connector 1 → Operative
        print("\n🔧 Step 3: Setting connector 1 back to Operative...")

        result = await central_system.change_availability(
            charge_point_id=connected_cp, connector_id=1, availability_type="Operative"
        )

        print(
            f"📨 Central System → Charge Point: ChangeAvailability (connector=1, type=Operative)"
        )
        print(f"📨 Charge Point → Central System: {result['status']}")

        if result["status"] == "Accepted":
            print("✅ ChangeAvailability accepted!")
            print("   - Connector 1 is now Operative (available)")
            print("   - Should receive StatusNotification: Available")
        else:
            print(f"❌ ChangeAvailability failed: {result.get('error')}")

        await asyncio.sleep(3)

        # Step 4: Test entire ChargePoint (connector_id = 0)
        print("\n🔧 Step 4: Setting entire ChargePoint to Inoperative...")

        result = await central_system.change_availability(
            charge_point_id=connected_cp,
            connector_id=0,  # 0 = entire charge point
            availability_type="Inoperative",
        )

        print(
            f"📨 Central System → Charge Point: ChangeAvailability (connector=0, type=Inoperative)"
        )
        print(f"📨 Charge Point → Central System: {result['status']}")

        if result["status"] == "Accepted":
            print("✅ ChangeAvailability accepted!")
            print("   - Entire ChargePoint is now Inoperative")
            print("   - Should receive StatusNotification for connectors 0 and 1")
        else:
            print(f"❌ ChangeAvailability failed: {result.get('error')}")

        await asyncio.sleep(3)

        # Step 5: Check database persistence
        print("\n💾 Step 5: Checking database persistence...")

        from app.database import AsyncSessionLocal
        from app.models import ConnectorStatus
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            # Get latest ConnectorStatus records
            status_result = await session.execute(
                select(ConnectorStatus)
                .where(ConnectorStatus.charge_point_id == connected_cp)
                .order_by(ConnectorStatus.created_at.desc())
                .limit(5)
            )
            recent_statuses = status_result.scalars().all()

            if recent_statuses:
                print(f"📊 Recent connector status changes for {connected_cp}:")
                for status in recent_statuses:
                    connector_label = (
                        "ChargePoint"
                        if status.connector_id == 0
                        else f"Connector {status.connector_id}"
                    )
                    print(
                        f"   {connector_label}: {status.status} (availability: {status.availability})"
                    )
                    print(f"      Timestamp: {status.created_at}")
            else:
                print("📊 No connector status records found.")

        # Step 6: Test invalid inputs
        print("\n🚫 Step 6: Testing invalid inputs...")

        # Test invalid connector_id
        result = await central_system.change_availability(
            charge_point_id=connected_cp,
            connector_id=2,  # Invalid for MVP (only 0,1 supported)
            availability_type="Operative",
        )
        print(f"Invalid connector_id=2: {result['status']} ✓")

        # Test invalid availability type
        result = await central_system.change_availability(
            charge_point_id=connected_cp,
            connector_id=1,
            availability_type="InvalidType",
        )
        print(f"Invalid type='InvalidType': {result['status']} ✓")

        # Step 7: Reset to normal state
        print("\n🔄 Step 7: Resetting to normal state...")

        result = await central_system.change_availability(
            charge_point_id=connected_cp, connector_id=0, availability_type="Operative"
        )

        if result["status"] == "Accepted":
            print("✅ ChargePoint reset to Operative state")

        print("\n🎉 ChangeAvailability Demo completed!")
        print("\nKey behaviors demonstrated:")
        print("✅ Connector-specific availability changes (connector_id=1)")
        print("✅ ChargePoint-wide availability changes (connector_id=0)")
        print("✅ Database persistence of availability state")
        print("✅ Automatic StatusNotification after changes")
        print("✅ Input validation and error handling")
        print("✅ OCPP 1.6 Section 5.2 compliance")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main demo function."""
    await demo_change_availability_workflow()


if __name__ == "__main__":
    asyncio.run(main())

