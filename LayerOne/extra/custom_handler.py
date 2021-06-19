import abc
from typing import Optional

from LayerOne.extra.handler import Host, SendFunc

class CustomHandler (abc.ABC):
    @abc.abstractmethod
    def __init__ (self, client_address: Host): pass
    @abc.abstractmethod
    def packet_received (self, to_client_func: SendFunc, packet_id: int, packet_data: bytes) -> Optional [bool]: pass
    @abc.abstractmethod
    def disconnected (self, initiated_by_server: bool): pass