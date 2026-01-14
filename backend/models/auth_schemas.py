"""
Authentication and Authorization schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    user_id: Optional[str] = None
    role: str = Field(default="user", description="User role")


class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserInfo(BaseModel):
    """User information"""
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)
