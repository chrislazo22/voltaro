import asyncio
import websockets
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call
from datetime import datetime, timedelta


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
    """Send BootNotification, heartbeats, authorization, and start transaction."""
    # Wait a moment for the connection to be fully established
    await asyncio.sleep(1)

    # Send BootNotification first
    await send_boot_notification(cp)

    # Send a couple of heartbeats
    for i in range(2):
        await asyncio.sleep(2)  # Wait 2 seconds between heartbeats
        await send_heartbeat(cp, i + 1)

    # Test authorization with different ID tags
    test_tags = [
        "VALID001",  # Should be accepted
        "VALID002",  # Should be accepted
        "BLOCKED001",  # Should be blocked
        "EXPIRED001",  # Should be expired
        "CHILD001",  # Should be accepted with parent
        "UNKNOWN123",  # Should be invalid (not in database)
    ]

    print("\n🔐 Testing Authorization...")
    for tag in test_tags:
        await asyncio.sleep(1)  # Wait between authorization requests
        await send_authorize(cp, tag)

    # Test StartTransaction with valid and invalid tags
    print("\n🔋 Testing StartTransaction...")

    # Test with valid tag
    await asyncio.sleep(2)
    await send_start_transaction(cp, "VALID001", connector_id=1, meter_start=1000)

    # Test with blocked tag
    await asyncio.sleep(2)
    await send_start_transaction(cp, "BLOCKED001", connector_id=2, meter_start=2000)

    # Test with unknown tag
    await asyncio.sleep(2)
    await send_start_transaction(cp, "UNKNOWN123", connector_id=1, meter_start=3000)

    # Test MeterValues during charging
    print("\n⚡ Testing MeterValues...")

    # Send some meter values for an active transaction
    await asyncio.sleep(2)
    await send_meter_values(
        cp, connector_id=1, transaction_id=None
    )  # Without transaction

    await asyncio.sleep(2)
    await send_meter_values(
        cp, connector_id=1, transaction_id=123456
    )  # With transaction (if exists)


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


async def send_authorize(cp, tag):
    print(f"Sending Authorize request with tag: {tag}")
    request = call.Authorize(id_tag=tag)

    try:
        response = await cp.call(request)
        print(f"Authorize response for {tag}: {response}")
        print(f"  Status: {response.id_tag_info['status']}")

        # Show additional info if present
        if "expiryDate" in response.id_tag_info:
            print(f"  Expiry Date: {response.id_tag_info['expiryDate']}")
        if "parentIdTag" in response.id_tag_info:
            print(f"  Parent Tag: {response.id_tag_info['parentIdTag']}")

    except Exception as e:
        print(f"Failed to send Authorize request for {tag}: {e}")


async def send_start_transaction(cp, tag, connector_id, meter_start):
    print(
        f"Sending StartTransaction request with tag: {tag}, connector_id: {connector_id}, meter_start: {meter_start}"
    )
    request = call.StartTransaction(
        id_tag=tag,
        connector_id=connector_id,
        meter_start=meter_start,
        timestamp=datetime.utcnow().isoformat(),
    )

    try:
        response = await cp.call(request)
        print(f"StartTransaction response for {tag}: {response}")
        print(f"  Status: {response.id_tag_info['status']}")
        print(f"  Transaction ID: {response.transaction_id}")

        # Show additional info if present
        if "expiryDate" in response.id_tag_info:
            print(f"  Expiry Date: {response.id_tag_info['expiryDate']}")
        if "parentIdTag" in response.id_tag_info:
            print(f"  Parent Tag: {response.id_tag_info['parentIdTag']}")

    except Exception as e:
        print(f"Failed to send StartTransaction request for {tag}: {e}")


async def send_meter_values(cp, connector_id, transaction_id=None):
    print(
        f"Sending MeterValues for connector {connector_id}, transaction_id: {transaction_id}"
    )

    # Create sample meter values with different measurands
    meter_values = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "sampledValue": [
                {
                    "value": "15420",
                    "context": "Sample.Periodic",
                    "measurand": "Energy.Active.Import.Register",
                    "unit": "Wh",
                    "location": "Outlet",
                },
                {
                    "value": "7.2",
                    "context": "Sample.Periodic",
                    "measurand": "Power.Active.Import",
                    "unit": "kW",
                    "location": "Outlet",
                },
                {
                    "value": "32.1",
                    "context": "Sample.Periodic",
                    "measurand": "Current.Import",
                    "unit": "A",
                    "phase": "L1",
                    "location": "Outlet",
                },
            ],
        },
        {
            "timestamp": (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
            "sampledValue": [
                {
                    "value": "15450",
                    "context": "Sample.Periodic",
                    "measurand": "Energy.Active.Import.Register",
                    "unit": "Wh",
                    "location": "Outlet",
                },
                {
                    "value": "230.5",
                    "context": "Sample.Periodic",
                    "measurand": "Voltage",
                    "unit": "V",
                    "phase": "L1",
                    "location": "Outlet",
                },
            ],
        },
    ]

    # Build request
    request_params = {"connector_id": connector_id, "meter_value": meter_values}

    if transaction_id:
        request_params["transaction_id"] = transaction_id

    request = call.MeterValues(**request_params)

    try:
        response = await cp.call(request)
        print(f"MeterValues response: {response}")
        print(f"  Successfully sent {len(meter_values)} meter value sets")

    except Exception as e:
        print(f"Failed to send MeterValues: {e}")


if __name__ == "__main__":
    asyncio.run(main())
