#!/usr/bin/env python3
"""
Test script for RemoteStartTransaction functionality.

This script demonstrates:
1. Central System sending RemoteStartTransaction requests
2. Charge point responding to the requests
3. Validation of ID tags and connector availability
4. Database verification of the operations

Run this after starting the server and connecting a mock client.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.central_system import CentralSystem
from app.database import AsyncSessionLocal
from app.models import ChargePoint, IdTag, Session, ConnectorStatus
from sqlalchemy import select


async def test_remote_start_transaction():
    """Test RemoteStartTransaction functionality."""
    print("🚀 Testing RemoteStartTransaction Functionality")
    print("=" * 60)

    # Test 1: Get charge point status
    print("\n📊 Step 1: Getting charge point status...")
    try:
        status = await CentralSystem.get_charge_point_status()
        print(f"Total charge points: {status.get('total_charge_points', 0)}")
        print(f"Connected charge points: {status.get('connected_count', 0)}")

        if status.get("charge_points"):
            for cp in status["charge_points"]:
                print(
                    f"  - {cp['charge_point_id']}: Connected={cp['connected']}, Status={cp.get('status', 'Unknown')}"
                )

        # Find a connected charge point for testing
        connected_cp = None
        if status.get("charge_points"):
            for cp in status["charge_points"]:
                if cp["connected"]:
                    connected_cp = cp["charge_point_id"]
                    break

        if not connected_cp:
            print(
                "\n❌ No connected charge points found. Please start a mock client first."
            )
            print("Run: python tests/mock_client.py")
            return

        print(f"\n✅ Using charge point: {connected_cp}")

        # Test 2: Validate ID tags
        print("\n🏷️  Step 2: Validating ID tags...")
        test_tags = ["VALID001", "VALID002", "BLOCKED001", "INVALID999"]

        for tag in test_tags:
            validation = await CentralSystem.validate_id_tag(tag)
            print(
                f"  {tag}: {validation['status']} - {validation.get('reason', 'Valid')}"
            )

        # Test 3: Remote start with valid tag
        print("\n🔋 Step 3: Testing RemoteStartTransaction with valid tag...")
        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp, id_tag="VALID001", connector_id=1
        )

        print(f"Result: {result}")
        if result["success"]:
            print(f"✅ RemoteStartTransaction {result['status']}")
        else:
            print(f"❌ RemoteStartTransaction failed: {result.get('error')}")

        # Test 4: Remote start with invalid tag
        print("\n🚫 Step 4: Testing RemoteStartTransaction with invalid tag...")
        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp, id_tag="INVALID999", connector_id=1
        )

        print(f"Result: {result}")
        if result["status"] == "Rejected":
            print("✅ Correctly rejected invalid tag")
        else:
            print("❌ Should have rejected invalid tag")

        # Test 5: Remote start with blocked tag
        print("\n🔒 Step 5: Testing RemoteStartTransaction with blocked tag...")
        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp, id_tag="BLOCKED001", connector_id=1
        )

        print(f"Result: {result}")
        if result["status"] == "Rejected":
            print("✅ Correctly rejected blocked tag")
        else:
            print("❌ Should have rejected blocked tag")

        # Test 6: Remote start without specific connector
        print(
            "\n🔌 Step 6: Testing RemoteStartTransaction without specific connector..."
        )
        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp, id_tag="VALID002"
        )

        print(f"Result: {result}")
        if result["success"]:
            print(f"✅ RemoteStartTransaction {result['status']} (any connector)")
        else:
            print(f"❌ RemoteStartTransaction failed: {result.get('error')}")

        # Test 7: Remote start with charging profile
        print("\n⚡ Step 7: Testing RemoteStartTransaction with charging profile...")
        charging_profile = {
            "chargingProfileId": 1,
            "stackLevel": 0,
            "chargingProfilePurpose": "TxProfile",
            "chargingProfileKind": "Relative",
            "chargingSchedule": {
                "chargingRateUnit": "A",
                "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 16.0}],
            },
        }

        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp,
            id_tag="VALID001",
            connector_id=2,
            charging_profile=charging_profile,
        )

        print(f"Result: {result}")
        if result["success"]:
            print(f"✅ RemoteStartTransaction with charging profile {result['status']}")
        else:
            print(
                f"❌ RemoteStartTransaction with charging profile failed: {result.get('error')}"
            )

        # Test 8: Try to start on disconnected charge point
        print(
            "\n📡 Step 8: Testing RemoteStartTransaction on disconnected charge point..."
        )
        result = await CentralSystem.remote_start_transaction(
            charge_point_id="DISCONNECTED_CP", id_tag="VALID001", connector_id=1
        )

        print(f"Result: {result}")
        if not result["success"] and "not connected" in result.get("error", ""):
            print("✅ Correctly rejected disconnected charge point")
        else:
            print("❌ Should have rejected disconnected charge point")

        # Test 9: Check database for any sessions created
        print("\n💾 Step 9: Checking database for sessions...")
        async with AsyncSessionLocal() as session:
            try:
                # Get recent sessions
                sessions_result = await session.execute(
                    select(Session)
                    .where(Session.charge_point_id == connected_cp)
                    .order_by(Session.created_at.desc())
                    .limit(5)
                )
                sessions = sessions_result.scalars().all()

                print(f"Recent sessions for {connected_cp}:")
                for sess in sessions:
                    print(
                        f"  Transaction {sess.transaction_id}: {sess.status} "
                        f"(Connector {sess.connector_id})"
                    )

            except Exception as e:
                print(f"Error checking database: {e}")

        print("\n🎉 RemoteStartTransaction testing completed!")
        print(
            "\nNote: RemoteStartTransaction acceptance doesn't automatically create sessions."
        )
        print("The charge point would typically respond by:")
        print("1. Sending StatusNotification (Preparing)")
        print("2. Initiating the actual transaction")
        print("3. Sending StartTransaction request")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


async def test_remote_stop_transaction():
    """Test RemoteStopTransaction functionality."""
    print("\n🛑 Testing RemoteStopTransaction Functionality")
    print("=" * 60)

    try:
        # Find a connected charge point
        status = await CentralSystem.get_charge_point_status()
        connected_cp = None
        if status.get("charge_points"):
            for cp in status["charge_points"]:
                if cp["connected"]:
                    connected_cp = cp["charge_point_id"]
                    break

        if not connected_cp:
            print("❌ No connected charge points found.")
            return

        # Find an active session to stop
        async with AsyncSessionLocal() as session:
            try:
                sessions_result = await session.execute(
                    select(Session)
                    .where(Session.charge_point_id == connected_cp)
                    .where(Session.status == "Active")
                    .order_by(Session.created_at.desc())
                    .limit(1)
                )
                active_session = sessions_result.scalar_one_or_none()

                if active_session:
                    print(f"Found active session: {active_session.transaction_id}")

                    # Test remote stop
                    result = await CentralSystem.remote_stop_transaction(
                        charge_point_id=connected_cp,
                        transaction_id=active_session.transaction_id,
                    )

                    print(f"RemoteStopTransaction result: {result}")
                    if result["success"]:
                        print(f"✅ RemoteStopTransaction {result['status']}")
                    else:
                        print(f"❌ RemoteStopTransaction failed: {result.get('error')}")
                else:
                    print("No active sessions found to stop.")

                    # Test with a fake transaction ID
                    result = await CentralSystem.remote_stop_transaction(
                        charge_point_id=connected_cp, transaction_id=999999
                    )

                    print(f"RemoteStopTransaction (fake ID) result: {result}")

            except Exception as e:
                print(f"Error testing RemoteStopTransaction: {e}")

    except Exception as e:
        print(f"❌ Error during RemoteStopTransaction testing: {e}")


async def main():
    """Main test function."""
    print("RemoteStartTransaction Test Suite")
    print("Make sure the OCPP server is running and a mock client is connected!")
    print("Commands to run first:")
    print("1. python app/main.py")
    print("2. python tests/mock_client.py")
    print()

    await test_remote_start_transaction()
    await test_remote_stop_transaction()


if __name__ == "__main__":
    asyncio.run(main())
