from datetime import datetime, timedelta, timezone
import os
import secrets

from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import Employee, Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKEN_STORE: dict[str, tuple[int, datetime]] = {}
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(employee_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    TOKEN_STORE[token] = (employee_id, expires_at)
    return token


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Employee:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization.split(" ", 1)[1]
    token_record = TOKEN_STORE.get(token)
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    employee_id, expires_at = token_record
    if expires_at < datetime.now(timezone.utc):
        TOKEN_STORE.pop(token, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    user = db.get(Employee, employee_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: Role):
    def dependency(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        return current_user

    return dependency
