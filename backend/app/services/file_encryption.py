import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet:
    # Derive a 32-byte URL-safe base64-encoded key from SECRET_KEY
    key_material = settings.SECRET_KEY.encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return Fernet(key)

def encrypt_bytes(data: bytes) -> bytes:
    return get_fernet().encrypt(data)

def decrypt_bytes(data: bytes) -> bytes:
    return get_fernet().decrypt(data)
