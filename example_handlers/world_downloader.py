import io
import json
import threading
import pickle

from LayerOne.extra.handler import Host, PrintFunc, SendFunc, Handler
from LayerOne.extra.mojang_client_auth import auth_from_file
from LayerOne.network.conn_wrapper import ConnectionWrapper, DummySocket
from LayerOne.network.packet import Packet
from LayerOne.network.server.proxy import Proxy
from LayerOne.types.byte_array import ByteArray
from LayerOne.types.common import ProtocolException
from LayerOne.types.native import Byte, Int, Boolean, UShort, UByte, UShortLE
from LayerOne.types.string import String
from LayerOne.types.varint import VarInt
from LayerOne.network.extra.world_manipulation import world_to_map_chunk_bulk_datas

class WorldDownloader (Handler):
    def __init__ (self, client_address: Host):
        self.has_dimension = False
        self.dimension = 0

        self.chunk_columns_lock = threading.Lock ()
        self.chunk_columns = {}
    def ready (self): pass
    def client_to_server (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        if packet_id == 0x01: # Chat Message
            chat_message: str = Packet.decode_fields (packet_data, (String,)) [0]
            if not chat_message.startswith ("."): return True
            command = chat_message [len ('.'):]
            def respond (response: str): to_client_func (0x02, Packet.encode_fields ((json.dumps ({"text": response}), String), (0x02, Byte)))
            split_command = command.split (" ")
            name = split_command [0]
            args = split_command [1:]
            if name != "save":
                respond ("Only valid command is save")
                return False
            if len (args) != 1:
                respond ("Need exactly one argument, output filename")
                return False
            output_file_name = args [0]
            assert self.has_dimension
            dump = {
                "dimension": self.dimension
            }
            full_output_file_name = f"../../LayerTwo/worlds/{output_file_name}.l1w"
            with self.chunk_columns_lock:
                dump ["chunk_columns"] = self.chunk_columns
                chunk_column_count = len (self.chunk_columns)
                with open (full_output_file_name, "wb+") as output_file:
                    pickle.dump (dump, output_file)
            respond (f"Saved {chunk_column_count} chunks to {full_output_file_name}")
            return False
        return True
    def server_to_client (self, current_state: dict, print_func: PrintFunc, to_client_func: SendFunc, to_server_func: SendFunc, packet_id: int, packet_data: bytes) -> bool:
        if packet_id == 0x01:
            player_eid, gamemode, dimension, difficulty, max_players, level_type, reduced_debug_info = Packet.decode_fields (packet_data, (Int, UByte, Byte, UByte, UByte, String, Boolean))
            self.has_dimension = True
            print_func (f"picked up dimension {dimension}")
            self.dimension = dimension
            return True

        def p_byte (byte, size = 1): return bin (byte) [2:].zfill (8 * size)
        def get_leftover (_reader: ConnectionWrapper): return len (reader.client.wrapped.getbuffer ()) - reader.client.wrapped.tell ()

        CHUNK_STEP = 16
        def read_chunk_column (_reader: ConnectionWrapper, _primary_bit_mask: int, _has_skylight: bool, _has_biome: bool, _chunk_x: int, _chunk_z: int):
            def dbg_print (*args): return print (*args) if _chunk_x == 0 and _chunk_z == 0 else None

            column_block_data = {} # dict of list of list of blocks
            # and to access block at chunk_y, x, y, z, you do
            # column_block_data [chunk_y] [y] [z] [x]
            for chunk_y in range (CHUNK_STEP):
                block_data = {}
                if not (_primary_bit_mask & (1 << chunk_y)):
                    # dbg_print (f"no data for chunk y {chunk_y}")
                    continue
                # dbg_print (f"have data for chunk y {chunk_y}")

                def to_abs (_x, _y, _z): return (_chunk_x * CHUNK_STEP) + _x, (chunk_y * CHUNK_STEP) + _y, (_chunk_z * CHUNK_STEP) + _z

                for y in range (CHUNK_STEP):
                    z_set = {}
                    for z in range (CHUNK_STEP):
                        x_set = {}
                        for x in range (CHUNK_STEP):
                            id_and_meta_data = UShortLE.read (_reader) [0]
                            block_id = id_and_meta_data >> 4
                            meta_data = id_and_meta_data & 0b1111

                            if block_id > 0:
                                # print (f"{to_abs (x, y, z)} {block_id} {meta_data} (src {p_byte (id_and_meta_data, size = 2)})")

                                x_set [x] = [block_id, meta_data]
                        if len (x_set) > 0: z_set [z] = x_set
                    if len (z_set) > 0: block_data [y] = z_set

                def _read_half_byte_array (label: str):
                    def _append_to_data_for_coord (_x, _y, _z, to_append):
                        if _y in block_data and _z in block_data [_y] and _x in block_data [_y] [_z]: block_data [_y] [_z] [_x].append (to_append)

                    for y in range (CHUNK_STEP):
                        for z in range (CHUNK_STEP):
                            for half_x in range (CHUNK_STEP // 2):
                                both_vals = UByte.read (_reader) [0]

                                first_x = half_x * 2
                                first_val = both_vals & 0b11110000 >> 4
                                # dbg_print (f"{to_abs (first_x, y, z)} {label}: {first_val}")
                                _append_to_data_for_coord (first_x, y, z, first_val)

                                second_x = first_x + 1
                                second_val = both_vals & 0b00001111
                                # dbg_print (f"{to_abs (second_x, y, z)} {label}: {second_val}")
                                _append_to_data_for_coord (second_x, y, z, second_val)
                _read_half_byte_array ("block light")
                if _has_skylight: _read_half_byte_array ("skylight")

                column_block_data [chunk_y] = block_data

            if _has_biome:
                column_biome_data = []
                for z in range (CHUNK_STEP):
                    x_set = []
                    for x in range (CHUNK_STEP):
                        abs_x = (_chunk_x * CHUNK_STEP) + x
                        abs_z = (_chunk_z * CHUNK_STEP) + z
                        biome_id = UByte.read (_reader) [0]
                        # dbg_print (f"biome at {abs_x},{abs_z} is {p_byte (biome_id)}")
                        x_set.append (biome_id)
                    column_biome_data.append (x_set)
                print ("read column biome data")
            else:
                column_biome_data = None

            return column_block_data, column_biome_data

        updated_chunk_columns = []

        if packet_id == 0x21:
            print_func (f"--- (SINGLE) chunk data, len {len (packet_data)}")

            chunk_x, chunk_z, new, primary_bit_mask, chunk_data = Packet.decode_fields (packet_data, (Int, Int, Boolean, UShort, ByteArray))
            print (f"new: {new}")
            assert self.has_dimension
            print_func (f"{chunk_x},{chunk_z} {bin (primary_bit_mask)}")

            reader = ConnectionWrapper (DummySocket (io.BytesIO (chunk_data)))
            column = read_chunk_column (reader, primary_bit_mask, self.dimension == 0, new, chunk_x, chunk_z)
            with self.chunk_columns_lock:
                if new and len (column [0]) == 0:
                    if (chunk_x, chunk_z) in self.chunk_columns:
                        print ("deleted chunk column")
                        del self.chunk_columns [chunk_x, chunk_z]
                else:
                    if new:
                        print ("new column")
                        self.chunk_columns [chunk_x, chunk_z] = column
                        updated_chunk_columns.append ((chunk_x, chunk_z))
                    else:
                        print ("updated column")
                        self.chunk_columns [chunk_x, chunk_z] [0].update (column [0])
                        updated_chunk_columns.append ((chunk_x, chunk_z))
            leftover = get_leftover (reader)
            if leftover > 0: raise ProtocolException (f"we had {leftover} bytes left in the single chunk packet!")
            print_func ("--- end of single")
            should_roundtrip = False
        elif packet_id == 0x26:
            print_func (f"--- (MULTI) map chunk bulk, len {len (packet_data)}")

            reader = ConnectionWrapper (DummySocket (io.BytesIO (packet_data)))
            has_light = Boolean.read (reader) [0]
            chunk_column_count = VarInt.read (reader) [0]
            print_func (f"has light: {has_light}, chunk column count: {chunk_column_count}")

            meta = []
            for chunk_index in range (chunk_column_count):
                chunk_x = Int.read (reader) [0]
                chunk_z = Int.read (reader) [0]
                primary_bit_mask = UShort.read (reader) [0]
                meta.append ((chunk_x, chunk_z, primary_bit_mask))

            new_chunk_columns = {}
            for chunk_x, chunk_z, primary_bit_mask in meta:
                print_func (f"reading chunk at {chunk_x},{chunk_z} with pbm {bin (primary_bit_mask)}")
                column = read_chunk_column (reader, primary_bit_mask, has_light, True, chunk_x, chunk_z)
                if len (column [0]) > 0:
                    new_chunk_columns [chunk_x, chunk_z] = column
                    updated_chunk_columns.append ((chunk_x, chunk_z))

            with self.chunk_columns_lock:
                self.chunk_columns.update (new_chunk_columns)

            leftover = get_leftover (reader)
            if leftover > 0: raise ProtocolException (f"we had {leftover} bytes left in the multi chunk packet!")
            print_func ("--- end of multi")
            should_roundtrip = True
        else: return True

        with self.chunk_columns_lock:
            actual_updated_chunk_columns = {chunk_coords: self.chunk_columns [chunk_coords] for chunk_coords in updated_chunk_columns}

        datas =world_to_map_chunk_bulk_datas ({
            "dimension": self.dimension,
            "chunk_columns": actual_updated_chunk_columns
        })
        assert len (datas) == 1
        data = datas [0]
        to_client_func (0x26, data)

        return False
    def disconnected (self): pass

if __name__ == "__main__":
    Proxy (quiet = True, host = ("0.0.0.0", 25567), target = ("localhost", 25566), auth = auth_from_file ("../auth.json"), handler_class = WorldDownloader)