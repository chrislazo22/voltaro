import asyncio
import websockets
from ocpp.v16 import call
from ocpp.v16 import ChargePoint as ChargePointV16

class MockChargePoint(ChargePointV16):
    async def start(self):
        # Send BootNotification to server
        request = call.BootNotification(
            charge_point_model="Model X",
            charge_point_vendor="Voltaro Inc."
        )
        response = await self.call(request)

        print(f"BootNotification response: {response.status}, interval: {response.interval}")

async def main():
    uri = "ws://localhost:9000/CP001"
    async with websockets.connect(uri, subprotocols=["ocpp1.6"]) as websocket:
        print(f"Connected to {uri} with protocol: {websocket.subprotocol}")

        cp = MockChargePoint("CP001", websocket)
        await cp.start()

if __name__ == "__main__":
    asyncio.run(main())
