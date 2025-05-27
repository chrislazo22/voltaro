import asyncio
import websockets
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call


class ChargePoint(ChargePointV16):
    pass  # No custom handlers needed for the client


async def main():
    uri = "ws://localhost:9000/CP001"
    try:
        async with websockets.connect(uri, subprotocols=["ocpp1.6"]) as ws:
            print(f"Connected to {uri}")
            cp = ChargePoint("CP001", ws)

            # Start the charge point (this handles incoming messages)
            await asyncio.gather(cp.start(), send_boot_notification(cp))
    except Exception as e:
        print(f"Error: {e}")


async def send_boot_notification(cp):
    # Wait a moment for the connection to be fully established
    await asyncio.sleep(1)

    print("Sending BootNotification...")
    request = call.BootNotification(
        charge_point_vendor="MockVendor",
        charge_point_model="MockModel",
        charge_point_serial_number="SN123456789",
        charge_box_serial_number="CB987654321",
        firmware_version="1.0.0",
        meter_type="EnergyMeter",
        meter_serial_number="EM123456",
    )

    try:
        response = await cp.call(request)
        print(f"BootNotification response: {response}")
        print(f"Status: {response.status}")
        print(f"Current Time: {response.current_time}")
        print(f"Heartbeat Interval: {response.interval} seconds")
    except Exception as e:
        print(f"Failed to send BootNotification: {e}")


if __name__ == "__main__":
    asyncio.run(main())
