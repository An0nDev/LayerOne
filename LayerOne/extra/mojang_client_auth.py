import json
import os

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

def auth_from_file (file_path: str) -> (str, str): # UUID, access token
    with open (os.path.abspath (file_path), "r") as auth_file:
        auth_json = json.load (auth_file)
    return authenticate (auth_json ["email"], auth_json ["password"], auth_json ["client_token"])