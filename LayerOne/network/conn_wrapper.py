import io
import socket
import threading
from typing import Union

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class DummySocket:
    def __init__ (self, wrapped: io.BytesIO):
        self.wrapped = wrapped
    def recv (self, size: int, flags: int):
        return self.wrapped.read (size)
    def send (self, data: bytes):
        return self.wrapped.write (data)

class ConnectionWrapper:
    def __init__ (self, client: Union [socket.socket, DummySocket]):
        self.client = client
        self.encryption_enabled = False
        self.encryptor = None
        self.decryptor = None

        self.write_lock = threading.Lock ()
    def setup_encryption (self, encryption_key: bytes):
        cipher = Cipher (algorithm = algorithms.AES (encryption_key), mode = modes.CFB8 (encryption_key))
        self.encryptor = cipher.encryptor ()
        self.decryptor = cipher.decryptor ()
        self.encryption_enabled = True
    def read_one (self) -> int:
        return self.read (1) [0]
    def read (self, count: int) -> bytes:
        if count == 0: return b""
        data = self.client.recv (count, socket.MSG_WAITALL)
        if data is None: raise EOFError ()
        if len (data) < count: raise EOFError ()
        return self.decryptor.update (data) if self.encryption_enabled else data
    def write_one (self, value) -> None:
        self.write (bytes ([value]))
    def write (self, data, force_dont_encrypt = False) -> None:
        with self.write_lock:
            self.client.send (self.encryptor.update (data) if (self.encryption_enabled and not force_dont_encrypt) else data)
    def ensure_closed (self) -> None:
        try:
            self.client.shutdown (socket.SHUT_RDWR)
            self.client.close ()
        except OSError as os_error:
            if os_error.errno not in (9, 107): raise # Allow "Bad file descriptor" and "Transport endpoint is not connected"
