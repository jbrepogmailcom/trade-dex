import base64
import getpass
import hashlib
from cryptography.fernet import Fernet

def derive_key(password: str) -> bytes:
    # Derive a key from the password using SHA256 (without salt)
    sha = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(sha)

def encrypt_string(plaintext: str, password: str) -> str:
    key = derive_key(password)
    f = Fernet(key)
    ciphertext = f.encrypt(plaintext.encode())
    return ciphertext.decode()

def main():
    password = getpass.getpass("Enter password for encryption: ")
    plaintext = input("Enter string to encrypt: ")
    ciphertext = encrypt_string(plaintext, password)
    print("\nEncrypted string:")
    print(ciphertext)

if __name__ == "__main__":
    main()
