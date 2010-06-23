import os
import hashlib
import base64
import struct

from Crypto.Cipher import AES

SALT_LEN = 4

PASSES_HASH = 100000
PASSES_CIPHER = 200000

class Error(Exception):
    pass

def _pad(s):
    padded_len = ((len(s) + 2 - 1) |  0xF) + 1
    padding_len = padded_len - len(s) - 2
    return os.urandom(padding_len) + s + struct.pack("!H", len(s))

def _unpad(padded):
    len, = struct.unpack("!H", padded[-2:])
    return padded[-(2 + len) :-2]

def _rinserepeat(f, input, count):
    for x in xrange(count):
        input = f(input)
    return input

def _cipher_key(passphrase):
    cipher_key = _rinserepeat(lambda k: hashlib.sha256(k).digest(),  
                              passphrase, 
                              PASSES_HASH if passphrase else 1)
    return cipher_key

def _cipher(passphrase, mode=AES.MODE_OFB):
    return AES.new(_cipher_key(passphrase), mode)

def fmt(secret, passphrase):
    salt = os.urandom(SALT_LEN)
    plaintext = salt + hashlib.sha1(secret).digest() + secret
    ciphertext = _rinserepeat(_cipher(passphrase).encrypt, 
                              _pad(plaintext), 
                              PASSES_CIPHER if passphrase else 1)

    return base64.b64encode(ciphertext)

def parse(formatted, passphrase):
    ciphertext = base64.b64decode(formatted)
    decrypted = _rinserepeat(_cipher(passphrase).decrypt,
                             ciphertext,
                             PASSES_CIPHER if passphrase else 1)
    decrypted = _unpad(decrypted)

    digest = decrypted[SALT_LEN:SALT_LEN+20]
    secret = decrypted[SALT_LEN+20:]

    if digest != hashlib.sha1(secret).digest():
        raise Error("error decrypting key")

    return secret

def generate():
    return fmt(hashlib.sha1(os.urandom(32)).digest(), "")
