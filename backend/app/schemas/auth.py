from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

from ..utils.validation import validate_username, validate_email, validate_password

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    
    @validator('username')
    def validate_username_format(cls, v):
        return validate_username(v)
    
    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(str(v))
    
    @validator('password')
    def validate_password_strength(cls, v):
        return validate_password(v)
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 100:
                raise ValueError("Display name too long (max 100 characters)")
        return v

class UserLogin(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def validate_username_format(cls, v):
        # For login, be more permissive but still sanitize
        if not isinstance(v, str):
            raise ValueError("Username must be a string")
        return v.strip().lower()

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
