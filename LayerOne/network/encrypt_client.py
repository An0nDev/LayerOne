from LayerOne.network.conn_wrapper import ConnectionWrapper

class EncryptData: pass

class ClientEncryptor:
    @staticmethod
    def encrypt (client: ConnectionWrapper) -> EncryptData:

        raise NotImplementedError ()

class FutureEncrypt:
    @staticmethod
    def encrypt (data: bytes, extra: EncryptData) -> bytes:
        raise NotImplementedError ()
    @staticmethod
    def decrypt (data: bytes, extra: EncryptData) -> bytes:
        raise NotImplementedError ()
