#!/usr/bin/env python3
"""
Quick script to check charge point connection status.
"""
import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.central_system import CentralSystem


async def check_connections():
    """Check current charge point connections."""
    print("🔍 Checking Charge Point Connections")
    print("=" * 40)

    try:
        status = await CentralSystem.get_charge_point_status()

        print(
            f"Total charge points in database: {status.get('total_charge_points', 0)}"
        )
        print(f"Currently connected: {status.get('connected_count', 0)}")
        print()

        if status.get("charge_points"):
            print("Charge Point Details:")
            for cp in status["charge_points"]:
                connection_status = (
                    "🟢 CONNECTED" if cp["connected"] else "🔴 DISCONNECTED"
                )
                print(f"  {cp['charge_point_id']}: {connection_status}")
                print(f"    Status: {cp.get('status', 'Unknown')}")
                print(f"    Online: {cp.get('online', False)}")
                if cp.get("last_seen"):
                    print(f"    Last seen: {cp['last_seen']}")
                print()
        else:
            print("No charge points found in database.")

        if status.get("connected_count", 0) == 0:
            print("💡 To connect a mock client:")
            print("   1. Make sure the server is running: python app/main.py")
            print("   2. Run the mock client: python tests/mock_client.py")

    except Exception as e:
        print(f"❌ Error checking connections: {e}")
        print("\nMake sure the OCPP server is running:")
        print("  python app/main.py")


if __name__ == "__main__":
    asyncio.run(check_connections())

