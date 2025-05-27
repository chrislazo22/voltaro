import asyncio
from datetime import datetime, timezone
from loguru import logger
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call_result
from ocpp.routing import on
from app.database import AsyncSessionLocal
from app.models import ChargePoint as ChargePointModel, IdTag, Session
from sqlalchemy import select
import random


class ChargePoint(ChargePointV16):
    """
    Custom ChargePoint class for handling OCPP 1.6 messages.
    """

    @on("BootNotification")
    async def on_boot_notification(
        self, charge_point_vendor, charge_point_model, **kwargs
    ):
        logger.info(
            f"BootNotification received from {self.id}: vendor={charge_point_vendor}, model={charge_point_model}"
        )

        # Store/update charge point in database
        async with AsyncSessionLocal() as session:
            try:
                # Check if charge point already exists
                charge_point = await session.get(ChargePointModel, self.id)

                if charge_point is None:
                    # Create new charge point
                    charge_point = ChargePointModel(
                        id=self.id,
                        vendor=charge_point_vendor,
                        model=charge_point_model,
                        charge_point_serial_number=kwargs.get(
                            "charge_point_serial_number"
                        ),
                        charge_box_serial_number=kwargs.get("charge_box_serial_number"),
                        firmware_version=kwargs.get("firmware_version"),
                        iccid=kwargs.get("iccid"),
                        imsi=kwargs.get("imsi"),
                        meter_type=kwargs.get("meter_type"),
                        meter_serial_number=kwargs.get("meter_serial_number"),
                        is_online=True,
                        last_seen=datetime.utcnow(),
                        boot_status="Accepted",
                    )
                    session.add(charge_point)
                    logger.info(f"Created new charge point: {self.id}")
                else:
                    # Update existing charge point
                    charge_point.vendor = charge_point_vendor
                    charge_point.model = charge_point_model
                    charge_point.charge_point_serial_number = kwargs.get(
                        "charge_point_serial_number"
                    )
                    charge_point.charge_box_serial_number = kwargs.get(
                        "charge_box_serial_number"
                    )
                    charge_point.firmware_version = kwargs.get("firmware_version")
                    charge_point.iccid = kwargs.get("iccid")
                    charge_point.imsi = kwargs.get("imsi")
                    charge_point.meter_type = kwargs.get("meter_type")
                    charge_point.meter_serial_number = kwargs.get("meter_serial_number")
                    charge_point.is_online = True
                    charge_point.last_seen = datetime.utcnow()
                    charge_point.boot_status = "Accepted"
                    charge_point.updated_at = datetime.utcnow()
                    logger.info(f"Updated existing charge point: {self.id}")

                await session.commit()
                logger.info(f"BootNotification data stored in database for {self.id}")

            except Exception as e:
                logger.error(f"Failed to store BootNotification data: {e}")
                await session.rollback()
                # Continue with response even if DB fails

        # Return OCPP 1.6 compliant response
        return call_result.BootNotification(
            current_time=datetime.utcnow().isoformat(),
            interval=300,  # Heartbeat interval in seconds
            status="Accepted",
        )

    @on("Heartbeat")
    async def on_heartbeat(self):
        """Handle Heartbeat requests - update last_seen timestamp."""
        logger.info(f"Heartbeat received from {self.id}")

        # Update last_seen timestamp in database
        async with AsyncSessionLocal() as session:
            try:
                charge_point = await session.get(ChargePointModel, self.id)

                if charge_point:
                    charge_point.last_seen = datetime.utcnow()
                    charge_point.is_online = True
                    charge_point.updated_at = datetime.utcnow()
                    await session.commit()
                    logger.debug(f"Updated last_seen for charge point {self.id}")
                else:
                    logger.warning(
                        f"Received heartbeat from unknown charge point: {self.id}"
                    )

            except Exception as e:
                logger.error(f"Failed to update heartbeat timestamp: {e}")
                await session.rollback()
                # Continue with response even if DB fails

        # Return OCPP 1.6 compliant response with current time
        return call_result.Heartbeat(current_time=datetime.utcnow().isoformat())

    @on("Authorize")
    async def on_authorize(self, id_tag):
        """Handle Authorize requests - validate ID tag against database."""
        logger.info(f"Authorize request received from {self.id} for idTag: {id_tag}")

        # Get ID tag info (reuse logic from authorize)
        id_tag_info = await self._get_id_tag_info(id_tag)

        # Return OCPP 1.6 compliant response
        return call_result.Authorize(id_tag_info=id_tag_info)

    @on("StartTransaction")
    async def on_start_transaction(
        self, connector_id, id_tag, meter_start, timestamp, **kwargs
    ):
        """Handle StartTransaction requests - create new charging session."""
        logger.info(
            f"StartTransaction received from {self.id}: connector={connector_id}, idTag={id_tag}, meterStart={meter_start}"
        )

        # Get ID tag info and validate authorization
        id_tag_info = await self._get_id_tag_info(id_tag)

        # Default transaction ID (will be updated if session is created)
        transaction_id = 0

        # Only create session if tag is accepted
        if id_tag_info["status"] == "Accepted":
            async with AsyncSessionLocal() as session:
                try:
                    # Get the ID tag record
                    tag_result = await session.execute(
                        select(IdTag).where(IdTag.tag == id_tag)
                    )
                    tag_record = tag_result.scalar_one_or_none()

                    if tag_record:
                        # Generate unique transaction ID
                        transaction_id = await self._generate_transaction_id(session)

                        # Parse timestamp
                        if isinstance(timestamp, str):
                            start_time = datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            )
                        else:
                            start_time = timestamp

                        # Create new session
                        new_session = Session(
                            transaction_id=transaction_id,
                            charge_point_id=self.id,
                            id_tag_id=tag_record.id,
                            connector_id=connector_id,
                            meter_start=meter_start,
                            start_timestamp=start_time,
                            status="Active",
                            reservation_id=kwargs.get("reservation_id"),
                        )
                        session.add(new_session)
                        await session.commit()

                        logger.info(
                            f"Created session {transaction_id} for {self.id} connector {connector_id}"
                        )
                    else:
                        logger.error(f"ID tag {id_tag} not found when creating session")
                        id_tag_info = {"status": "Invalid"}

                except Exception as e:
                    logger.error(f"Failed to create session: {e}")
                    await session.rollback()
                    id_tag_info = {"status": "Invalid"}
        else:
            logger.info(
                f"StartTransaction rejected for {id_tag}: {id_tag_info['status']}"
            )

        # Return OCPP 1.6 compliant response
        return call_result.StartTransaction(
            id_tag_info=id_tag_info, transaction_id=transaction_id
        )

    async def _get_id_tag_info(self, id_tag):
        """Helper method to get ID tag info (shared between Authorize and StartTransaction)."""
        # Default response for unknown/invalid tags
        id_tag_info = {"status": "Invalid"}

        # Look up ID tag in database
        async with AsyncSessionLocal() as session:
            try:
                # Query for the ID tag
                result = await session.execute(select(IdTag).where(IdTag.tag == id_tag))
                tag_record = result.scalar_one_or_none()

                if tag_record:
                    # Check if tag is expired
                    if (
                        tag_record.expiry_date
                        and tag_record.expiry_date < datetime.utcnow()
                    ):
                        id_tag_info = {
                            "status": "Expired",
                            "expiryDate": tag_record.expiry_date.isoformat(),
                        }
                        logger.info(f"ID tag {id_tag} is expired")
                    else:
                        # Use the tag's current status
                        id_tag_info = {"status": tag_record.status}

                        # Add optional fields if present
                        if tag_record.expiry_date:
                            id_tag_info["expiryDate"] = (
                                tag_record.expiry_date.isoformat()
                            )
                        if tag_record.parent_id_tag:
                            id_tag_info["parentIdTag"] = tag_record.parent_id_tag

                        logger.info(
                            f"ID tag {id_tag} authorized with status: {tag_record.status}"
                        )
                else:
                    logger.info(f"ID tag {id_tag} not found in database")

            except Exception as e:
                logger.error(f"Failed to lookup ID tag {id_tag}: {e}")
                # Return Invalid status on database error
                id_tag_info = {"status": "Invalid"}

        return id_tag_info

    async def _generate_transaction_id(self, session):
        """Generate a unique transaction ID."""
        # Simple approach: use random number and check for uniqueness
        # In production, you might use a sequence or UUID
        while True:
            transaction_id = random.randint(100000, 999999)

            # Check if this ID already exists
            result = await session.execute(
                select(Session).where(Session.transaction_id == transaction_id)
            )
            existing = result.scalar_one_or_none()

            if not existing:
                return transaction_id
