from LayerOne.extra.handler import PrintFunc, SendFunc, Handler

class DummyHandler (Handler):
    def connected (self):
        print ("connected")
        return
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        print_func ("client to server")
        return True
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        print_func ("server to client")
        return True
    def disconnected (self):
        print ("disconnected")
        return