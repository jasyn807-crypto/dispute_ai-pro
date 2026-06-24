import hashlib
from datetime import datetime, timedelta, timezone
from typing import Union
import jwt
import bcrypt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Pre-hash the password using SHA-256 hexdigest to fit within bcrypt's 72-byte limit
        pwd_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        pwd_bytes = pwd_hash.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        if bcrypt.checkpw(pwd_bytes, hashed_bytes):
            return True
    except Exception:
        pass

    try:
        # Backward compatibility fallback for passwords hashed without pre-hashing
        raw_pwd_bytes = plain_password.encode('utf-8')
        if len(raw_pwd_bytes) <= 72:
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(raw_pwd_bytes, hashed_bytes)
    except Exception:
        pass

    return False

def get_password_hash(password: str) -> str:
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    pwd_bytes = pwd_hash.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
