import abc
from typing import Optional

class Handler (abc.ABC):
    @abc.abstractmethod
    def __init__ (self, client, is_first: bool): pass
    @abc.abstractmethod
    def packet_received (self, packet_id: int, packet_data: bytes) -> Optional [bool]: pass
    @abc.abstractmethod
    def disconnected (self, initiated_by_server: bool): pass