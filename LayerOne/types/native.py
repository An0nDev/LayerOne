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

def proxy_read (fmt): return lambda conn_wrapper: _NativeBase.read (conn_wrapper, f"!{fmt}")
def proxy_write (fmt): return lambda conn_wrapper, value: _NativeBase.write (conn_wrapper, value, f"!{fmt}")

class UShort:
    read = proxy_read ("H")
    write = proxy_write ("H")