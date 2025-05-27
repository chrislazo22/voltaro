import asyncio
from datetime import datetime
from loguru import logger
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call_result
from ocpp.routing import on


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
        return call_result.BootNotification(
            current_time=datetime.utcnow().isoformat(),
            interval=300,  # Heartbeat interval in seconds
            status="Accepted",
        )
