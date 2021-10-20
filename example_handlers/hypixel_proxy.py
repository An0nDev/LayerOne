import io
import json
from multiprocessing import Pool
from typing import Optional

import requests

import re

from LayerOne.extra.handler import Host, PrintFunc, SendFunc, Handler
from LayerOne.network.conn_wrapper import DummySocket, ConnectionWrapper
from LayerOne.network.extra.chat_formatting import chat_to_plain_str
from LayerOne.network.packet import Packet
from LayerOne.types.chat import Chat
from LayerOne.types.native import Byte, Int, UByte
from LayerOne.types.string import String

HYPIXEL_API_KEY = "54f16ef3-1854-4753-af20-b196f937cb6f"

def get_status (username) -> Optional [dict]:
    uuid_response = requests.get (f"https://api.mojang.com/users/profiles/minecraft/{username}")
    uuid_response.raise_for_status ()
    if uuid_response.status_code == 204: return
    uuid = uuid_response.json () ["id"]

    status_resp = requests.get (f"https://api.hypixel.net/status",
                                params = {"key": HYPIXEL_API_KEY, "uuid": uuid})
    status_resp.raise_for_status ()
    status_json = status_resp.json ()
    if not status_json ["success"]:
        print (f"Failed to get status: {status_json ['cause']}")
        return
    status = status_json ["session"]
    return status

BEDWARS_MODES_TO_FRIENDLY_NAMES = {
    "EIGHT_ONE": "solos",
    "EIGHT_TWO": "doubles",
    "FOUR_THREE": "threes",
    "FOUR_FOUR": "fours",
    "TWO_FOUR": "4v4"
}

def status_to_str (status) -> Optional [str]:
    if not status ["online"]: return
    if status ["gameType"] == "BEDWARS":
        if status ["mode"] == "LOBBY":
            return "is in a Bed Wars lobby"
        friendly_mode = BEDWARS_MODES_TO_FRIENDLY_NAMES.get (status ["mode"])
        if friendly_mode is None: friendly_mode = status ["mode"].lower ()
        return f"is in a Bed Wars {friendly_mode} game on {status ['map']}"
    return f"is in a {' '.join (status ['gameType'].split ('_')).title ()} game"

def process_friend_line (friend_line) -> Optional [str]:
    print (f"I'm pretty sure this is a friend line: {friend_line}")
    username_match = re.fullmatch (r"([A-Za-z0-9_]+) is [\s\S]+", friend_line)
    if username_match is None:
        print (f"{friend_line} did not match for some reason")
        return
    username = username_match.group (1)

    print (f"detected {username}")

    if re.fullmatch (r"([A-Za-z0-9_]+) is currently offline", friend_line) is not None:
        return f"{friend_line}\n"

    status = get_status (username)
    status_str = status_to_str (status)
    if status_str is None:
        return f"{friend_line} (API disabled)\n"

    return f"{username} {status_str}\n"

CHAT_LINE_SEPARATOR = '-' * 53

