from attrs import define, field, validators as vd
import websockets.exceptions as wse
import coloredlogs
import websockets
import asyncio
import logging
import json
import sys

from .ProtocolState import ProtocolState


@define
class WebSocket:
    LOG = logging.getLogger("Kuzzle-WebSocket")
    state: ProtocolState = field(init=False, default=ProtocolState.CLOSE)
    event_loop: object = field(init=False, default=None)
    ws: any = field(init=False, default=None)
    __retry: int = field(init=False, default=0)

    __host: str = field()
    __port: int = field(default=7512, validator=vd.instance_of(int))
    __isSsl: bool = field(default=False, validator=vd.instance_of(bool))
    __autoReconnect: bool = field(default=True, validator=vd.instance_of(bool))
    __reconnectionDelay: int = field(default=1000, validator=vd.instance_of(int))
    __reconnectionRetries: int = field(default=60, validator=vd.instance_of(int))

    def __attrs_post_init__(self):
        coloredlogs.install(logger=WebSocket.LOG, fmt="[%(thread)X] - %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG, stream=sys.stdout)

    async def __connect_task(self) -> None:
        self.LOG.debug("<Connecting.... url = %s>", self.url)
        try:
            self.ws = await websockets.connect(self.url)
            self.state = ProtocolState.OPEN
        except Exception as e:
            self.state = ProtocolState.CLOSE
            self.LOG.critical(e)
            return
        self.LOG.info("<Connected to %s>", self.url)
        self.event_loop.create_task(self.__run_loop_task())

    async def __run_loop_task(self) -> None:
        while True:
            self.LOG.debug("<<Waiting for data from Kuzzle...>>")
            try:
                resp = await asyncio.wait_for(self.ws.recv(), timeout=60)
                self.LOG.debug("<<Received data from Kuzzle>>")
            except wse.ConnectionClosed as e:
                self.LOG.error("__publish_state_task: ws disconnection: %s", str(e))
                self.__retry += 1
                if not self.__autoReconnect or self.__retry > self.__reconnectionRetries:
                    return
                self.LOG.info(f"reconnecting in {self.__reconnectionDelay}ms...")
                await asyncio.sleep(self.__reconnectionDelay / 1000)
                try:
                    self.ws = await websockets.connect(self.url)
                    self.LOG.debug("Re subscribing to own state...")
                    self.state = ProtocolState.OPEN
                except Exception as e:
                    self.LOG.critical(e)
                continue
            except asyncio.TimeoutError:
                try:
                    self.LOG.info("PING Kuzzle")
                    pong_waiter = await self.ws.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                    self.LOG.info("PONG Kuzzle")
                except asyncio.TimeoutError:
                    self.LOG.critical("No PONG from Kuzzle")
                    break
                continue
            except Exception as e:
                self.LOG.error("__publish_state_task: ws except: %s", str(e))
            if not resp:
                continue
            self.LOG.debug("<<Received data from Kuzzle...>>")
            print(resp)

    async def __post_query_task(self, query: dict, parent: str) -> None:
        self.LOG.debug(f"<<{parent}: Posting query>>")
        await self.ws.send(json.dumps(query))
        self.LOG.debug(f"<<{parent}: Query posted>>")

    def subscribe_realtime(self, index: str, collection: str):
        query = {"action": "subscribe", "index": index, "collection": collection, "controller": "realtime", "query": {"match_all": {}}}
        return self.event_loop.create_task(self.__post_query_task(query, "subscribe_realtime"))

    def post_query(self, query: dict):
        self.LOG.debug("<<Adding task to post a query>>")
        return self.event_loop.create_task(self.__post_query_task(query, "post_query"))

    def connect(self) -> any:
        if self.state == ProtocolState.OPEN:
            self.LOG.warning("<Already connected>")
            return
        self.event_loop = asyncio.get_event_loop()
        assert self.event_loop, "No event loop found"
        return self.event_loop.create_task(self.__connect_task())

    def disconnect(self):
        self.LOG.debug("<<Disconnecting>>")
        self.ws.close()
        self.state = ProtocolState.CLOSE
        self.LOG.debug("<<Disconnected>>")

    @property
    def url(self) -> str:
        return f"{['ws','wss'][self.__isSsl]}://{self.__host}:{self.__port}"