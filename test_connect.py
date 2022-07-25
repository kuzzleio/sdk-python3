import websockets
from src import WebSocket
import asyncio


async def main():
    websockets = WebSocket("localhost")
    await websockets.connect()
    await websockets.post_query({"controller": "index", "action": "create", "body": {}, "index": "from_python"})


asyncio.run(main())
