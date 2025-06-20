"""
Main entry point for the OCPP WebSocket server.
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


async def main():
    """Start the WebSocket server."""
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9000, subprotocols=["ocpp1.6"]
    )

    logger.info("OCPP WebSocket server started on ws://0.0.0.0:9000")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
