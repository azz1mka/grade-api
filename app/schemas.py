from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str  # ← Обычный str вместо EmailStr
    password: str = Field(..., min_length=6)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Неверный формат email')
        return v.lower()


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str