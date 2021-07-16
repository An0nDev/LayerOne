import struct

from LayerOne.network.conn_wrapper import ConnectionWrapper

class _NativeBase:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper, fmt: str) -> (int, int):
        size = struct.calcsize (fmt)
        raw = conn_wrapper.read (size)
        return struct.unpack (fmt, raw) [0], size
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, value: int, fmt: str) -> None:
        conn_wrapper.write (struct.pack (fmt, value))

def proxy_read (fmt, endianness = '!'): return lambda conn_wrapper: _NativeBase.read (conn_wrapper, f"{endianness}{fmt}")
def proxy_write (fmt, endianness = '!'): return lambda conn_wrapper, value: _NativeBase.write (conn_wrapper, value, f"{endianness}{fmt}")
def proxy (fmt, endianness = '!'): return proxy_read (fmt, endianness = endianness), proxy_write (fmt, endianness = endianness)

class Boolean:  read, write = proxy ("?")
class Byte:     read, write = proxy ("b")
class UByte:    read, write = proxy ("B")
class Short:    read, write = proxy ("h")
class UShort:   read, write = proxy ("H")
class UShortLE: read, write = proxy ("H", endianness = '<')
class Int:      read, write = proxy ("i")
class UInt:     read, write = proxy ("I")
class Long:     read, write = proxy ("q")
class ULong:    read, write = proxy ("Q")
class Float:    read, write = proxy ("f")
class Double:   read, write = proxy ("d")
