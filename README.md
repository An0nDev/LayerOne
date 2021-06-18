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

e.g. `python3 auth.json 0.0.0.0:25567 localhost:25566` will use `auth.json` in the current directory to forward connections on all interfaces port 25567 to a minecraft server running on localhost port 25566.
### intercepting/crafting play packets
(packets by default are printed to the console if < 100 bytes with the current connection state and packet id, modifying or creating new ones are todo)
## credits
https://wiki.vg for all protocol information, most from https://wiki.vg/index.php?title=Protocol&oldid=7368

python `requests` and `cryptography` libraries to handle http requests and encryption

many stdlib components, namely zlib for compression