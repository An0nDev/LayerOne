# LayerOne

transparent minecraft man-in-the-middle proxy targeting mc 1.8.9 (**unlikely to work consistently with other minecraft versions**)

tested on Python 3.8

dependencies are `requests` and `cryptography` (`pip3 install requests cryptography`) if you want to do encrypted passthrough (default for the notchian server)

## setup
### adding your credentials
Make a file called `auth.json` with the following contents:
```json
{
  "email": "your_mojang_account@email.com",
  "password": "supersecure",
  "client_token": "487c8d0040774f6b84af38831801a867"
}
```
To get a `client_token`, copy your local launcher's token from `~/.minecraft/launcher_accounts.json` (`mojangClientToken`) to use the proxy while staying signed in, or run `python3 gen_token.py`, which may sign you out from your launcher.

Your credentials are necessary since part of the encryption process mandates the client sends a request to Mojang's session server, which servers will then check for.

Since the encryption is handled as part of the proxy rather than being passed through (thus allowing the proxy to read and write encrypted packets), we need to have an access token to provide as part of the request.
## usage
### running the proxy
`python3 main.py path_to_auth_json host proxy_target` where:
- `path_to_auth_json` is the path relative to the current directory where `auth.json` is stored
- both `host` and `proxy_target` are in the format `ip:port`
- `host` is the host the proxy will **run on**
- `proxy_target` is the host the proxy will **connect to**

e.g. `python3 main.py auth.json 0.0.0.0:25567 localhost:25566` will use `auth.json` in the current directory to forward connections on all interfaces port 25567 to a minecraft server running on localhost port 25566.
### intercepting/crafting play packets
if run like ^, packet information will be printed to the console.

to implement custom behavior when a play packet is received from the client or server, subclass `LayerOne.extra.handler.Handler` with a class such as this one (`ChatModifierHandler` from `example_handlers/chat_modifier.py`):
```python
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
```
`connected` and `disconnected` are called when a (non-server-list-ping) client completes login and disconnects, respectively. They accept no arguments and the return value is discarded.
(They're mainly meant for handlers to do any startup/cleanup necessary; `disconnected` is guaranteed to be called unless the process is killed.)

`client_to_server` and `server_to_client` are called when a packet is sent from the client to the server and from the server to the client, respectively, with the following caveats:
- `current_state: dict` contains information about the current state of the protocol, such as `["id"]` representing the value of the notchian state enum (0 = handshaking, 1 = status, 2 = login, 3 = play)
- `print_func: PrintFunc` is a function that prints the sole argument as a string with fancy formatting, depending on which direction the function is called from.
In addition to a single positional argument which `str` is called on to form the body of the message, it accepts keyword arguments `generic: bool = False` (avoid appending extra packet info?) and `meta: bool = False` (if `generic`, add extra emphasis?).
- `to_client_func: SendFunc, to_server_func: SendFunc` are functions that send a packet with the given positional packet ID (`int`) and data (`bytes`) in the direction indicated by the variable name, handling any necessary compression and/or encryption.
- `packet_id` is the packet ID (`int`) of the incoming packet. See the wiki.vg page below to understand how to interpret this; serverbound and clientbound directions have separate sets of IDs, and the connection state will always be 3 aka Play.
- `packet_data` is the data contained in the incoming packet. `Packet.decode_fields` and `Packet.encode_fields` provide interoperability with Python types and types in protocol format.
- The return value, a `bool`, indicates whether the packet should be passed through unmodified to the other side. Returning `True` is helpful in `else` blocks if you want special behavior to occur only for specific packets.

Note the example usages of `Packet.decode_fields` and `Packet.encode_fields` based on wiki.vg's description of the serverbound Chat Message packet (id `0x01`, single `String` field containing the raw message text)

To start the server with a custom handler class, add another argument with the form `package.path:ClassName`:
- `package.path` is the path to the `.py` file containing the class implementation, in Python `import` format.
- `ClassName` is the name of the class.

ex. `python3 main.py auth.json 0.0.0.0:25567 localhost:25566 example_handlers.chat_modifier:ChatModifierHandler` will use the `ChatModifierHandler` class from `example_handlers/chat_modifier.py`.

Good luck and happy MITM'ing! If you make a cool handler, open an issue with a link to the source code, and I'll add it to this list of cool handlers:
- [`ChatModifierHandler` by An0nDev](https://github.com/An0nDev/LayerOne/blob/master/example_handlers/chat_modifier.py): replaces all outgoing global chat messages with the text "SUBSCRIBE TO TECHNOBLADEEEEEEEEee" 
## credits
https://wiki.vg for all protocol information, most from https://wiki.vg/index.php?title=Protocol&oldid=7368

python `requests` and `cryptography` libraries to handle http requests and encryption

many stdlib components, namely zlib for compression