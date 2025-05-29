#!/usr/bin/env python3
"""
Demo script for RemoteStartTransaction functionality.

This script demonstrates the complete workflow:
1. Central System sends RemoteStartTransaction
2. Charge point responds and changes status
3. Optionally triggers actual StartTransaction
4. Shows database updates

Run this script in a separate terminal while the server and mock client are running.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.central_system import CentralSystem


async def demo_remote_start_workflow():
    """Demonstrate the complete RemoteStartTransaction workflow."""
    print("🚀 RemoteStartTransaction Demo")
    print("=" * 50)
    print("Make sure you have:")
    print("1. OCPP server running (python app/main.py)")
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

        # Step 2: Send RemoteStartTransaction
        print("\n🔋 Step 2: Sending RemoteStartTransaction...")
        print("Requesting charge point to start transaction with:")
        print("  - ID Tag: VALID001")
        print("  - Connector: 1")

        result = await CentralSystem.remote_start_transaction(
            charge_point_id=connected_cp, id_tag="VALID001", connector_id=1
        )

        print(f"\n📨 Central System → Charge Point: RemoteStartTransaction")
        print(f"📨 Charge Point → Central System: {result['status']}")

        if result["success"]:
            print("✅ RemoteStartTransaction accepted!")
            print("\nWhat happens next:")
            print("1. Charge point may send StatusNotification (Preparing)")
            print("2. User presents ID tag or charge point auto-starts")
            print("3. Charge point sends StartTransaction")
            print("4. Charging session begins")
        else:
            print(f"❌ RemoteStartTransaction rejected: {result.get('error')}")

        # Step 3: Wait a moment and check for any new sessions
        print("\n⏳ Step 3: Waiting for potential session creation...")
        await asyncio.sleep(2)

        # Check if any sessions were created
        from app.database import AsyncSessionLocal
        from app.models import Session
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            recent_sessions = await session.execute(
                select(Session)
                .where(Session.charge_point_id == connected_cp)
                .order_by(Session.created_at.desc())
                .limit(3)
            )
            sessions = recent_sessions.scalars().all()

            if sessions:
                print(f"📊 Recent sessions for {connected_cp}:")
                for sess in sessions:
                    print(
                        f"  Transaction {sess.transaction_id}: {sess.status} "
                        f"(Connector {sess.connector_id}, Tag: {sess.id_tag})"
                    )
            else:
                print("📊 No sessions found yet.")

        # Step 4: Demonstrate RemoteStopTransaction
        print("\n🛑 Step 4: Demonstrating RemoteStopTransaction...")

        # Find an active session
        async with AsyncSessionLocal() as session:
            active_session_result = await session.execute(
                select(Session)
                .where(Session.charge_point_id == connected_cp)
                .where(Session.status == "Active")
                .order_by(Session.created_at.desc())
                .limit(1)
            )
            active_session = active_session_result.scalar_one_or_none()

            if active_session:
                print(f"Found active session: {active_session.transaction_id}")

                stop_result = await CentralSystem.remote_stop_transaction(
                    charge_point_id=connected_cp,
                    transaction_id=active_session.transaction_id,
                )

                print(f"📨 Central System → Charge Point: RemoteStopTransaction")
                print(f"📨 Charge Point → Central System: {stop_result['status']}")

                if stop_result["success"]:
                    print("✅ RemoteStopTransaction accepted!")
                    print("The charge point should now stop the transaction.")
                else:
                    print(
                        f"❌ RemoteStopTransaction failed: {stop_result.get('error')}"
                    )
            else:
                print("No active sessions to stop.")

        print("\n🎉 Demo completed!")
        print("\nNext steps:")
        print("- Check the mock client output for status changes")
        print("- Run database verification scripts")
        print(
            "- Try the comprehensive test: python tests/test_remote_start_transaction.py"
        )

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main demo function."""
    await demo_remote_start_workflow()


if __name__ == "__main__":
    asyncio.run(main())

