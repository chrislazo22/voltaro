import asyncio
import websockets

async def main():
    uri = "ws://localhost:9000/CP001"  # CP001 is a sample charge point id
    try:
        async with websockets.connect(
            uri,
            subprotocols=["ocpp1.6"]
        ) as websocket:
            print(f"Connected to {uri} with protocol: {websocket.subprotocol}")
            # Optionally, keep the connection open for a few seconds
            await asyncio.sleep(2)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
