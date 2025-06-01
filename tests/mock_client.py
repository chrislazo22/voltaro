import asyncio
import websockets
from ocpp.v16 import ChargePoint as ChargePointV16
from ocpp.v16 import call, call_result
from ocpp.routing import on
from datetime import datetime, timedelta, timezone
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils import utc_now_iso


class MockClient:
    """Mock client for testing OCPP functionality."""

    def __init__(self, charge_point_id):
        self.charge_point_id = charge_point_id
        self.charge_point = None
        self.websocket = None

    async def start(self):
        """Connect and start the mock charge point."""
        import websockets

        uri = f"ws://localhost:9000/{self.charge_point_id}"
        try:
            self.websocket = await websockets.connect(uri, subprotocols=["ocpp1.6"])
            self.charge_point = ChargePoint(self.charge_point_id, self.websocket)

            # Start listening for messages in background
            self._message_task = asyncio.create_task(self.charge_point.start())

            # Send BootNotification
            await send_boot_notification(self.charge_point)

            return self.charge_point
        except Exception as e:
            print(f"Failed to connect mock client {self.charge_point_id}: {e}")
            raise

    async def stop(self):
        """Stop and disconnect the mock charge point."""
        if hasattr(self, "_message_task"):
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass
        if self.websocket:
            await self.websocket.close()


