import importlib
import json
import sys

from LayerOne.extra.mojang_client_auth import auth
from LayerOne.network.server import Server

auth_file_path = sys.argv [1]
with open (auth_file_path, "r") as auth_file:
    auth_json = json.load (auth_file)

proxy_auth = auth ( # NOTE: Only Mojang accounts are currently supported, but I can add Microsoft account support; open an issue.
    auth_json ["email"], # Account email
    auth_json ["password"], # Account password
    auth_json ["client_token"] # Should be a unique string, like "487c8d0040774f6b84af38831801a867" from uuid.uuid4 ().hex. Invalidates all access tokens if changed
) # This is necessary since part of the encryption process mandates you send a request to Mojang's session server, which servers will then check for.
# Since the encryption is handled as part of the proxy rather than being passed through, we need to have an access token to provide as part of the request.

def parse_host (_host) -> (str, int):
    partitioned = _host.rpartition (':') # "host:with:colons:port" --> ["host:with:colons", ':', "port"]
    return partitioned [0], int (partitioned [2])

def parse_handler_class (_handler) -> type:
    partitioned = _handler.rpartition (':')
    module = importlib.import_module (partitioned [0])
    _class = module.__getattribute__ (partitioned [2])
    return _class

host = parse_host (sys.argv [2])
proxy_target = parse_host (sys.argv [3])
handler_class = parse_handler_class (sys.argv [4]) if len (sys.argv) >= 5 else None
Server (quiet = handler_class is not None, host = host, proxy = True, proxy_target = proxy_target, proxy_auth = proxy_auth, handler_class = handler_class)
