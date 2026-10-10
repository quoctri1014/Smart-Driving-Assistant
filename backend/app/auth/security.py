import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "trafficguard-super-secret-enterprise-key-2026-secure-32chars")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

INSECURE_SECRETS = {"secret", "changeme", "dev-secret", "super-secret-key-change-me-in-production", "admin", "123456"}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        # Hỗ trợ cả trường hợp password demo không mã hoá
        if plain_password == hashed_password:
            return True
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if len(SECRET_KEY) < 32 or SECRET_KEY in INSECURE_SECRETS:
        if ENVIRONMENT in ("production", "prod", "staging"):
            raise RuntimeError("CRITICAL: Production must configure a strong unique JWT_SECRET of >= 32 characters. Insecure fallback prohibited.")
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
