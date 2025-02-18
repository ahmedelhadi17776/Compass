from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from Backend.core.config import settings

# Get secret key from settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    print("🔑 Attempting password verification")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"🔐 Password verification {'succeeded' if result else 'failed'}")
        return result
    except Exception as e:
        print(f"🔴 Error during password verification: {str(e)}")
        return False


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    now = datetime.utcnow()
    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at time
        # Unique token ID with microseconds
        "jti": f"{now.timestamp()}.{now.microsecond}"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        exp: int = payload.get("exp")

        if not email or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            print("🔴 Token is invalid or expired")
            return None  # Token expired or invalid

        print("✅ Token Decoded Successfully:", payload)
        return payload
    except JWTError as e:
        print(f"🔴 JWT Error: {e}")
        return None
