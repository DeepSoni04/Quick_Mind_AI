import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """Ensure key is a valid 32-byte url-safe base64 Fernet key."""
    raw_key = settings.ENCRYPTION_KEY.encode('utf-8')
    try:
        # Check if already a valid Fernet key
        Fernet(raw_key)
        return raw_key
    except Exception:
        # Hash into 32 bytes and url-safe base64 encode
        key = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
        return key


_fernet_instance = None


def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(_get_fernet_key())
    return _fernet_instance


def encrypt_secret(secret_text: str) -> str:
    """Encrypt secret text (e.g. database password) to ciphertext string."""
    if not secret_text:
        return ""
    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(secret_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt ciphertext string back to plaintext secret."""
    if not ciphertext:
        return ""
    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt database credential: {str(e)}")
