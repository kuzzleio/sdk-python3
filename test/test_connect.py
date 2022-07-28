import asyncstdlib as a
import asyncio
import inspect
import json
import sys
import os

currentdir: str = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir: str = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from sdkPython import WebSocket


async def unsubscribe(data: dict, roomId: str, websockets: WebSocket):
    await websockets.unsubscribe_realtime(roomId)


async def publish(data: dict, websockets: WebSocket):
    await websockets.publish_realtime("index_test", "collect_test", {"test": "test"}, callback=lambda answ: asyncio.ensure_future(unsubscribe(answ, data["result"]["roomId"], websockets)))


async def main():
    websockets: WebSocket = WebSocket("localhost")
    websockets.debug(True)
    await websockets.connect()
    await websockets.subscribe_realtime("index_test", "collect_test", callback=lambda answ: asyncio.ensure_future(publish(answ, websockets)))
    # websockets.post_query({"index": "index_test", "collection": "collect_test", "controller": "document", "action": "create", "body": {"age": "23", "name": "John"}})
    while True:
        await asyncio.sleep(0.1)


asyncio.run(main())
