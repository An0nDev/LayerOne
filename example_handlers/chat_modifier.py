from LayerOne.extra.handler import PrintFunc, SendFunc, Handler
from LayerOne.network.packet import Packet
from LayerOne.types.string import String

class ChatModifierHandler (Handler):
    def connected (self): pass
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        if packet_id == 0x01: # Chat Message
            chat_message: str = Packet.decode_fields (packet_data, (String,)) [0]
            if chat_message.startswith ("/"): return True # pass through commands
            chat_message = "SUBSCRIBE TO TECHNOBLADEEEEEEEEee"
            out_data = Packet.encode_fields ((chat_message, String))
            to_server_func (0x01, out_data) # send modified chat message
            print_func ("hacked outgoing chat message")
            return False # don't pass through hacked chat message
        return True # pass through other c2s packets
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        return True # pass through unmodified
    def disconnected (self): pass