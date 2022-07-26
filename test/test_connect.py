import asyncio
import inspect
import sys
import os

currentdir: str = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir: str = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from sdkPython import WebSocket


async def main():
    websockets: WebSocket = WebSocket("localhost")
    await websockets.connect()
    websockets.subscribe_realtime("from_python_1", "perso")
    websockets.post_query({"index": "from_python_1", "collection": "perso", "controller": "document", "action": "create", "body": {"name": "test", "age": "test"}})


asyncio.run(main())
