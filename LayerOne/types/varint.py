from LayerOne.types.common import ProtocolException, switch_format
from LayerOne.network.conn_wrapper import ConnectionWrapper

class _VarBase:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper, max_read: int, bit_count: int, name: str) -> (int, int):
        read_count: int = 0
        result: int = 0
        _input: int = 0
        while True:
            _input = conn_wrapper.read_one ()
            value: int = (_input & 0b01111111)
            result |= (value << (7 * read_count))

            read_count += 1
            if read_count > max_read: raise ProtocolException (f"{name} is too big")
            if _input & 0b10000000 == 0: break
        result_signed = switch_format ("@I", "<i", result)
        return result_signed, read_count
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int, max_written: int, bit_count: int, name: str) -> None:
        value_unsigned = switch_format ("<i", "@I", value)
        if value_unsigned >> bit_count > 0: raise ProtocolException (f"{name} is too big")
        while True:
            temp: int = value_unsigned & 0b01111111
            value_unsigned >>= 7
            if value_unsigned != 0:
                temp |= 0b10000000
            conn_wrapper.write_one (temp)
            if value_unsigned == 0:
                break

class VarInt:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper): return _VarBase.read (conn_wrapper = conn_wrapper, max_read = 7, bit_count = 32, name = "VarInt")
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int): return _VarBase.write (conn_wrapper = conn_wrapper, value = value, max_written = 7, bit_count = 32, name = "VarInt")

class VarLong:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper): return _VarBase.read (conn_wrapper = conn_wrapper, max_read = 7, bit_count = 32, name = "VarLong")
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int): return _VarBase.write (conn_wrapper = conn_wrapper, value = value, max_written = 7, bit_count = 32, name = "VarInt")
