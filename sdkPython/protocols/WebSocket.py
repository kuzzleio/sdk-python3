from attrs import define, field, validators as vd
from asyncio import AbstractEventLoop
from requests import request

import websockets.exceptions as wse
import coloredlogs
import websockets
import asyncio
import logging
import uuid
import json
import sys

from .ProtocolState import ProtocolState


@define
class WebSocket:
    LOG = logging.getLogger("Kuzzle-WebSocket")

    __request_callbacks: dict = field(init=False, default=dict())
    state: ProtocolState = field(init=False, default=ProtocolState.CLOSE)
    event_loop: AbstractEventLoop = field(init=False, default=None)
    ws: any = field(init=False, default=None)
    __retry: int = field(init=False, default=0)
    __timeout: float = field(init=False, default=60)

    __host: str = field()
    __port: int = field(default=7512, validator=vd.instance_of(int))
    __isSsl: bool = field(default=False, validator=vd.instance_of(bool))
    __autoReconnect: bool = field(default=True, validator=vd.instance_of(bool))
    __reconnectionDelay: int = field(default=1000, validator=vd.instance_of(int))
    __reconnectionRetries: int = field(default=60, validator=vd.instance_of(int))

    def __attrs_post_init__(self):
        coloredlogs.install(logger=WebSocket.LOG, fmt="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.DEBUG, stream=sys.stdout)
        self.LOG.disabled = True

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
        self.LOG.debug("<<Listener is launched ...>>")
        while True:
            resp_str: str = ""
            resp_json: dict = {}
            try:
                resp_str = await asyncio.wait_for(self.ws.recv(), timeout=self.__timeout)
                resp_json = json.loads(resp_str)
                self.LOG.debug("<<Received data from Kuzzle>>")
            except wse.ConnectionClosed as e:
                self.state = ProtocolState.RECONNECTING
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
                    self.state = ProtocolState.CLOSE
                continue
            except asyncio.TimeoutError:
                try:
                    pong_waiter = await self.ws.ping()
                    await asyncio.wait_for(pong_waiter, timeout=self.__timeout)
                except asyncio.TimeoutError:
                    self.LOG.critical("No PONG from Kuzzle")
                    break
                continue
            except Exception as e:
                self.LOG.error("__publish_state_task: ws except: %s", str(e))
            self.LOG.info(f"\x1b[{'31' if resp_json.get('error', None) else '33'}m[ℹ️] New notification triggered by API action \"{resp_json['controller']}:{resp_json['action']}\"\x1b[0m")
            if not self.LOG.disabled:
                print(json.dumps(resp_json["result"] or resp_json["error"], indent=4, sort_keys=True, ensure_ascii=False))
            if self.__request_callbacks.get(resp_json["requestId"], None):
                self.__request_callbacks.pop(resp_json["requestId"])(resp_json)

    async def __post_query_task(self, query: dict, parent: str, callback: callable = None) -> None:
        if self.state != ProtocolState.OPEN:
            self.LOG.error("<Not connected>")
            return
        query["requestId"] = str(uuid.uuid4())
        if callable(callback):
            self.__request_callbacks[query["requestId"]] = callback
        await self.ws.send(json.dumps(query))
        self.LOG.debug(f"<<{parent}: Query posted>>")

    def subscribe_realtime(self, index: str, collection: str, body: dict = None, callback: callable = None) -> any:
        query: dict = {"action": "subscribe", "index": index, "collection": collection, "controller": "realtime", "body": body or {}}
        return self.event_loop.create_task(self.__post_query_task(query, "subscribe_realtime", callback))

    def unsubscribe_realtime(self, room_id: int, callback: callable = None) -> any:
        query: dict = {"action": "unsubscribe", "controller": "realtime", "body": {"roomId": room_id}}
        return self.event_loop.create_task(self.__post_query_task(query, "unsubscribe_realtime", callback))

    def publish_realtime(self, index: str, collection: str, body: dict = None, callback: callable = None) -> any:
        query: dict = {"action": "publish", "index": index, "collection": collection, "controller": "realtime", "body": body or {}}
        return self.event_loop.create_task(self.__post_query_task(query, "publish_realtime", callback))

    def post_query(self, query: dict, callback: callable = None):
        return self.event_loop.create_task(self.__post_query_task(query, "post_query", callback))

    def connect(self) -> any:
        if self.state == ProtocolState.OPEN:
            self.LOG.warning("<Already connected>")
            return
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.set_debug(True)
        assert self.event_loop, "No event loop found"
        return self.event_loop.create_task(self.__connect_task())

    def disconnect(self) -> None:
        self.LOG.debug("<<Disconnecting...>>")
        self.ws.close()
        self.state = ProtocolState.CLOSE
        self.LOG.debug("<<Disconnected>>")

    def debug(self, state: bool) -> None:
        self.LOG.disabled = not state

    def status(self) -> str:
        return self.state.name

    @property
    def url(self) -> str:
        return f"{['ws','wss'][self.__isSsl]}://{self.__host}:{self.__port}"
