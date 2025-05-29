"""
Connection manager for storing and retrieving connected charge points.
This module avoids circular imports between main.py and central_system.py.
"""

import asyncio
from datetime import datetime, timezone
from loguru import logger
from app.database import AsyncSessionLocal
from app.models import ChargePoint as ChargePointModel
from app.utils import utc_now_naive
from sqlalchemy import select

# Global dictionary to store connected charge points for Central System operations
# This is only valid within the server process
_connected_charge_points = {}


async def register_charge_point(charge_point_id: str, charge_point_instance):
    """Register a connected charge point."""
    _connected_charge_points[charge_point_id] = charge_point_instance
    logger.info(
        f"Registered charge point {charge_point_id} for Central System operations"
    )

    # Update database to reflect connection status
    try:
        async with AsyncSessionLocal() as session:
            # Get or create charge point record
            cp_result = await session.execute(
                select(ChargePointModel).where(ChargePointModel.id == charge_point_id)
            )
            cp_record = cp_result.scalar_one_or_none()

            if cp_record:
                cp_record.is_online = True
                cp_record.last_seen = utc_now_naive()
                cp_record.status = "Available"  # Default status when connecting
            else:
                # Create new charge point record if it doesn't exist
                cp_record = ChargePointModel(
                    id=charge_point_id,
                    is_online=True,
                    last_seen=utc_now_naive(),
                    status="Available",
                    vendor="Mock",  # Default for test clients
                    model="TestCP",
                )
                session.add(cp_record)

            await session.commit()
            logger.info(f"Updated database: {charge_point_id} is now online")

    except Exception as e:
        logger.error(
            f"Failed to update database for charge point {charge_point_id}: {e}"
        )


async def unregister_charge_point(charge_point_id: str):
    """Unregister a charge point when it disconnects."""
    if charge_point_id in _connected_charge_points:
        del _connected_charge_points[charge_point_id]
        logger.info(
            f"Unregistered charge point {charge_point_id} from Central System operations"
        )

    # Update database to reflect disconnection
    try:
        async with AsyncSessionLocal() as session:
            cp_result = await session.execute(
                select(ChargePointModel).where(ChargePointModel.id == charge_point_id)
            )
            cp_record = cp_result.scalar_one_or_none()

            if cp_record:
                cp_record.is_online = False
                cp_record.last_seen = utc_now_naive()
                await session.commit()
                logger.info(f"Updated database: {charge_point_id} is now offline")

    except Exception as e:
        logger.error(
            f"Failed to update database for charge point {charge_point_id}: {e}"
        )


def get_connected_charge_point(charge_point_id: str):
    """Get a connected charge point instance for Central System operations."""
    return _connected_charge_points.get(charge_point_id)


def get_all_connected_charge_points():
    """Get all connected charge points."""
    return dict(_connected_charge_points)


def get_connected_charge_point_ids():
    """Get list of connected charge point IDs."""
    return list(_connected_charge_points.keys())


def is_charge_point_connected(charge_point_id: str):
    """Check if a charge point is currently connected."""
    return charge_point_id in _connected_charge_points


async def get_database_connection_status():
    """Get connection status from database (works across processes)."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ChargePointModel))
            charge_points = result.scalars().all()

            status_info = {
                "total_charge_points": len(charge_points),
                "connected_count": sum(1 for cp in charge_points if cp.is_online),
                "charge_points": [],
            }

            for cp in charge_points:
                status_info["charge_points"].append(
                    {
                        "charge_point_id": cp.id,
                        "connected": cp.is_online,
                        "online": cp.is_online,
                        "status": cp.status,
                        "last_seen": cp.last_seen.isoformat() if cp.last_seen else None,
                        "vendor": cp.vendor,
                        "model": cp.model,
                    }
                )

            return status_info

    except Exception as e:
        logger.error(f"Failed to get database connection status: {e}")
        return {
            "error": str(e),
            "total_charge_points": 0,
            "connected_count": 0,
            "charge_points": [],
        }

