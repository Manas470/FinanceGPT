"""Auth schemas"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.ANALYST


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    company_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
