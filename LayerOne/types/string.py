from LayerOne.network.conn_wrapper import ConnectionWrapper
from LayerOne.types.varint import VarInt

_string_encoding = "utf-8"

class String:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper) -> (str, int):
        str_len, str_len_len = VarInt.read (conn_wrapper)
        _str = conn_wrapper.read (str_len)
        return _str.decode (_string_encoding), str_len_len + str_len
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: str) -> None:
        VarInt.write (conn_wrapper, len (value))
        conn_wrapper.write (value.encode (_string_encoding))