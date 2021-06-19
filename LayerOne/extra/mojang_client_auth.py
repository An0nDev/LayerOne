import json

import requests

_auth_server = "https://authserver.mojang.com"
def _make_request (endpoint: str, data: dict) -> dict:
    response = requests.post (f"{_auth_server}{endpoint}", headers = {"Content-Type": "application/json"}, data = json.dumps (data))
    response.raise_for_status ()
    return response.json ()

def authenticate (username: str, password: str, client_token: str) -> (str, str): # UUID, access token
    auth_response = _make_request ("/authenticate", {
        "agent": {"name": "Minecraft", "version": 1},
        "username": username,
        "password": password,
        "clientToken": client_token,
        "requestUser": True
    })
    return auth_response ["selectedProfile"] ["id"], auth_response ["accessToken"]