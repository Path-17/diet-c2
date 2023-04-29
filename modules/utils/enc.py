import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import os
import sys

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
        print(type(s))
        return s[:-ord(s[len(s)-1:])]

test = AESCipher("thisisakey:)1234")

if sys.argv[1] == "file":
    f_path = sys.argv[2]
    save_path = sys.argv[3]
    
    # Read the file bytes
    with open(f_path, "rb") as enc_f:
        f_bytes = enc_f.read()
        # encrypt 
        enc_bytes = test.encrypt(f_bytes)
        # save to save_path
        with open(save_path, "wb") as f:
            f.write(enc_bytes)
if sys.argv[1] == "string":
    str_raw = sys.argv[2]
    print(test.encrypt(raw_str=str_raw))




