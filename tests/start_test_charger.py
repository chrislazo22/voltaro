#!/usr/bin/env python3
"""
Simple script to start a test charge point for RemoteStartTransaction testing.
Run this in a separate terminal while the API server is running.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_client import MockClient


async def main():
    """Start a test charge point and keep it running."""
    charge_point_id = "TEST-CP-001"
    
    print("🔌 Starting Test Charge Point")
    print("=" * 40)
    print(f"Charge Point ID: {charge_point_id}")
    print(f"Connecting to: ws://localhost:9000/{charge_point_id}")
    print()
    print("Make sure the API server is running!")
    print("(python start_api_server.py)")
    print()
    
    try:
        # Create and start mock client
        mock_client = MockClient(charge_point_id)
        charge_point = await mock_client.start()
        
        print("✅ Charge Point connected successfully!")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        print()
        print("The charge point is now ready to receive commands:")
        print("  - RemoteStartTransaction")
        print("  - RemoteStopTransaction") 
        print("  - ChangeAvailability")
        print()
        print("You can now test from the web frontend at:")
        print("  http://localhost:3000/chargers")
        print()
        print("Press Ctrl+C to stop the charge point...")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping charge point...")
            
    except Exception as e:
        print(f"❌ Failed to start charge point: {e}")
        return
    
    finally:
        try:
            await mock_client.stop()
            print("✅ Charge point disconnected cleanly")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main()) 