import json
from typing import Optional

from LayerOne.extra.custom_handler import Host, SendFunc, CustomHandler
from LayerOne.network.packet import Packet
from LayerOne.network.server.custom import Custom
from LayerOne.types.common import ProtocolException
from LayerOne.types.native import UShort
from LayerOne.types.string import String
from LayerOne.types.varint import VarInt

class ServerListPing (CustomHandler):
    def __init__ (self, client_address: Host):
        self.packet_number = 0
        self.in_status = False
    def packet_received (self, to_client_func: SendFunc, packet_id: int, packet_data: bytes) -> Optional [bool]:
        # this is a really badly written example that doesn't follow the protocol state machine
        # but it works as a test and i want to move onto the next task
        if self.packet_number == 0:
            # handshake
            assert packet_id == 0, f"packet {self.packet_number} is not handshake reeeeeeeeee"
            handshake = Packet.decode_fields (packet_data, (VarInt, String, UShort, VarInt))
            print (f"handshake, client protocol version {handshake [0]}")
            next_state = handshake [3]
            if next_state == 1:
                self.in_status = True
                print ("switched state to status")
            else:
                print ("login not implemented")
                return True
        elif self.packet_number == 1:
            if self.in_status:
                # request packet
                if packet_id != 0: raise ProtocolException (f"second packet {self.packet_number} is not status request")
                response_json = {
                    "version": {
                        "name": "1.8.9",
                        "protocol": 47
                    },
                    "players": {
                        "max": 420,
                        "online": 69,
                        "sample": []
                    },
                    "description": {
                        "text": "Server list ping test"
                    }
                }
                response_data = Packet.encode_fields ((json.dumps (response_json), String))
                to_client_func (0x00, response_data)
                print ("sent response to status request")
        else:
            if self.in_status:
                # ping packet
                if packet_id != 1: raise ProtocolException (f">= third packet {self.packet_number} is not ping")
                to_client_func (0x01, packet_data)
                print ("sent pong to ping")
        self.packet_number += 1
    def disconnected (self, initiated_by_server: bool): pass

if __name__ == "__main__":
    Custom (quiet = False, host = ("0.0.0.0", 25568), handler_class = ServerListPing)