from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

_pwd = CryptContext(schemes=["bcrypt"])
_bearer = HTTPBearer()

def hash_password(p: str) -> str: return _pwd.hash(p)
def verify_password(p: str, h: str) -> bool: return _pwd.verify(p, h)

def make_token(user_id: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_min)
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, settings.jwt_secret, "HS256")

def decode_token(token: str) -> dict:
    try:
        claims = jwt.decode(token, settings.jwt_secret, ["HS256"])
        claims["sub"] = UUID(claims["sub"])
        return claims
    except JWTError: raise HTTPException(401, "Invalid token")
    except (ValueError, TypeError): raise HTTPException(401, "Invalid token")

def current_user(cred=Depends(_bearer)) -> dict:
    return decode_token(cred.credentials)

def require_admin(user=Depends(current_user)) -> dict:
    if user["role"] != "ADMIN": raise HTTPException(403, "Admin only")
    return user

def require_participant(user=Depends(current_user)) -> dict:
    if user["role"] != "PARTICIPANT": raise HTTPException(403, "Participants only")
    return user
