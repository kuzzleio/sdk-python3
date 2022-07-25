import asyncio
import inspect
import sys
import os

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from sdkPython import WebSocket


async def main():
    websockets = WebSocket("localhost")
    await websockets.connect()
    await websockets.post_query({"controller": "index", "action": "create", "body": {}, "index": "from_python"})


asyncio.run(main())
