"""
Enhanced OCPP WebSocket server with integrated Central System CLI.
This version includes a command-line interface for Central System operations.
"""

import asyncio
import logging
from datetime import datetime
from loguru import logger
import websockets
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v201 import ChargePoint as ChargePointV201
from app.handlers.charge_point import ChargePoint
from app.connection_manager import register_charge_point, unregister_charge_point
from app.central_system_cli import start_cli

# Configure logging
logger.add(
    "logs/ocpp_server.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


async def on_connect(websocket, path):
    """Handle new WebSocket connections."""
    charge_point_id = None
    try:
        requested_protocols = websocket.request_headers.get(
            "Sec-WebSocket-Protocol", ""
        ).split(",")
        logger.info(f"Client connected. Requested protocols: {requested_protocols}")

        # For now, we'll only support OCPP 1.6
        if "ocpp1.6" in requested_protocols:
            charge_point_id = path.strip("/")
            cp = ChargePoint(charge_point_id, websocket)

            # Register the charge point for Central System operations
            await register_charge_point(charge_point_id, cp)

            await cp.start()
        else:
            logger.warning(f"Unsupported protocol requested: {requested_protocols}")
            await websocket.close(1002, "Unsupported protocol")
    except Exception as e:
        logger.error(f"Error handling connection: {e}")
        await websocket.close(1011, "Internal error")
    finally:
        # Unregister the charge point when connection closes
        if charge_point_id:
            await unregister_charge_point(charge_point_id)


async def start_server():
    """Start the WebSocket server."""
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9000, subprotocols=["ocpp1.6"]
    )

    logger.info("OCPP WebSocket server started on ws://0.0.0.0:9000")
    logger.info("Central System CLI will start in 3 seconds...")

    # Wait a moment for server to fully start
    await asyncio.sleep(3)

    return server


async def main():
    """Start the WebSocket server with Central System CLI."""
    print("🚀 Starting OCPP Server with Central System CLI")
    print("=" * 60)

    # Start the WebSocket server
    server = await start_server()

    # Start the Central System CLI
    print("\n🎯 Starting Central System Command Interface...")
    print("You can now send RemoteStartTransaction commands!")
    print("Type 'help' for available commands.")

    # Run both server and CLI concurrently
    try:
        await asyncio.gather(server.wait_closed(), start_cli())
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logger.error(f"Server error: {e}")

