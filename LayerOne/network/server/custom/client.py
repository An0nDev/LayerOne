import socket
import traceback
from threading import Thread

import colorama

from LayerOne.network.server.custom.common import Host
from LayerOne.network.conn_wrapper import ConnectionWrapper
from LayerOne.network.packet import Packet
from LayerOne.network.utils import Utils
from LayerOne.types.varint import VarInt

class Client:
    def __init__ (self, server, native_connection: socket.socket, address: Host, is_first: bool):
        self.server = server

        self.connection = ConnectionWrapper (native_connection)
        self.address = address

        self.handler = server.handler_class (self, is_first)

        self.disconnecting = False
        self.disconnecting_from_inner = False

        self.compression_threshold = -1

        self.receive_thread = Thread (target = self._receive_loop)
        self.receive_thread.start ()
    def enable_compression (self, compression_threshold: int): # Should only be called in Login state (prior to sending Login Success)
        self.send (0x03, Packet.encode_fields ((compression_threshold, VarInt))) # Enable Compression
        self.compression_threshold = compression_threshold
    def send (self, _packet_id: int, _data: bytes):
        Packet.write (self.connection, _packet_id, _data, compression_threshold = self.compression_threshold)
    def _receive_loop (self):
        def meta_print (message, **kwargs):
            if not self.server.quiet: print (f"{colorama.Style.BRIGHT}{message}{colorama.Style.RESET_ALL}", **kwargs)

        meta_print (f"connected, ip {self.address [0]} port {self.address [1]}")

        disconnect_initiated_by_handler = False

        while True:
            try:
                packet_id, packet_data = Packet.read (self.connection, compression_threshold = self.compression_threshold)
                meta_print (f"id 0x{'{0:x}'.format (packet_id).zfill (2)} data {Utils.buffer_to_str (packet_data)}")

                should_disconnect = self.handler.packet_received (packet_id, packet_data)
                if should_disconnect is not None and should_disconnect:
                    disconnect_initiated_by_handler = True
                    break
            except EOFError:
                meta_print ("eof")
                break
            except ConnectionResetError:
                meta_print ("reset")
                break
            except BrokenPipeError:
                meta_print ("broken pipe")
                break
            except Exception as exception:
                meta_print (f"other error: {repr (exception)}")
                meta_print (traceback.format_exc (), end = "")
                break
        if not self.disconnecting:
            self.disconnecting_from_inner = True
            if disconnect_initiated_by_handler: meta_print ("disconnect initiated by handler")
            with self.server.clients_lock:
                self_index = self.server.clients.index (self)
                self.server.disconnect_client (self_index)
        else:
            meta_print ("disconnect initiated internally by server or other client")