class ChargePoint(ChargePointV16):
    """Mock charge point that can handle Central System requests."""

    @on("RemoteStartTransaction")
    async def on_remote_start_transaction(self, id_tag, **kwargs):
        """Handle RemoteStartTransaction requests from Central System."""
        connector_id = kwargs.get("connector_id", 1)  # Default to connector 1
        charging_profile = kwargs.get("charging_profile")

        print(f"\n🔋 Received RemoteStartTransaction request:")
        print(f"  ID Tag: {id_tag}")
        print(f"  Connector ID: {connector_id}")
        if charging_profile:
            print(f"  Charging Profile ID: {charging_profile.get('chargingProfileId')}")

        # Simulate charge point logic
        # For demo purposes, accept most requests except for specific cases
        if id_tag in ["BLOCKED001", "INVALID999", "EXPIRED001"]:
            print(f"  ❌ Rejecting request for {id_tag}")
            return call_result.RemoteStartTransaction(status="Rejected")

        print(f"  ✅ Accepting request for {id_tag}")

        # Schedule the full OCPP flow after accepting the request
        asyncio.create_task(self._handle_remote_start_flow(id_tag, connector_id))

        return call_result.RemoteStartTransaction(status="Accepted")

    async def _handle_remote_start_flow(self, id_tag, connector_id):
        """Handle the complete flow after accepting RemoteStartTransaction."""
        try:
            # Step 1: Send StatusNotification (Preparing)
            await asyncio.sleep(0.5)  # Brief delay to ensure response is sent first
            
            await self._send_status_notification_simple(
                connector_id, "Preparing", "Remote start initiated"
            )
            
            # Step 2: Simulate authorization check (if AuthorizeRemoteTxRequests = true)
            # For this demo, we'll skip Authorize.req and go straight to StartTransaction
            await asyncio.sleep(1.0)  # Simulate preparation time
            
            # Step 3: Send StartTransaction.req (this is required by OCPP spec)
            print(f"  🚀 Starting transaction for {id_tag} on connector {connector_id}")
            
            request = call.StartTransaction(
                connector_id=connector_id,
                id_tag=id_tag,
                meter_start=0,  # Starting meter value
                timestamp=utc_now_iso()
            )
            
            response = await self.call(request)
            transaction_id = response.transaction_id
            
            print(f"  ✅ StartTransaction accepted! Transaction ID: {transaction_id}")
            
            # Step 4: Send StatusNotification (Charging)
            await self._send_status_notification_simple(
                connector_id, "Charging", f"Transaction {transaction_id} in progress"
            )
            
            # Store transaction info for potential remote stop
            if not hasattr(self, '_active_transactions'):
                self._active_transactions = {}
            self._active_transactions[transaction_id] = {
                'id_tag': id_tag,
                'connector_id': connector_id,
                'start_time': utc_now_iso(),
                'meter_start': 0
            }
            
            print(f"  📊 Transaction {transaction_id} is now active and charging")
            
        except Exception as e:
            print(f"  ❌ Error in remote start flow: {e}")
            # Send error status
            await self._send_status_notification_simple(
                connector_id, "Faulted", f"Remote start failed: {str(e)}"
            )

    async def _send_status_notification_simple(self, connector_id, status, info=None):
        """Send a simple StatusNotification."""
        try:
            request = call.StatusNotification(
                connector_id=connector_id,
                error_code="NoError",
                status=status,
                info=info,
                timestamp=utc_now_iso(),
            )
            await self.call(request)
            print(f"  📊 StatusNotification sent: Connector {connector_id} → {status}")
        except Exception as e:
            print(f"  ❌ Failed to send StatusNotification: {e}")

    @on("RemoteStopTransaction")
    async def on_remote_stop_transaction(self, transaction_id):
        """Handle RemoteStopTransaction requests from Central System."""
        print(f"\n🛑 Received RemoteStopTransaction request:")
        print(f"  Transaction ID: {transaction_id}")

        # Check if we have this transaction active
        if not hasattr(self, '_active_transactions'):
            self._active_transactions = {}
        
        if transaction_id not in self._active_transactions:
            print(f"  ❌ Transaction {transaction_id} not found or already stopped")
            return call_result.RemoteStopTransaction(status="Rejected")

        print(f"  ✅ Accepting stop request for transaction {transaction_id}")

        # Schedule the stop transaction flow
        asyncio.create_task(self._handle_remote_stop_flow(transaction_id))

        return call_result.RemoteStopTransaction(status="Accepted")

    async def _handle_remote_stop_flow(self, transaction_id):
        """Handle the complete flow after accepting RemoteStopTransaction."""
        try:
            transaction_info = self._active_transactions.get(transaction_id)
            if not transaction_info:
                print(f"  ❌ Transaction {transaction_id} info not found")
                return
            
            connector_id = transaction_info['connector_id']
            id_tag = transaction_info['id_tag']
            
            # Step 1: Send StatusNotification (Finishing)
            await asyncio.sleep(0.5)  # Brief delay
            await self._send_status_notification_simple(
                connector_id, "Finishing", "Remote stop initiated"
            )
            
            # Step 2: Send StopTransaction.req (required by OCPP spec)
            print(f"  🛑 Stopping transaction {transaction_id}")
            
            request = call.StopTransaction(
                transaction_id=transaction_id,
                meter_stop=1000,  # Simulated final meter reading
                timestamp=utc_now_iso(),
                reason="Remote",
                id_tag=id_tag  # Optional, but good practice
            )
            
            response = await self.call(request)
            print(f"  ✅ StopTransaction completed! ID Tag status: {getattr(response, 'id_tag_info', {}).get('status', 'Unknown')}")
            
            # Step 3: Send StatusNotification (Available)
            await self._send_status_notification_simple(
                connector_id, "Available", f"Transaction {transaction_id} completed"
            )
            
            # Remove from active transactions
            del self._active_transactions[transaction_id]
            print(f"  📊 Transaction {transaction_id} stopped and connector {connector_id} is now available")
            
        except Exception as e:
            print(f"  ❌ Error in remote stop flow: {e}")

    @on("ChangeAvailability")
    async def on_change_availability(self, connector_id, type):
        """Handle ChangeAvailability requests from Central System."""
        print(f"\n🔄 Received ChangeAvailability request:")
        print(f"  Connector ID: {connector_id}")
        print(f"  Type: {type}")

        # Simulate charge point logic
        if connector_id < 0 or connector_id > 1:
            print(f"  ❌ Rejecting request: Invalid connector_id {connector_id}")
            return call_result.ChangeAvailability(status="Rejected")

        if type not in ["Operative", "Inoperative"]:
            print(f"  ❌ Rejecting request: Invalid type {type}")
            return call_result.ChangeAvailability(status="Rejected")

        print(f"  ✅ Accepting ChangeAvailability request")

        # Schedule StatusNotification to be sent after response
        connector_label = (
            "ChargePoint" if connector_id == 0 else f"Connector {connector_id}"
        )
        print(f"  📊 {connector_label} availability changing to {type}")

        # Send StatusNotification after a delay
        asyncio.create_task(
            self._send_availability_status_notification(connector_id, type)
        )

        return call_result.ChangeAvailability(status="Accepted")

    async def _send_status_preparing_delayed(self, connector_id):
        """Send StatusNotification for Preparing state after a short delay."""
        try:
            # Wait a moment to ensure the RemoteStartTransaction response is sent first
            await asyncio.sleep(0.5)

            request = call.StatusNotification(
                connector_id=connector_id,
                error_code="NoError",
                status="Preparing",
                info="Remote start initiated",
                timestamp=utc_now_iso(),
            )
            response = await self.call(request)
            print(
                f"  📊 Sent StatusNotification: Preparing for connector {connector_id}"
            )
        except Exception as e:
            print(f"  ❌ Failed to send StatusNotification: {e}")

    async def _send_status_preparing(self, connector_id):
        """Send StatusNotification for Preparing state."""
        try:
            request = call.StatusNotification(
                connector_id=connector_id,
                error_code="NoError",
                status="Preparing",
                info="Remote start initiated",
                timestamp=utc_now_iso(),
            )
            response = await self.call(request)
            print(
                f"  📊 Sent StatusNotification: Preparing for connector {connector_id}"
            )
        except Exception as e:
            print(f"  ❌ Failed to send StatusNotification: {e}")

    async def _send_availability_status_notification(
        self, connector_id, availability_type
    ):
        """Send StatusNotification after availability change."""
        try:
            await asyncio.sleep(1.0)  # Wait for response to be sent first

            # Determine status based on availability
            status = "Available" if availability_type == "Operative" else "Unavailable"
            info = f"Availability changed to {availability_type}"

            connector_label = (
                "ChargePoint" if connector_id == 0 else f"Connector {connector_id}"
            )

            request = call.StatusNotification(
                connector_id=connector_id,
                error_code="NoError",
                status=status,
                info=info,
                timestamp=utc_now_iso(),
            )

            await self.call(request)
            print(f"  📊 StatusNotification sent: {connector_label} now {status}")

        except Exception as e:
            print(f"  ❌ Failed to send StatusNotification: {e}")


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

    # Test StopTransaction
    print("\n🛑 Testing StopTransaction...")

    # Test stopping a transaction that should exist (if StartTransaction succeeded)
    await asyncio.sleep(2)
    await send_stop_transaction(
        cp,
        transaction_id=123456,  # Assuming this transaction exists from earlier
        meter_stop=25000,
        reason="Local",
        id_tag="VALID001",
    )

    # Test stopping with different scenarios
    await asyncio.sleep(2)
    await send_stop_transaction(
        cp,
        transaction_id=999999,  # Non-existent transaction
        meter_stop=30000,
        reason="Remote",
    )

    # Test stopping with transaction data
    await asyncio.sleep(2)
    await send_stop_transaction(
        cp,
        transaction_id=123457,  # Another transaction
        meter_stop=18000,
        reason="EVDisconnected",
        id_tag="VALID002",
        include_transaction_data=True,
    )

    # Test StatusNotification
    print("\n📊 Testing StatusNotification...")

    # Test charge point status (connector 0)
    await asyncio.sleep(2)
    await send_status_notification(
        cp,
        connector_id=0,
        status="Available",
        error_code="NoError",
        info="Charge point online",
    )

    # Test connector status transitions
    await asyncio.sleep(1)
    await send_status_notification(
        cp, connector_id=1, status="Available", error_code="NoError"
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=1,
        status="Preparing",
        error_code="NoError",
        info="User initiated charging",
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=1,
        status="Charging",
        error_code="NoError",
        info="Energy transfer started",
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=1,
        status="SuspendedEV",
        error_code="NoError",
        info="EV requested pause",
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=1,
        status="Finishing",
        error_code="NoError",
        info="Transaction completed",
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp, connector_id=1, status="Available", error_code="NoError"
    )

    # Test error conditions
    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=2,
        status="Faulted",
        error_code="OverCurrentFailure",
        info="Overcurrent detected on connector 2",
        vendor_id="MockVendor",
        vendor_error_code="ERR_001",
    )

    await asyncio.sleep(1)
    await send_status_notification(
        cp,
        connector_id=2,
        status="Unavailable",
        error_code="InternalError",
        info="Connector disabled for maintenance",
    )


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
    """Send StartTransaction request."""
    print(f"\n🔋 Sending StartTransaction...")
    print(f"  ID Tag: {tag}")
    print(f"  Connector: {connector_id}")
    print(f"  Meter Start: {meter_start} Wh")

    try:
        request = call.StartTransaction(
            connector_id=connector_id,
            id_tag=tag,
            meter_start=meter_start,
            timestamp=utc_now_iso(),
        )
        response = await cp.call(request)

        print(f"  Response: {response.id_tag_info['status']}")
        if hasattr(response, "transaction_id"):
            print(f"  Transaction ID: {response.transaction_id}")
            return response.transaction_id
        else:
            print("  No transaction ID returned")
            return None

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


