import io
from typing import Callable, Any, Union, Optional, List

from LayerOne.network.conn_wrapper import ConnectionWrapper, DummySocket
from LayerOne.types.native import Boolean, UShort, UShortLE, UByte, Int
from LayerOne.types.varint import VarInt

def world_to_map_chunk_bulk_datas (world: dict, max_chunk_columns_per_packet: int = 10) -> List [bytes]:
    datas = []

    chunk_columns_items = list (world ["chunk_columns"].items ())
    chunk_columns_count = len (chunk_columns_items)
    chunk_columns_count += (max_chunk_columns_per_packet - (chunk_columns_count % max_chunk_columns_per_packet)) % max_chunk_columns_per_packet
    chunk_columns_partition_count = chunk_columns_count // max_chunk_columns_per_packet
    chunk_columns_partitions = []
    for partition_index in range (chunk_columns_partition_count):
        partition_start_index = (max_chunk_columns_per_packet * partition_index)
        partition_end_index = (max_chunk_columns_per_packet * (partition_index + 1))
        partition = chunk_columns_items [partition_start_index:partition_end_index]
        print (f"{partition_index} = {partition_start_index}:{partition_end_index} = len {len (partition)}")
        try:
            assert (len (partition) == max_chunk_columns_per_packet) if partition_index < (chunk_columns_partition_count - 1) else (max_chunk_columns_per_packet >= len (partition) > 0)
        except AssertionError:
            raise
        print ("partition good")
        chunk_columns_partitions.append (partition)

    for partition in chunk_columns_partitions:
        print (f"partition {partition}")
        out_buffer = io.BytesIO ()
        out_wrapper = ConnectionWrapper (DummySocket (out_buffer))

        send_skylight = world ["dimension"] != -1
        Boolean.write (out_wrapper, send_skylight)

        VarInt.write (out_wrapper, len (partition))

        for chunk_coords, chunk_column in partition:
            print (f"chunk column at {chunk_coords}")
            Int.write (out_wrapper, chunk_coords [0])
            Int.write (out_wrapper, chunk_coords [1])

            column_block_data = chunk_column [0]

            primary_bit_mask: int = 0
            sorted_keys = list (column_block_data.keys ())
            sorted_keys.sort ()
            for chunk_y in sorted_keys:
                primary_bit_mask |= (1 << chunk_y)
            UShort.write (out_wrapper, primary_bit_mask)

            print (f"wrote header for chunk at {chunk_coords [0]},{chunk_coords [1]} with pbm {primary_bit_mask}")

        CHUNK_STEP = 16
        for chunk_coords, chunk_column in partition:
            print (f"sending chunk at {chunk_coords [0]},{chunk_coords [1]}")
            column_block_data = chunk_column [0]
            column_biome_data = chunk_column [1]

            sorted_keys = list (column_block_data.keys ())
            sorted_keys.sort ()

            for chunk_y in sorted_keys:
                block_data = column_block_data [chunk_y]

                def write_for_each_block (source_data: dict, two_inputs_per_output: bool, placeholder_func: Callable [[], None], bottom_func: Union [Callable [[Any], None], Callable [[Optional [Any], Optional [Any]], None]], dimensions: int, _current_dimension: int = 1):
                    bottom = dimensions - _current_dimension == 0
                    if bottom and two_inputs_per_output:
                        for half_bottom_coordinate in range (CHUNK_STEP // 2):
                            first_bottom_coordinate = half_bottom_coordinate * 2
                            second_bottom_coordinate = first_bottom_coordinate + 1
                            first_bottom = source_data.get (first_bottom_coordinate, None)
                            second_bottom = source_data.get (second_bottom_coordinate, None)
                            bottom_func (first_bottom, second_bottom)
                        return

                    for single_coordinate in range (CHUNK_STEP):
                        if single_coordinate not in source_data:
                            for _ in range (CHUNK_STEP ** (dimensions - _current_dimension) // (2 if two_inputs_per_output else 1)): placeholder_func ()
                            continue

                        if not bottom:
                            write_for_each_block (source_data [single_coordinate], two_inputs_per_output, placeholder_func, bottom_func, dimensions, _current_dimension = _current_dimension + 1)
                            continue

                        # bottom and not two_inputs_per_output
                        bottom_func (source_data [single_coordinate])

                def write_single_block_data (single_block_data: list):
                    out = 0
                    out |= (single_block_data [0] << 4 & 0b1111111111110000)
                    out |= (single_block_data [1]      & 0b0000000000001111)
                    UShortLE.write (out_wrapper, out)
                write_for_each_block (source_data = block_data, two_inputs_per_output = False, placeholder_func = lambda: UShortLE.write (out_wrapper, 0), bottom_func = write_single_block_data, dimensions = 3)

                def gen_write_double_data (index_into_data: int):
                    def write_double_data (first_block_data: list, second_block_data: list):
                        out = 0
                        if first_block_data is not None:  out |= (first_block_data  [index_into_data] << 4 & 0b11110000)
                        if second_block_data is not None: out |= (second_block_data [index_into_data]      & 0b00001111)
                        UByte.write (out_wrapper, out)
                    return write_double_data
                write_for_each_block (source_data = block_data, two_inputs_per_output = True, placeholder_func = lambda: UByte.write (out_wrapper, 0), bottom_func = gen_write_double_data (2), dimensions = 3)
                if send_skylight:
                    write_for_each_block (source_data = block_data, two_inputs_per_output = True, placeholder_func = lambda: UByte.write (out_wrapper, 0), bottom_func = gen_write_double_data (3), dimensions = 3)

            for z in range (CHUNK_STEP):
                for x in range (CHUNK_STEP):
                    UByte.write (out_wrapper, column_biome_data [z] [x])

        datas.append (bytes (out_buffer.getvalue ()))

    return datas
# def gen_chunk_data_packet_data_to_delete_chunk (chunk_x, chunk_z):
#