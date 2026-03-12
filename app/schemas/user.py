from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# --- Request Schemas ---

class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, examples=["user@example.com"])
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255, examples=["John Doe"])


class UserLogin(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(...)


# --- Response Schemas ---

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
