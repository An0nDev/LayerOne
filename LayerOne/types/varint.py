from LayerOne.types.common import ProtocolException, switch_format
from LayerOne.network.conn_wrapper import ConnectionWrapper

class _VarBase:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper, max_bits: int, name: str) -> (int, int):
        read_count: int = 0
        result: int = 0
        _input: int = 0
        while True:
            _input = conn_wrapper.read_one ()
            value: int = (_input & 0b01111111)
            result |= (value << (7 * read_count))

            read_count += 1
            if result >> max_bits > 0: raise ProtocolException (f"{name} is too big")
            if _input & 0b10000000 == 0: break
        result_signed = switch_format ("@I", "<i", result)
        return result_signed, read_count
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int, max_bits: int, name: str) -> None:
        value_unsigned = switch_format ("<i", "@I", value)
        if value_unsigned >> max_bits > 0: raise ProtocolException (f"{name} is too big")
        while True:
            temp: int = value_unsigned & 0b01111111
            value_unsigned >>= 7
            if value_unsigned != 0:
                temp |= 0b10000000
            conn_wrapper.write_one (temp)
            if value_unsigned == 0:
                break

_BITS_PER_BYTE = 8
# these are because in java, varints and varlongs decompress to their associated native types, which have max sizes of 4 and 8 bytes respectively
_VARINT_MAX_BITS = _BITS_PER_BYTE * 4
_VARLONG_MAX_BITS = _BITS_PER_BYTE * 8

class VarInt:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper): return _VarBase.read (conn_wrapper = conn_wrapper, max_bits = _VARINT_MAX_BITS, name = "VarInt")
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int): return _VarBase.write (conn_wrapper = conn_wrapper, value = value, max_bits = _VARINT_MAX_BITS, name = "VarInt")

class VarLong:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper): return _VarBase.read (conn_wrapper = conn_wrapper, max_bits = _VARLONG_MAX_BITS, name = "VarLong")
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int): return _VarBase.write (conn_wrapper = conn_wrapper, value = value, max_bits = _VARLONG_MAX_BITS, name = "VarInt")
