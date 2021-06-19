import io
from typing import Union

from LayerOne.types.varint import VarInt
from LayerOne.network.conn_wrapper import ConnectionWrapper, DummySocket

class Utils:
    @staticmethod
    def int_to_varint_buffer (value: int) -> (bytes, int):
        holder = io.BytesIO ()
        VarInt.write (ConnectionWrapper (DummySocket (holder)), value)
        buffer = holder.getvalue ()
        return buffer, len (buffer)
    @staticmethod
    def buffer_to_str (buffer: bytes, trunc_threshold: int = 100):
        buffer_str = "(truncated)" if len (buffer) >= trunc_threshold else str (buffer)
        return f"{buffer_str} (len {len (buffer)})"
    @staticmethod
    def read_id_and_data (conn_wrapper_or_packet: Union [ConnectionWrapper, bytes], length: int) -> (int, bytes):
        if type (conn_wrapper_or_packet) == bytes:
            conn_wrapper = ConnectionWrapper (DummySocket (io.BytesIO (conn_wrapper_or_packet)))
        else:
            conn_wrapper = conn_wrapper_or_packet

        packet_id, packet_id_length = VarInt.read (conn_wrapper)
        data_length = length - packet_id_length
        data = conn_wrapper.read (data_length)
        return packet_id, data