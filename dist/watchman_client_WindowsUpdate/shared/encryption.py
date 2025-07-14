"""
Shared encryption utilities for secure communication between client and server.
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib
import os

class EncryptionManager:
    def __init__(self, password=None):
        """Initialize encryption with password or generate key"""
        if password:
            self.key = self._derive_key_from_password(password)
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from password"""
        password_bytes = password.encode('utf-8')
        salt = hashlib.sha256(password_bytes).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        encrypted = self.cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    
    def get_key_string(self) -> str:
        """Get base64 encoded key string"""
        return base64.urlsafe_b64encode(self.key).decode('utf-8')

def obfuscate_string(text: str, shift: int = 13) -> str:
    """Simple string obfuscation using Caesar cipher"""
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        else:
            result += char
    return result

def deobfuscate_string(text: str, shift: int = 13) -> str:
    """Reverse string obfuscation"""
    return obfuscate_string(text, -shift)
