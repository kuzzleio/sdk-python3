import websockets
import asyncio
import json

URI = "ws://localhost:7512"
TIMEOUT = 120


async def create_ws():
    return await websockets.connect(URI)


async def receive_message():
    ws = await create_ws()
    print("Connected")
    await ws.send(json.dumps({"action": "subscribe", "index": "index_test", "collection": "collect_test", "controller": "realtime", "body": {}}))
    while True:
        message = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
        print(json.dumps(json.loads(message), indent=4))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(receive_message())
