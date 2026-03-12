import base64
import hashlib
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from spirit.core.config import settings


class EncryptionService:
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = base64.urlsafe_b64decode(key)
        elif settings.ENCRYPTION_KEY:
            self.key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY)
        else:
            self.key = self._generate_key()
        self.cipher = Fernet(self.key)
    
    @staticmethod
    def _generate_key() -> bytes:
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt(self, plaintext: str) -> str:
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        decoded = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
    
    def get_key_for_storage(self) -> str:
        return base64.urlsafe_b64encode(self.key).decode()


encryption_service = EncryptionService()
