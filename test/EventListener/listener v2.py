import websockets
import asyncio
import json

URI = "ws://localhost:7512"
TIMEOUT = 120


class c:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class EventListener:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.msg = None

    async def run(self):
        await self.loop.create_task(self.create_ws())
        print("Connected")
        await self.loop.create_task(self.ws.send(json.dumps({"action": "subscribe", "index": "index_test", "collection": "collect_test", "controller": "realtime", "body": {}})))
        self.loop.create_task(self.recv())

    async def recv(self):
        while True:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=20)
                self.msg = json.loads(message)
                print(f"\x1b[33m[ℹ️] New notification triggered by API action \"{self.msg['controller']}:{self.msg['action']}\"\x1b[0m")
                print(json.dumps(self.msg["result"], indent=4, sort_keys=True, ensure_ascii=False))
            except asyncio.TimeoutError:
                continue

    async def create_ws(self):
        self.ws = await websockets.connect(URI)


async def main():
    listener = EventListener()
    await listener.run()
    while True:
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