async def send_meter_values(cp, connector_id, transaction_id=None):
    """Send MeterValues request with sample energy readings."""
    print(f"\n⚡ Sending MeterValues...")
    print(f"  Connector: {connector_id}")
    print(f"  Transaction: {transaction_id if transaction_id else 'None'}")

    try:
        # Create sample meter values
        meter_values = [
            {
                "timestamp": utc_now_iso(),
                "sampledValue": [
                    {
                        "value": "15420",  # 15.42 kWh
                        "context": "Sample.Periodic",
                        "format": "Raw",
                        "measurand": "Energy.Active.Import.Register",
                        "location": "Outlet",
                        "unit": "Wh",
                    },
                    {
                        "value": "16.5",  # 16.5 Amps
                        "context": "Sample.Periodic",
                        "format": "Raw",
                        "measurand": "Current.Import",
                        "location": "Outlet",
                        "unit": "A",
                        "phase": "L1",
                    },
                ],
            },
            {
                "timestamp": (
                    datetime.now(timezone.utc) + timedelta(seconds=30)
                ).isoformat(),
                "sampledValue": [
                    {
                        "value": "15890",  # 15.89 kWh (470 Wh increase)
                        "context": "Sample.Periodic",
                        "format": "Raw",
                        "measurand": "Energy.Active.Import.Register",
                        "location": "Outlet",
                        "unit": "Wh",
                    }
                ],
            },
        ]

        request_params = {
            "connector_id": connector_id,
            "meter_value": meter_values,
        }

        # Add transaction_id if provided
        if transaction_id:
            request_params["transaction_id"] = transaction_id

        request = call.MeterValues(**request_params)
        response = await cp.call(request)

        print(f"  ✅ MeterValues sent successfully")
        print(f"  Energy reading: 15.42 kWh → 15.89 kWh")
        print(f"  Current: 16.5A")

    except Exception as e:
        print(f"  ❌ Error: {e}")


