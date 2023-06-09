import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import string
import random
import base64

# Generate a random string, upper case, lower case, numbers
def id_generator(N=32, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

# AES class implementation
# encrypt(raw input) -> base64 output
# decrypt(base64 input) -> raw output
class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw_bytes: bytes = b"", raw_str: str = ""):
        if raw_bytes != b"":
            raw = raw_bytes
        elif raw_str != "":
            raw = raw_str
        else:
            raise TypeError

        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        if type(raw) is bytes:
            return base64.b64encode(iv + cipher.encrypt(raw))
        else:
            return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc, isFile=False):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        if isFile:
            return self._unpad(cipher.decrypt(enc[AES.block_size:]))
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        if type(s) is bytes:
            return s + ((self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)).encode()
        else: 
            return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
