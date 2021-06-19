import abc
from typing import Callable

PrintFunc = Callable [..., None]
SendFunc = Callable [[int, bytes], None]

class Handler (abc.ABC):
    @abc.abstractmethod
    def connected (self):
        return
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        return True
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        return True
    def disconnected (self):
        return