from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from core.security import (
    TEST_ACCOUNTS, USER_REGISTRY, get_password_hash, verify_password, create_access_token
)

router = APIRouter(tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters long")
    role: str = Field(default="user", description="One of: user, reporter, analyst, admin")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    email: str

class MessageResponse(BaseModel):
    message: str

@router.post("/auth/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """Registers a new user in the system (in-memory registry)."""
    valid_roles = ["user", "reporter", "analyst", "admin"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles are: {valid_roles}"
        )

    email_lower = user_data.email.lower()
    if email_lower in TEST_ACCOUNTS or email_lower in USER_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )

    # Save to user registry
    hashed_pwd = get_password_hash(user_data.password)
    USER_REGISTRY[email_lower] = {
        "password": hashed_pwd,
        "role": user_data.role
    }
    return {"message": "User registered successfully"}

@router.post("/auth/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    """Logs in user with JSON body credentials."""
    email_lower = login_data.email.lower()
    user_record = None
    
    if email_lower in TEST_ACCOUNTS:
        user_record = TEST_ACCOUNTS[email_lower]
    elif email_lower in USER_REGISTRY:
        user_record = USER_REGISTRY[email_lower]

    if not user_record or not verify_password(login_data.password, user_record["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": email_lower, "role": user_record["role"]}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user_record["role"],
        "email": email_lower
    }

@router.post("/auth/login/form", response_model=TokenResponse)
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Logs in user using form-data for OpenAPI/Swagger UI integration."""
    email_lower = form_data.username.lower()
    user_record = None
    
    if email_lower in TEST_ACCOUNTS:
        user_record = TEST_ACCOUNTS[email_lower]
    elif email_lower in USER_REGISTRY:
        user_record = USER_REGISTRY[email_lower]

    if not user_record or not verify_password(form_data.password, user_record["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": email_lower, "role": user_record["role"]}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user_record["role"],
        "email": email_lower
    }
