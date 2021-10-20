# python3 main.py auth.json 0.0.0.0:25567 mc.hypixel.net:25565 example_handlers.hypixel_proxy:HypixelProxyHandler

import json
import tkinter
import pathlib
from typing import Optional

from LayerOne.network.server.proxy import Proxy
from hypixel_proxy import HypixelProxyHandler

def data_from_lunar () -> dict:
    with open (pathlib.Path.home () / ".lunarclient" / "settings" / "game" / "accounts.json") as accounts_file: return json.load (accounts_file)

def accounts_from_lunar () -> dict [str, str]: # username: UUID
    accounts_json = data_from_lunar ()
    out_accounts = {}
    for account_id, account_data in accounts_json ["accounts"].items ():
        if "accessToken" not in account_data: continue
        profile = account_data ["minecraftProfile"]
        out_accounts [profile ["name"]] = profile ["id"]
    return out_accounts

def auth_from_lunar (uuid: str) -> str: # UUID, access token
    accounts_json = data_from_lunar ()
    for account_id, account_data in accounts_json ["accounts"].items ():
        profile = account_data ["minecraftProfile"]
        if uuid == profile ["id"]: return account_data ["accessToken"]
    raise Exception (f"account with uuid {uuid} not found in lunar accounts.json")

class HypixelProxyGUI:
    choose_placeholder = "<choose username>"
    reload_text = "🔄"
    start_text = "▶️"
    stop_text = "⏹️"
    def __init__ (self):
        self.running = False
        self.proxy = Proxy (quiet = True, host = ("0.0.0.0", 25567), target = ("mc.hypixel.net", 25565), auth = None, handler_class = HypixelProxyHandler, forking = True)
        self.start_stop_button_text = None
        self.start_stop_button = None

        self.root = tkinter.Tk ()
        self.root.wm_title ("Hypixel Proxy GUI")

        self.accounts = accounts_from_lunar ()

        self.account_selection = tkinter.StringVar ()
        self.account_selection.set (HypixelProxyGUI.choose_placeholder)
        self.account_selector = tkinter.OptionMenu (self.root, self.account_selection, HypixelProxyGUI.choose_placeholder, *self.accounts.keys ())
        self.account_selector.grid (row = 0, column = 0, sticky = "NSEW")
        self.account_selection.trace ("w", self._on_account_select)

        self.account_list_refresh_button = tkinter.Button (self.root, command = self._on_account_list_refresh, text = HypixelProxyGUI.reload_text)
        self.account_list_refresh_button.grid (row = 0, column = 1, sticky = "NSEW")

        self.selected_account = None
        self.auth: tuple [Optional [str], Optional [str]] = (None, None)

        self.root.mainloop ()

        if self.running: self._start_stop ()
    def _on_account_list_refresh (self):
        self.accounts = accounts_from_lunar ()
        menu = self.account_selector.children ["menu"]
        menu.delete (1, "end")

        for account in self.accounts.keys ():
            menu.add_command (label = account, command = lambda _account = account: self.account_selection.set (_account))
    def _on_account_select (self, internal_variable_name, empty_string, operation):
        was_running = self.running
        if was_running: self._start_stop ()

        selected_account = self.account_selection.get ()
        if selected_account == HypixelProxyGUI.choose_placeholder: return
        selected_account = self.accounts [selected_account]
        if selected_account == self.selected_account: return
        is_first_select = self.selected_account is None
        self.selected_account = selected_account
        self.proxy.auth = (self.selected_account, auth_from_lunar (self.selected_account))

        if is_first_select: self._on_first_account_select ()

        if was_running: self._start_stop ()
    def _on_first_account_select (self):
        self.start_stop_button_text = tkinter.StringVar ()
        self.start_stop_button_text.set (HypixelProxyGUI.start_text)
        self.start_stop_button = tkinter.Button (self.root, textvariable = self.start_stop_button_text, command = self._start_stop)
        self.start_stop_button.grid (row = 1, column = 0, columnspan = 2, sticky = "NSEW")

        self._start_stop ()
    def _start_stop (self):
        self.proxy.start () if not self.running else self.proxy.stop ()
        self.running = not self.running
        self.start_stop_button_text.set (HypixelProxyGUI.start_text if not self.running else HypixelProxyGUI.stop_text)

if __name__ == "__main__":
    HypixelProxyGUI ()