class HypixelProxyHandler (Handler):
    def __init__ (self, client_address: Host):
        self.finding_f_list = False
    def ready (self): pass
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        if packet_id == 0x17:
            plugin_channel, _plugin_channel_len = String.read (ConnectionWrapper (DummySocket (io.BytesIO (packet_data))))
            data = packet_data [_plugin_channel_len:]
            print_func (f"PLUGIN TO SERVER plugin_channel={plugin_channel} data={data}")
            # return False
        if packet_id in [0x00]: return True # Keep Alive
        # print_func (f"{packet_id} {len (packet_data)}")
        # if packet_id == 0x01: print_func (f"--- CHAT MESSAGE {packet_data} ---")
        if packet_id == 0x01: # Chat Message
            chat_message: str = Packet.decode_fields (packet_data, (String,)) [0]

            if not chat_message.startswith ("/"): return True

            full_command = chat_message [len ("/"):]
            command_parts = full_command.split (" ")
            if command_parts [0] != "fl":
                if len (command_parts) < 2: return True
                command, subcommand = map (lambda _str: _str.lower (), command_parts [0:2])
                if command not in ("f", "friend", "friends"): return True
                if subcommand != "list": return True

            print_func ("DETECTED FRIENDS LIST REQUEST")
            self.finding_f_list = True
            return True
        return True # pass through other c2s packets
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        s2c_plugin_message_packet_id = 0x3F
        if packet_id == s2c_plugin_message_packet_id:
            plugin_channel, _plugin_channel_len = String.read (ConnectionWrapper (DummySocket (io.BytesIO (packet_data)))) # read name of plugin channel
            data = packet_data [_plugin_channel_len:] # read attached data

            print_func (f"PLUGIN TO CLIENT plugin_channel={plugin_channel} data={data}")

            if plugin_channel == "MC|Brand": # LUNAR BYPASS
                server_brand_name = Packet.decode_fields (data, (String,)) [0]
                if server_brand_name.startswith ("Hypixel BungeeCord"):
                    # server is telling client that we're hypixel... how about no

                    print_func ("lunar client bypass")

                    return False # drop packet

            if plugin_channel == "badlion:mods": # BLC BYPASS
                # server is telling client what badlion mods are ok

                print_func ("badlion client bypass")

                mods = json.loads (data.decode ())

                # allow perspective mod, if it's present in config
                if "Perspective" in mods: mods ["Perspective"] ["disabled"] = False

                out_holder = io.BytesIO ()
                String.write (ConnectionWrapper (DummySocket (out_holder)), plugin_channel)
                to_client_func (s2c_plugin_message_packet_id, out_holder.getvalue () + json.dumps (mods).encode ()) # write modified packet
                return False # drop original packet
        # if packet_id in [0x00, 0x02, 0x03, 0x04, 0x12, 0x13, 0x15, 0x18, 0x1c, 0x2A, 0x21, 0x24, 0x26, 0x35, 0x3b]: return True
        if packet_id in [0x00, 0x21, 0x26]: return True # Keep Alive, Chunk Data, Map Chunk Bulk
        # print_func (f"{packet_id} {len (packet_data)} {packet_data}")
        if packet_id == 0x01: print_func (f"--- JOIN GAME ---")
        # if packet_id == 0x02: print_func (f"--- CHAT MESSAGE {packet_data} ---")
        if packet_id == 0x07:
            dimension, difficulty, gamemode, level_type = Packet.decode_fields (packet_data, (Int, UByte, UByte, String))
            print_func (f"--- RESPAWN dimension={dimension} difficulty={difficulty} gamemode={gamemode} level_type={level_type}---")
        # print (f"packet id {hex (packet_id)} data {packet_data}")
        if not self.finding_f_list: return True

        if packet_id != 0x02: return True # Chat Message
        chat_json: dict
        position: int
        chat_json, position = Packet.decode_fields (packet_data, (Chat, Byte))
        if position > 1: return True # not in chat box
        chat_plain_str = chat_to_plain_str (chat_json)
        print_func (f"DETECTED CLIENTBOUND CHAT (len {len (chat_plain_str)}): {chat_plain_str}")

        chat_lines = chat_plain_str.split ("\n")
        print_func (f"Chat lines: {chat_lines}")
        if len (chat_lines) < 3: return True
        if chat_lines [0] != CHAT_LINE_SEPARATOR or chat_lines [-1] != CHAT_LINE_SEPARATOR: return True
        actual_chat_lines = chat_lines [1:-1]
        header = actual_chat_lines [0].strip ()
        if re.fullmatch (r"(?:<< )?Friends \(Page \d+ of \d+\)(?: >>)?", header) is None: return True
        friend_lines = actual_chat_lines [1:]

        self.finding_f_list = False

        out = f"{CHAT_LINE_SEPARATOR}\n"

        with Pool (processes = len (friend_lines)) as pool:
            processed_friend_lines = pool.map (process_friend_line, friend_lines)

        for processed_friend_line in processed_friend_lines:
            if processed_friend_line is not None: out += processed_friend_line

        out += CHAT_LINE_SEPARATOR

        out_json = {"text": out}

        to_client_func (0x02, Packet.encode_fields ((out_json, Chat), (position, Byte)))
    def disconnected (self): pass