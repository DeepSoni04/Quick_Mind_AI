from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt with 72 byte truncation safeguard."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


import secrets
import string
import re


def generate_temp_password(length: int = 14) -> str:
    """Generate a high-entropy temporary password for password resets."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least 1 lower, 1 upper, 1 digit, 1 symbol
    pwd = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    pwd += [secrets.choice(alphabet) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


def sanitize_sensitive_text(text: str, known_secrets: Optional[list] = None) -> str:
    """Scrub passwords, tokens, connection URIs, and credentials from text before logging or returning to client."""
    if not text:
        return ""
    
    sanitized = text
    if known_secrets:
        for s in known_secrets:
            if s and len(str(s)) > 1:
                sanitized = sanitized.replace(str(s), "******")
                
    # Mask passwords in connection URIs like mysql://user:pass@host:port/db
    sanitized = re.sub(r'://([^:]+):([^@]+)@', r'://\1:******@', sanitized)
    # Mask password=... or pwd=...
    sanitized = re.sub(r'(password|pwd|secret|token|api_key)=([^\s;&,]+)', r'\1=******', sanitized, flags=re.IGNORECASE)
    # Mask Bearer tokens
    sanitized = re.sub(r'Bearer\s+[A-Za-z0-9\-_.]+', 'Bearer ******', sanitized)
    return sanitized
