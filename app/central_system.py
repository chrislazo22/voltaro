"""
Central System operations for sending commands to charge points.
"""

import asyncio
from datetime import datetime, timezone
from loguru import logger
from ocpp.v16 import call
from app.connection_manager import (
    get_connected_charge_point,
    get_all_connected_charge_points,
    get_database_connection_status,
)
from app.database import AsyncSessionLocal
from app.models import ChargePoint as ChargePointModel, IdTag, Session
from app.utils import utc_now_iso, utc_now_naive
from sqlalchemy import select


class CentralSystem:
    """Central System operations for managing charge points."""

    @staticmethod
    async def remote_start_transaction(
        charge_point_id: str,
        id_tag: str,
        connector_id: int = None,
        charging_profile: dict = None,
    ):
        """
        Send RemoteStartTransaction request to a charge point.

        Args:
            charge_point_id: ID of the target charge point
            id_tag: ID tag to authorize the transaction
            connector_id: Optional specific connector ID
            charging_profile: Optional charging profile configuration

        Returns:
            dict: Response from charge point with status
        """
        logger.info(
            f"Central System initiating RemoteStartTransaction to {charge_point_id}: "
            f"idTag={id_tag}, connectorId={connector_id}"
        )

        # Get the connected charge point (in-memory WebSocket connection)
        charge_point = get_connected_charge_point(charge_point_id)
        if not charge_point:
            # Check if it exists in database but not connected to this process
            async with AsyncSessionLocal() as session:
                try:
                    cp_record = await session.get(ChargePointModel, charge_point_id)
                    if cp_record and cp_record.is_online:
                        logger.error(
                            f"Charge point {charge_point_id} is online in database but not connected to this Central System process"
                        )
                        return {
                            "success": False,
                            "error": "Charge point is online but not connected to this Central System process. Central System operations must run in the same process as the OCPP server.",
                            "status": "Rejected",
                        }
                    else:
                        logger.error(f"Charge point {charge_point_id} is not connected")
                        return {
                            "success": False,
                            "error": "Charge point not connected",
                            "status": "Rejected",
                        }
                except Exception as e:
                    logger.error(f"Failed to check charge point status: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to check charge point status: {e}",
                        "status": "Rejected",
                    }

        try:
            # Validate ID tag first
            id_tag_validation = await CentralSystem.validate_id_tag(id_tag)
            if not id_tag_validation["valid"]:
                logger.info(
                    f"RemoteStartTransaction rejected: ID tag {id_tag} is {id_tag_validation['status']}"
                )
                return {
                    "success": False,
                    "error": f"ID tag validation failed: {id_tag_validation['reason']}",
                    "status": "Rejected",
                    "id_tag_status": id_tag_validation["status"],
                }

            # Build the request parameters
            request_params = {"id_tag": id_tag}

            if connector_id is not None:
                request_params["connector_id"] = connector_id

            if charging_profile is not None:
                request_params["charging_profile"] = charging_profile

            # Create and send the RemoteStartTransaction request
            request = call.RemoteStartTransaction(**request_params)
            response = await charge_point.call(request)

            logger.info(
                f"RemoteStartTransaction response from {charge_point_id}: {response.status}"
            )

            return {
                "success": True,
                "status": response.status,
                "charge_point_id": charge_point_id,
                "id_tag": id_tag,
                "connector_id": connector_id,
                "timestamp": utc_now_iso(),
            }

        except Exception as e:
            logger.error(
                f"Failed to send RemoteStartTransaction to {charge_point_id}: {e}"
            )
            return {"success": False, "error": str(e), "status": "Rejected"}

    @staticmethod
    async def remote_stop_transaction(charge_point_id: str, transaction_id: int):
        """
        Send RemoteStopTransaction request to a charge point.

        Args:
            charge_point_id: ID of the target charge point
            transaction_id: ID of the transaction to stop

        Returns:
            dict: Response from charge point with status
        """
        logger.info(
            f"Central System initiating RemoteStopTransaction to {charge_point_id}: "
            f"transactionId={transaction_id}"
        )

        # Validate transaction exists and is active before sending request
        async with AsyncSessionLocal() as session:
            try:
                # Check if transaction exists and belongs to the specified charge point
                session_result = await session.execute(
                    select(Session)
                    .where(Session.transaction_id == transaction_id)
                    .where(Session.charge_point_id == charge_point_id)
                )
                session_record = session_result.scalar_one_or_none()

                if not session_record:
                    logger.error(
                        f"Transaction {transaction_id} not found for charge point {charge_point_id}"
                    )
                    return {
                        "success": False,
                        "error": f"Transaction {transaction_id} not found for charge point {charge_point_id}",
                        "status": "Rejected",
                    }

                if session_record.status != "Active":
                    logger.error(
                        f"Transaction {transaction_id} is not active (status: {session_record.status})"
                    )
                    return {
                        "success": False,
                        "error": f"Transaction {transaction_id} is not active (status: {session_record.status})",
                        "status": "Rejected",
                    }

                logger.info(
                    f"Transaction {transaction_id} validated: Active on connector {session_record.connector_id}"
                )

            except Exception as e:
                logger.error(f"Failed to validate transaction {transaction_id}: {e}")
                return {
                    "success": False,
                    "error": f"Failed to validate transaction: {e}",
                    "status": "Rejected",
                }

        # Get the connected charge point
        charge_point = get_connected_charge_point(charge_point_id)
        if not charge_point:
            logger.error(f"Charge point {charge_point_id} is not connected")
            return {
                "success": False,
                "error": "Charge point not connected",
                "status": "Rejected",
            }

        try:
            # Create and send the RemoteStopTransaction request
            request = call.RemoteStopTransaction(transaction_id=transaction_id)
            response = await charge_point.call(request)

            logger.info(
                f"RemoteStopTransaction response from {charge_point_id}: {response.status}"
            )

            return {
                "success": True,
                "status": response.status,
                "charge_point_id": charge_point_id,
                "transaction_id": transaction_id,
                "timestamp": utc_now_iso(),
            }

        except Exception as e:
            logger.error(
                f"Failed to send RemoteStopTransaction to {charge_point_id}: {e}"
            )
            return {"success": False, "error": str(e), "status": "Rejected"}

    @staticmethod
    async def get_charge_point_status(charge_point_id: str = None):
        """
        Get status of charge points.

        Args:
            charge_point_id: Optional specific charge point ID

        Returns:
            dict: Status information
        """
        if charge_point_id:
            # Get specific charge point status from database
            async with AsyncSessionLocal() as session:
                try:
                    cp_record = await session.get(ChargePointModel, charge_point_id)
                    if cp_record:
                        # Check if it's actually connected in this process (for Central System operations)
                        in_memory_connected = (
                            get_connected_charge_point(charge_point_id) is not None
                        )

                        return {
                            "charge_point_id": charge_point_id,
                            "connected": cp_record.is_online,  # Use database status for cross-process
                            "in_memory_connected": in_memory_connected,  # For debugging
                            "online": cp_record.is_online,
                            "status": cp_record.status,
                            "last_seen": (
                                cp_record.last_seen.isoformat()
                                if cp_record.last_seen
                                else None
                            ),
                            "vendor": cp_record.vendor,
                            "model": cp_record.model,
                        }
                    else:
                        return {
                            "charge_point_id": charge_point_id,
                            "connected": False,
                            "error": "Charge point not found in database",
                        }
                except Exception as e:
                    logger.error(f"Failed to get charge point status: {e}")
                    return {
                        "charge_point_id": charge_point_id,
                        "connected": False,
                        "error": str(e),
                    }
        else:
            # Get all charge points status from database (works across processes)
            try:
                return await get_database_connection_status()
            except Exception as e:
                logger.error(f"Failed to get all charge points status: {e}")
                return {
                    "error": str(e),
                    "total_charge_points": 0,
                    "connected_count": 0,
                    "charge_points": [],
                }

    @staticmethod
    async def validate_id_tag(id_tag: str):
        """
        Validate an ID tag against the database.

        Args:
            id_tag: ID tag to validate

        Returns:
            dict: Validation result
        """
        async with AsyncSessionLocal() as session:
            try:
                # Check if ID tag exists and is valid
                tag_result = await session.execute(
                    select(IdTag).where(IdTag.tag == id_tag)
                )
                tag_record = tag_result.scalar_one_or_none()

                if not tag_record:
                    return {
                        "id_tag": id_tag,
                        "valid": False,
                        "status": "Invalid",
                        "reason": "ID tag not found",
                    }

                # Check if tag is blocked (status field instead of is_blocked)
                if tag_record.status == "Blocked":
                    return {
                        "id_tag": id_tag,
                        "valid": False,
                        "status": "Blocked",
                        "reason": "ID tag is blocked",
                    }

                # Check expiry date
                if tag_record.expiry_date and tag_record.expiry_date < utc_now_naive():
                    return {
                        "id_tag": id_tag,
                        "valid": False,
                        "status": "Expired",
                        "reason": "ID tag has expired",
                        "expiry_date": tag_record.expiry_date.isoformat(),
                    }

                # Tag is valid
                return {
                    "id_tag": id_tag,
                    "valid": True,
                    "status": "Accepted",
                    "expiry_date": (
                        tag_record.expiry_date.isoformat()
                        if tag_record.expiry_date
                        else None
                    ),
                    "parent_id_tag": tag_record.parent_id_tag,
                }

            except Exception as e:
                logger.error(f"Failed to validate ID tag {id_tag}: {e}")
                return {
                    "id_tag": id_tag,
                    "valid": False,
                    "status": "Invalid",
                    "error": str(e),
                }

    async def change_availability(
        self, charge_point_id: str, connector_id: int, availability_type: str
    ):
        """
        Send ChangeAvailability request to a charge point.

        According to OCPP 1.6 Section 5.2:
        - Central System can request a Charge Point to change its availability
        - availability_type: "Operative" (available) or "Inoperative" (unavailable)
        - connector_id: 0 for entire charge point, >0 for specific connector
        - Response: "Accepted", "Rejected", or "Scheduled"

        Args:
            charge_point_id: Target charge point identifier
            connector_id: 0 for charge point, 1+ for specific connector (MVP: 0 or 1)
            availability_type: "Operative" or "Inoperative"

        Returns:
            dict: Response with status and details
        """
        logger.info(
            f"Sending ChangeAvailability to {charge_point_id}: "
            f"connectorId={connector_id}, type={availability_type}"
        )

        # Validate inputs
        if availability_type not in ["Operative", "Inoperative"]:
            logger.error(f"Invalid availability type: {availability_type}")
            return {
                "status": "Rejected",
                "error": f"Invalid availability type: {availability_type}",
            }

        # MVP: Validate connector_id (0 = charge point, 1 = single connector)
        if connector_id < 0 or connector_id > 1:
            logger.error(f"Invalid connector_id: {connector_id} (MVP supports 0 or 1)")
            return {
                "status": "Rejected",
                "error": f"Invalid connector_id: {connector_id} (MVP supports 0 or 1)",
            }

        async with AsyncSessionLocal() as session:
            try:
                # Validate charge point exists and is online
                charge_point = await session.get(ChargePointModel, charge_point_id)
                if not charge_point:
                    logger.warning(f"Charge point not found: {charge_point_id}")
                    return {
                        "status": "Rejected",
                        "error": f"Charge point not found: {charge_point_id}",
                    }

                if not charge_point.is_online:
                    logger.warning(f"Charge point offline: {charge_point_id}")
                    return {
                        "status": "Rejected",
                        "error": f"Charge point offline: {charge_point_id}",
                    }

                # Get charge point connection
                charge_point_connection = get_connected_charge_point(charge_point_id)
                if not charge_point_connection:
                    logger.warning(f"No active connection for: {charge_point_id}")
                    return {
                        "status": "Rejected",
                        "error": f"No active connection for: {charge_point_id}",
                    }

                # Send ChangeAvailability request
                request = call.ChangeAvailability(
                    connector_id=connector_id, type=availability_type
                )

                try:
                    response = await charge_point_connection.call(request)

                    logger.info(
                        f"ChangeAvailability response from {charge_point_id}: {response.status}"
                    )

                    return {
                        "status": response.status,
                        "charge_point_id": charge_point_id,
                        "connector_id": connector_id,
                        "availability_type": availability_type,
                        "timestamp": utc_now_iso(),
                    }

                except Exception as call_error:
                    logger.error(
                        f"Failed to send ChangeAvailability to {charge_point_id}: {call_error}"
                    )
                    return {
                        "status": "Rejected",
                        "error": f"Communication error: {str(call_error)}",
                    }

            except Exception as e:
                logger.error(f"Failed to process ChangeAvailability request: {e}")
                await session.rollback()
                return {
                    "status": "Rejected",
                    "error": f"Database error: {str(e)}",
                }


# Convenience functions for easy access
async def start_remote_transaction(
    charge_point_id: str, id_tag: str, connector_id: int = None
):
    """Convenience function to start a remote transaction."""
    return await CentralSystem.remote_start_transaction(
        charge_point_id, id_tag, connector_id
    )


async def stop_remote_transaction(charge_point_id: str, transaction_id: int):
    """Convenience function to stop a remote transaction."""
    return await CentralSystem.remote_stop_transaction(charge_point_id, transaction_id)


async def get_charge_point_status(charge_point_id: str = None):
    """Convenience function to get charge point status."""
    return await CentralSystem.get_charge_point_status(charge_point_id)
