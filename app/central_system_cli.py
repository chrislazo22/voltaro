"""
Central System Command Line Interface for real-time OCPP operations.
This runs within the server process and has access to connected charge points.
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger
from app.connection_manager import (
    get_all_connected_charge_points,
    get_connected_charge_point,
)
from app.central_system import CentralSystem


class CentralSystemCLI:
    """Interactive command-line interface for Central System operations."""

    def __init__(self):
        self.running = False

    async def start(self):
        """Start the CLI interface."""
        self.running = True
        print("\n" + "=" * 60)
        print("🎯 OCPP Central System Command Interface")
        print("=" * 60)
        print("Available commands:")
        print("  status                    - Show charge point status")
        print("  list                      - List connected charge points")
        print("  start <cp_id> <id_tag>    - Remote start transaction")
        print(
            "  start <cp_id> <id_tag> <connector> - Remote start on specific connector"
        )
        print("  stop <cp_id> <tx_id>      - Remote stop transaction")
        print("  validate <id_tag>         - Validate ID tag")
        print("  help                      - Show this help")
        print("  quit                      - Exit CLI")
        print("=" * 60)

        while self.running:
            try:
                # Show prompt with connected charge points count
                connected = get_all_connected_charge_points()
                prompt = f"Central System ({len(connected)} CPs connected) > "

                # Get user input
                command = await self._get_input(prompt)
                if command:
                    await self._process_command(command.strip())

            except KeyboardInterrupt:
                print("\n👋 Exiting Central System CLI...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    async def _get_input(self, prompt):
        """Get user input asynchronously."""
        print(prompt, end="", flush=True)

        # Use asyncio to read from stdin without blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sys.stdin.readline)

    async def _process_command(self, command):
        """Process a CLI command."""
        if not command:
            return

        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "quit" or cmd == "exit":
            self.running = False
            print("👋 Goodbye!")

        elif cmd == "help":
            await self._show_help()

        elif cmd == "status":
            await self._show_status()

        elif cmd == "list":
            await self._list_charge_points()

        elif cmd == "start":
            await self._remote_start(parts[1:])

        elif cmd == "stop":
            await self._remote_stop(parts[1:])

        elif cmd == "validate":
            await self._validate_tag(parts[1:])

        else:
            print(f"❌ Unknown command: {cmd}")
            print("Type 'help' for available commands")

    async def _show_help(self):
        """Show help information."""
        print("\n📋 Central System Commands:")
        print("-" * 40)
        print("status                     - Show overall system status")
        print("list                       - List all connected charge points")
        print("start CP001 VALID001       - Start transaction on any connector")
        print("start CP001 VALID001 2     - Start transaction on connector 2")
        print("stop CP001 123456          - Stop transaction 123456")
        print("validate VALID001          - Check if ID tag is valid")
        print("help                       - Show this help")
        print("quit                       - Exit CLI")
        print()

    async def _show_status(self):
        """Show system status."""
        print("\n📊 System Status:")
        print("-" * 30)

        try:
            status = await CentralSystem.get_charge_point_status()
            print(f"Total charge points: {status.get('total_charge_points', 0)}")
            print(f"Connected: {status.get('connected_count', 0)}")

            if status.get("charge_points"):
                print("\nCharge Points:")
                for cp in status["charge_points"]:
                    status_icon = "🟢" if cp["connected"] else "🔴"
                    print(
                        f"  {status_icon} {cp['charge_point_id']}: {cp.get('status', 'Unknown')}"
                    )
                    if cp.get("last_seen"):
                        print(f"     Last seen: {cp['last_seen']}")
        except Exception as e:
            print(f"❌ Error getting status: {e}")
        print()

    async def _list_charge_points(self):
        """List connected charge points."""
        print("\n🔌 Connected Charge Points:")
        print("-" * 35)

        connected = get_all_connected_charge_points()
        if connected:
            for cp_id, cp_instance in connected.items():
                print(f"  🟢 {cp_id} - Ready for Central System operations")
        else:
            print("  No charge points currently connected")
        print()

    async def _remote_start(self, args):
        """Handle remote start command."""
        if len(args) < 2:
            print("❌ Usage: start <charge_point_id> <id_tag> [connector_id]")
            return

        cp_id = args[0]
        id_tag = args[1]
        connector_id = int(args[2]) if len(args) > 2 else None

        print(f"\n🔋 Sending RemoteStartTransaction:")
        print(f"   Charge Point: {cp_id}")
        print(f"   ID Tag: {id_tag}")
        print(f"   Connector: {connector_id if connector_id else 'Any'}")

        try:
            result = await CentralSystem.remote_start_transaction(
                charge_point_id=cp_id, id_tag=id_tag, connector_id=connector_id
            )

            if result["success"]:
                print(f"   ✅ Response: {result['status']}")
                if result["status"] == "Accepted":
                    print("   🎉 Transaction start request accepted!")
                    print("   📊 Watch for StatusNotification messages...")
                else:
                    print(f"   ⚠️ Request was rejected by charge point")
            else:
                print(f"   ❌ Failed: {result.get('error')}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

    async def _remote_stop(self, args):
        """Handle remote stop command."""
        if len(args) < 2:
            print("❌ Usage: stop <charge_point_id> <transaction_id>")
            return

        cp_id = args[0]
        try:
            tx_id = int(args[1])
        except ValueError:
            print("❌ Transaction ID must be a number")
            return

        print(f"\n🛑 Sending RemoteStopTransaction:")
        print(f"   Charge Point: {cp_id}")
        print(f"   Transaction ID: {tx_id}")

        try:
            result = await CentralSystem.remote_stop_transaction(
                charge_point_id=cp_id, transaction_id=tx_id
            )

            if result["success"]:
                print(f"   ✅ Response: {result['status']}")
                if result["status"] == "Accepted":
                    print("   🎉 Transaction stop request accepted!")
                else:
                    print(f"   ⚠️ Request was rejected by charge point")
            else:
                print(f"   ❌ Failed: {result.get('error')}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

    async def _validate_tag(self, args):
        """Handle validate tag command."""
        if len(args) < 1:
            print("❌ Usage: validate <id_tag>")
            return

        id_tag = args[0]

        print(f"\n🏷️  Validating ID Tag: {id_tag}")

        try:
            result = await CentralSystem.validate_id_tag(id_tag)

            status_icon = "✅" if result["status"] == "Accepted" else "❌"
            print(f"   {status_icon} Status: {result['status']}")

            if result.get("reason"):
                print(f"   📝 Reason: {result['reason']}")

            if result.get("expiry_date"):
                print(f"   📅 Expires: {result['expiry_date']}")

            if result.get("parent_id_tag"):
                print(f"   👨‍👩‍👧‍👦 Parent Tag: {result['parent_id_tag']}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()


# Global CLI instance
_cli_instance = None


async def start_cli():
    """Start the Central System CLI."""
    global _cli_instance
    if _cli_instance is None:
        _cli_instance = CentralSystemCLI()
    await _cli_instance.start()


def is_cli_running():
    """Check if CLI is running."""
    global _cli_instance
    return _cli_instance is not None and _cli_instance.running

