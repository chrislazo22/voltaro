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
            await asyncio.gather(cp.start(), send_messages(cp))
    except Exception as e:
        print(f"Error: {e}")


async def send_messages(cp):
    """Send BootNotification followed by periodic heartbeats."""
    # Wait a moment for the connection to be fully established
    await asyncio.sleep(1)

    # Send BootNotification first
    await send_boot_notification(cp)

    # Send a few heartbeats with delays
    for i in range(3):
        await asyncio.sleep(2)  # Wait 2 seconds between heartbeats
        await send_heartbeat(cp, i + 1)


async def send_boot_notification(cp):
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


async def send_heartbeat(cp, sequence_number):
    print(f"Sending Heartbeat #{sequence_number}...")
    request = call.Heartbeat()

    try:
        response = await cp.call(request)
        print(f"Heartbeat #{sequence_number} response: {response}")
        print(f"Server Time: {response.current_time}")
    except Exception as e:
        print(f"Failed to send Heartbeat #{sequence_number}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
