from LayerOne.network.conn_wrapper import ConnectionWrapper
from LayerOne.types.varint import VarInt

class ByteArray:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper) -> (int, int):
        length, length_length = VarInt.read (conn_wrapper)
        data = conn_wrapper.read (length)
        return data, length_length + length
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: bytes) -> None:
        VarInt.write (conn_wrapper, len (value))
        conn_wrapper.write (value)