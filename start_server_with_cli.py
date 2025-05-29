#!/usr/bin/env python3
"""
Startup script for OCPP Server with Central System CLI.
This script makes it easy to test RemoteStartTransaction functionality.
"""
import os
import sys
import asyncio

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.main_with_cli import main


def print_instructions():
    """Print startup instructions."""
    print("🎯 OCPP Server with Central System CLI")
    print("=" * 50)
    print()
    print("📋 What this does:")
    print("✅ Starts OCPP WebSocket server on ws://0.0.0.0:9000")
    print("✅ Provides Central System command interface")
    print("✅ Allows real-time RemoteStartTransaction testing")
    print()
    print("🔧 Setup Instructions:")
    print("1. Keep this terminal running (server + CLI)")
    print("2. In another terminal, run: python tests/mock_client.py")
    print("3. Come back here and use Central System commands")
    print()
    print("💡 Example Commands (after mock client connects):")
    print("   list                    - See connected charge points")
    print("   start CP001 VALID001    - Start transaction")
    print("   validate BLOCKED001     - Test ID tag validation")
    print("   help                    - Show all commands")
    print()
    print("🚀 Starting server...")
    print()


if __name__ == "__main__":
    print_instructions()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

