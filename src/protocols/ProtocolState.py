from enum import Enum


class ProtocolState(Enum):
    CLOSE: int = 0
    OPEN: int = 1
    RECONNECTING: int = 2
