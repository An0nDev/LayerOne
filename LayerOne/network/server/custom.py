import socket
import traceback
from threading import Thread
from typing import Tuple

import colorama

from LayerOne.extra.custom_handler import CustomHandler
from LayerOne.network.conn_wrapper import ConnectionWrapper
from LayerOne.network.packet import Packet
from LayerOne.network.utils import Utils

Host = Tuple [str, int] # IP, port

class Custom:
    def __init__ (self, host: Host, handler_class: type (CustomHandler), quiet: bool = False):
        self.quiet = quiet
        if not quiet: colorama.init ()

        self.handler_class = handler_class

        server = socket.socket (family = socket.AF_INET, type = socket.SOCK_STREAM)
        server.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind (host)
        server.listen ()

        while True:
            native_client_connection, client_address = server.accept ()
            Thread (target = self.handler_serverbound, args = (native_client_connection, client_address)).start ()
    def handler_serverbound (self, native_client_connection: socket.socket, client_address: Host):
        def meta_print (message, **kwargs):
            if not self.quiet: print (f"{colorama.Style.BRIGHT}{message}{colorama.Style.RESET_ALL}", **kwargs)

        meta_print (f"connected, ip {client_address [0]} port {client_address [1]}")

        handler_instance: CustomHandler = self.handler_class (client_address)

        client_connection = ConnectionWrapper (native_client_connection)

        def to_client (_packet_id, _data):
            Packet.write (client_connection, _packet_id, _data)

        disconnect_initiated_by_server = False

        while True:
            try:
                packet_id, packet_data = Packet.read (client_connection)
                meta_print (f"id 0x{'{0:x}'.format (packet_id).zfill (2)} data {Utils.buffer_to_str (packet_data)}")

                should_disconnect = handler_instance.packet_received (to_client, packet_id, packet_data)
                if should_disconnect is not None and should_disconnect:
                    disconnect_initiated_by_server = True
                    break
            except EOFError:
                meta_print ("eof")
                break
            except ConnectionResetError:
                meta_print ("reset")
                break
            except BrokenPipeError:
                meta_print ("broken pipe (exception in other direction?)")
                break
            except Exception as exception:
                meta_print (f"other error: {repr (exception)}")
                meta_print (traceback.format_exc (), end = "")
                break
        client_connection.ensure_closed ()
        handler_instance.disconnected (disconnect_initiated_by_server)
        if not self.quiet: colorama.deinit ()
