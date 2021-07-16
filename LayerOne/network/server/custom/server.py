import socket
import traceback
from threading import Lock, RLock

import colorama

from LayerOne.network.server.custom.client import Client
from LayerOne.network.server.custom.common import Host
from LayerOne.network.server.custom.handler import Handler

class Server:
    def __init__ (self, host: Host, initial_storage: dict, handler_class: type (Handler), quiet: bool = False):
        self.quiet = quiet
        if not quiet: colorama.init ()

        self.initial_storage = initial_storage
        self.handler_class = handler_class

        server = socket.socket (family = socket.AF_INET, type = socket.SOCK_STREAM)
        server.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind (host)
        server.listen ()

        self.runtime_storage_lock = Lock ()
        self.runtime_storage = {}
        
        self.clients_lock = RLock ()
        self.clients = []

        is_first_client = True
        while True:
            try:
                native_client_connection, client_address = server.accept ()
                with self.clients_lock:
                    self.clients.append (Client (self, native_client_connection, client_address, is_first_client))
                if is_first_client: is_first_client = False
            except KeyboardInterrupt: break

        with self.clients_lock:
            while len (self.clients) > 0:
                self.disconnect_client (0)

        if not quiet: colorama.deinit ()
    def disconnect_client (self, client_index: int): # NOTE: CALLER MUST ACQUIRE clients_lock FIRST!
        with self.clients_lock:
            target = self.clients [client_index]
            target.disconnecting = True
            target.connection.ensure_closed ()
            target.handler.disconnected (True)
            if not target.disconnecting_from_inner: target.receive_thread.join ()
            self.clients.pop (client_index)
