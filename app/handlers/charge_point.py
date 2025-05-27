import asyncio
from datetime import datetime, timezone
from loguru import logger
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call_result
from ocpp.routing import on
from app.database import AsyncSessionLocal
from app.models import ChargePoint as ChargePointModel, IdTag
from sqlalchemy import select


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

        # Return OCPP 1.6 compliant response
        return call_result.Authorize(id_tag_info=id_tag_info)
