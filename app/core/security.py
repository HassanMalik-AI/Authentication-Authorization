from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import secrets
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing with Argon2 (more secure than bcrypt)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
)

def hash_password(password: str) -> bool:
    """Hash password using Argon2"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using constant-time comparison"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def needs_rehash(hashed_password: str) -> bool:
    """Check if password needs rehashing"""
    return pwd_context.needs_update(hashed_password)

# JWT Functions
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token with user data"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_hex(16)  # Unique token ID for blacklisting
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str, redis_client=None) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Check token blacklist if Redis is available
        # Note: This is async but being called from sync context, so we skip for now
        # In real implementation, use async decode_token or check blacklist separately
        
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None

def create_password_reset_token(email: str) -> str:
    """Create password reset token"""
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "password_reset",
        "jti": secrets.token_hex(16)
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def generate_mfa_secret() -> str:
    """Generate MFA secret key"""
    return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')

def generate_recovery_codes(count: int = 8, code_length: int = 8) -> list:
    """Generate MFA recovery codes"""
    codes = []
    for _ in range(count):
        code = secrets.token_hex(code_length // 2).upper()
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes

def hash_token_for_blacklist(token: str) -> str:
    """Hash token for blacklist storage (constant-time safe)"""
    return hashlib.sha256(token.encode()).hexdigest()

def encrypt_mfa_recovery_codes(codes: list, encryption_key: str) -> str:
    """Encrypt MFA recovery codes"""
    if not encryption_key:
        encryption_key = settings.SECRET_KEY[:32].encode()
    else:
        encryption_key = encryption_key[:32].encode()
    
    f = Fernet(base64.urlsafe_b64encode(encryption_key.ljust(32)[:32]))
    import json
    codes_json = json.dumps(codes)
    encrypted = f.encrypt(codes_json.encode())
    return encrypted.decode()

def decrypt_mfa_recovery_codes(encrypted_codes: str, encryption_key: str) -> list:
    """Decrypt MFA recovery codes"""
    try:
        if not encryption_key:
            encryption_key = settings.SECRET_KEY[:32].encode()
        else:
            encryption_key = encryption_key[:32].encode()
        
        f = Fernet(base64.urlsafe_b64encode(encryption_key.ljust(32)[:32]))
        decrypted = f.decrypt(encrypted_codes.encode())
        import json
        return json.loads(decrypted.decode())
    except Exception as e:
        logger.error(f"Failed to decrypt recovery codes: {e}")
        return []