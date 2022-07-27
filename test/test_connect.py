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
    websockets.subscribe_realtime("index_test", "collect_test")
    websockets.post_query({"index": "index_test", "collection": "collect_test", "controller": "document", "action": "create", "body": {"age": "23", "name": "John"}})
    while True:
        await asyncio.sleep(.1)


asyncio.run(main())
