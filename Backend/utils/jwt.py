import jwt
from fastapi import Header, HTTPException
from core.config import settings


def extract_user_id_from_token(authorization: str = Header(...)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    token = authorization.split(" ")[1]
    try:
        claims = jwt.decode(token, settings.jwt_secret_key,
                            algorithms=[settings.jwt_algorithm])
        user_id = claims.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="user_id not found in token")
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Token decode error: {str(e)}")
