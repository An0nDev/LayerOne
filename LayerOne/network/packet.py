import io, zlib

from typing import Tuple, Any, Union

from LayerOne.network.conn_wrapper import DummySocket, ConnectionWrapper
from LayerOne.types.common import ProtocolException
from LayerOne.types.varint import VarInt

class Packet:
    @staticmethod
    def read (conn_wrapper: ConnectionWrapper, compression_threshold: int = 0) -> (int, bytes):
        length, length_length = VarInt.read (conn_wrapper)
        if compression_threshold <= 0:
            return Packet._read_id_and_data (conn_wrapper, length)
        else:
            packet_length = length
            data_length, data_length_length = VarInt.read (conn_wrapper)
            compressed_length = packet_length - data_length_length
            if data_length == 0: # packet is uncompressed
                uncompressed_length = compressed_length
                packet = conn_wrapper.read (uncompressed_length)
            else: # data_length is the size of the uncompressed packet
                uncompressed_length = data_length
                if uncompressed_length < compression_threshold: raise ProtocolException ("Packet was sent compressed even though its length is below the compression threshold")
                compressed_packet = conn_wrapper.read (compressed_length)
                packet = zlib.decompress (compressed_packet)
                if len (packet) != uncompressed_length: raise ProtocolException ("Actual length of uncompressed packet does not match provided length")
            return Packet._read_id_and_data (packet, uncompressed_length)
    @staticmethod
    def _read_id_and_data (conn_wrapper_or_packet: Union [ConnectionWrapper, bytes], length: int) -> (int, bytes):
        if type (conn_wrapper_or_packet) == bytes:
            conn_wrapper = ConnectionWrapper (DummySocket (io.BytesIO (conn_wrapper_or_packet)))
        else:
            conn_wrapper = conn_wrapper_or_packet

        packet_id, packet_id_length = VarInt.read (conn_wrapper)
        data_length = length - packet_id_length
        data = conn_wrapper.read (data_length)
        return packet_id, data
    @staticmethod
    def decode_fields (data: bytes, spec: list) -> (list, int):
        all_decoded = []
        total_length = 0
        remainder: bytes = data
        for spec_item in spec:
            decoded, length = spec_item.read (ConnectionWrapper (DummySocket (io.BytesIO (remainder))))
            remainder = remainder [length:]
            all_decoded.append (decoded)
            total_length += length
        if len (remainder) > 0: raise ProtocolException (f"Data was left after decoding fields: {data}")
        return all_decoded# , total_length
    @staticmethod
    def encode_fields (*natives_and_specs: Tuple [Any, Any]) -> bytes:
        all_encoded = bytearray ()
        for native, spec in natives_and_specs:
            encoded_holder = io.BytesIO ()
            spec.write (ConnectionWrapper (DummySocket (encoded_holder)), native)
            encoded = encoded_holder.getvalue ()
            for byte in encoded: all_encoded.append (byte)
        return bytes (all_encoded)
    @staticmethod
    def write (conn_wrapper: ConnectionWrapper, packet_id: int, data: bytes, compression_threshold: int = 0, force_dont_encrypt: bool = False):
        def _write_data (_data: bytes): conn_wrapper.write (_data, force_dont_encrypt = force_dont_encrypt)

        packet_id_buffer, packet_id_length = Packet._int_to_varint_buffer (packet_id)

        if compression_threshold <= 0:
            length_buffer, length_length = Packet._int_to_varint_buffer (packet_id_length + len (data))

            _write_data (length_buffer)
            _write_data (packet_id_buffer)
            _write_data (data)
        else:
            if len (data) < compression_threshold:
                data_length_buffer, data_length_length = Packet._int_to_varint_buffer (0)
                packet = packet_id_buffer + data
            else:
                data_length_buffer, data_length_length = Packet._int_to_varint_buffer (len (data))
                packet = zlib.compress (packet_id_buffer + data)
            packet_length_buffer, packet_length_length = Packet._int_to_varint_buffer (data_length_length + len (packet))
            _write_data (packet_length_buffer)
            _write_data (data_length_buffer)
            _write_data (packet)
    @staticmethod
    def _int_to_varint_buffer (value: int) -> (bytes, int):
        holder = io.BytesIO ()
        VarInt.write (ConnectionWrapper (DummySocket (holder)), value)
        buffer = holder.getvalue ()
        return buffer, len (buffer)