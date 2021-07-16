import json

from LayerOne.network.conn_wrapper import ConnectionWrapper
from LayerOne.types.string import String

class Chat:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper) -> (dict, int):
        _str, str_len = String.read (conn_wrapper)
        return json.loads (_str), str_len
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: dict) -> None:
        _str = json.dumps (value)
        String.write (conn_wrapper, _str)
