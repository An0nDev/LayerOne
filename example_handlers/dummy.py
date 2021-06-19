from LayerOne.extra.handler import Host, PrintFunc, SendFunc, Handler

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