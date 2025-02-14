from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# Secret key for signing JWT tokens
SECRET_KEY = "a82552a2c8133eddce94cc781f716cdcb911d065528783a8a75256aff6731886"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token expiry time

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
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
