import json

from LayerOne.extra.handler import Host, PrintFunc, SendFunc, Handler
from LayerOne.network.packet import Packet
from LayerOne.types.native import Byte
from LayerOne.types.string import String

class SpecialMenu (Handler):
    def __init__ (self, client_address: Host): pass
    def ready (self): pass
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        if packet_id == 0x01: # Chat Message
            chat_message: str = Packet.decode_fields (packet_data, (String,)) [0]
            if not chat_message.startswith ("."): return True
            command = chat_message [len ('.'):]
            chat_message = json.dumps ({"text": f"Proxy received special command {command}"})
            out_data = Packet.encode_fields ((chat_message, String), (0x02, Byte))
            to_client_func (0x02, out_data) # send modified chat message
            print_func (f"received special command {command}")
            return False # don't pass through hacked chat message
        return True # pass through other c2s packets
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        return True # pass through unmodified
    def disconnected (self): pass