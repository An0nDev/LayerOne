import abc
from typing import Tuple, Callable

Host = Tuple [str, int] # IP, port
PrintFunc = Callable [..., None]
SendFunc = Callable [[int, bytes], None]

class Handler (abc.ABC):
    @abc.abstractmethod
    def __init__ (self, client_address: Host): pass
    @abc.abstractmethod
    def ready (self): pass
    @abc.abstractmethod
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool: return True
    @abc.abstractmethod
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool: return True
    @abc.abstractmethod
    def disconnected (self): pass