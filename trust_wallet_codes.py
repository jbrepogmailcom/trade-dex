# trust_wallet_codes.py
import getpass
import base64
import hashlib
from cryptography.fernet import Fernet

def derive_key(password: str) -> bytes:
    sha = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(sha)

def decrypt_string(ciphertext: str, password: str) -> str:
    key = derive_key(password)
    f = Fernet(key)
    plaintext = f.decrypt(ciphertext.encode())
    return plaintext.decode()

# Encrypted values (replace these with your real encrypted strings)
_encrypted_private_key = " use encrypt_string.py to make your code encrypted and put it here "
_encrypted_wallet_address = " use encrypt_string.py to make your code encrypted and put it here "


def get_keys():
    password = getpass.getpass("Enter your personal password: ")
    private_key = decrypt_string(_encrypted_private_key, password)
    wallet_address = decrypt_string(_encrypted_wallet_address, password)
    return wallet_address, private_key

if __name__ == "__main__":
    addr, key = get_keys()
    print("Decrypted wallet address:", addr)
    print("Decrypted private key:", key)