"""
Authentication and Authorization schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """User registration request (email is the identity — no username)."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    role: str = Field(default="user", description="User role")


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="Email address")
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


class ProfilePayload(BaseModel):
    """Onboarding / profile-update payload (flat, frontend-friendly)."""
    name: str = ""
    dob: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    location: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    dietary_type: str = "non-vegetarian"
    spice_tolerance: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)


class ProfileInfo(ProfilePayload):
    """Profile as returned to the client."""
    user_id: str = ""
    onboarded: bool = False
