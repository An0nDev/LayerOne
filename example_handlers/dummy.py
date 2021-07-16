from LayerOne.extra.handler import Host, PrintFunc, SendFunc, Handler
from LayerOne.extra.mojang_client_auth import auth_from_file
from LayerOne.network.server.proxy import Proxy

class DummyHandler (Handler):
    def __init__ (self, client_address: Host):
        print ("connected")
    def ready (self):
        print ("ready")
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        print_func ("client to server")
        return True
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        print_func ("server to client")
        return True
    def disconnected (self):
        print ("disconnected")

if __name__ == "__main__":
    Proxy (quiet = False, host = ("0.0.0.0", 25567), target = ("localhost", 25569), auth = auth_from_file ("../auth.json"), handler_class = DummyHandler)