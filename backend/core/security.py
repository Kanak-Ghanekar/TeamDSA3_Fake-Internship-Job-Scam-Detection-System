import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

JWT_SECRET_KEY = "92e3c04de84b6389a0715cf4b6480e72251a31d8e1bb18b6e6eb7b4cfbfbf9f7"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# In-memory user class representation
class User(BaseModel):
    email: str
    role: str

# In-memory database of test users
TEST_ACCOUNTS = {
    "admin@scamdetector.com": {"password": "admin123", "role": "admin"},
    "analyst@scamdetector.com": {"password": "analyst123", "role": "analyst"},
    "reporter@scamdetector.com": {"password": "reporter123", "role": "reporter"},
    "user@scamdetector.com": {"password": "user123", "role": "user"}
}

# Dynamic registry to allow register route to add users at runtime
USER_REGISTRY = {}

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        hashed_plain = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return hashed_plain == hashed_password or plain_password == hashed_password
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
        
    role = payload.get("role", "user")
    
    if email in TEST_ACCOUNTS or email in USER_REGISTRY:
        return User(email=email, role=role)
    else:
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {self.allowed_roles}",
            )
        return current_user

require_admin = RoleChecker(["admin"])
require_analyst = RoleChecker(["admin", "analyst"])
require_reporter = RoleChecker(["admin", "analyst", "reporter"])
require_user = RoleChecker(["admin", "analyst", "reporter", "user"])