async def send_stop_transaction(
    cp, transaction_id, meter_stop, reason, id_tag=None, include_transaction_data=False
):
    """Send StopTransaction request."""
    print(f"\n🛑 Sending StopTransaction...")
    print(f"  Transaction ID: {transaction_id}")
    print(f"  Meter Stop: {meter_stop} Wh")
    print(f"  Reason: {reason}")
    if id_tag:
        print(f"  ID Tag: {id_tag}")

    try:
        request_params = {
            "transaction_id": transaction_id,
            "meter_stop": meter_stop,
            "timestamp": utc_now_iso(),
            "reason": reason,
        }

        # Add optional ID tag
        if id_tag:
            request_params["id_tag"] = id_tag

        # Add transaction data if requested
        if include_transaction_data:
            request_params["transaction_data"] = [
                {
                    "timestamp": utc_now_iso(),
                    "sampledValue": [
                        {
                            "value": str(meter_stop),
                            "context": "Transaction.End",
                            "format": "Raw",
                            "measurand": "Energy.Active.Import.Register",
                            "location": "Outlet",
                            "unit": "Wh",
                        }
                    ],
                }
            ]

        request = call.StopTransaction(**request_params)
        response = await cp.call(request)

        print(f"  ✅ StopTransaction sent successfully")
        if hasattr(response, "id_tag_info") and response.id_tag_info:
            print(f"  ID Tag Status: {response.id_tag_info['status']}")

    except Exception as e:
        print(f"  ❌ Error: {e}")


async def send_status_notification(
    cp,
    connector_id,
    status,
    error_code,
    info=None,
    vendor_id=None,
    vendor_error_code=None,
):
    """Send StatusNotification request."""
    print(f"\n📊 Sending StatusNotification...")
    print(f"  Connector: {connector_id}")
    print(f"  Status: {status}")
    print(f"  Error Code: {error_code}")
    if info:
        print(f"  Info: {info}")

    try:
        request_params = {
            "connector_id": connector_id,
            "error_code": error_code,
            "status": status,
            "timestamp": utc_now_iso(),
        }

        # Add optional fields
        if info:
            request_params["info"] = info
        if vendor_id:
            request_params["vendor_id"] = vendor_id
        if vendor_error_code:
            request_params["vendor_error_code"] = vendor_error_code

        request = call.StatusNotification(**request_params)
        response = await cp.call(request)

        print(f"  ✅ StatusNotification sent successfully")

    except Exception as e:
        print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
