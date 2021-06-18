import struct

class ProtocolException (Exception):
    pass

def bitstring (byte: int):
    return "0b" + format (byte, '08b')

def multi_bitstring (_bytes: bytes):
    return " ".join (bitstring (byte) for byte in _bytes)

def switch_format (og: str, new: str, value):
    return struct.unpack (new, struct.pack (og, value)) [0]