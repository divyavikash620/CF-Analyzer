from typing import Any

from passlib.context import CryptContext

# Use bcrypt for hashing passwords
pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Returns the hashed password string suitable for storage.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hashed password.

    Returns True if the password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


__all__ = ["hash_password", "verify_password"]
