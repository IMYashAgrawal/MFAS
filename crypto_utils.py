import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

USER_SECRET_KEY = "thisisaprojectnamemultifactorauthenticationsystem"

SECRET_KEY = hashlib.sha256(USER_SECRET_KEY.encode()).digest()

def encrypt(plain_text):
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    encrypted_data = cipher.iv + cipher_text
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt(encrypted_text_b64):
    encrypted_data = base64.b64decode(encrypted_text_b64)
    iv = encrypted_data[:AES.block_size]
    cipher_text = encrypted_data[AES.block_size:]
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(cipher_text), AES.block_size)
    return decrypted_data
