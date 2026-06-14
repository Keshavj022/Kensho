"""Auth routes — register/login/refresh/logout/me, profile, and admin user ops."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from ..dependencies import get_current_active_user, get_current_user, require_role
from ..models.auth_schemas import (
    PasswordChangeRequest,
    ProfileInfo,
    ProfilePayload,
    RefreshTokenRequest,
    TokenResponse,
    UserInfo,
    UserLogin,
    UserRegister,
)
from ..services.auth_service import auth_service
from ..services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    try:
        auth_user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
        )
        auth_service.create_tokens(auth_user)  # issue + store a refresh token
        return UserInfo(
            user_id=auth_user["user_id"],
            username=auth_user["username"],
            email=auth_user["email"],
            role=auth_user["role"],
            is_active=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")


@router.get("/check-email")
async def check_email(email: str = Query(..., description="Email to check")):
    """Whether an email is already registered (used by onboarding)."""
    return {"email": email, "available": not auth_service.email_exists(email)}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_data = auth_service.authenticate_user(credentials.email, credentials.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = auth_service.create_tokens(user_data)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=60 * 30,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    tokens = auth_service.refresh_access_token(request.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=tokens["access_token"], token_type=tokens["token_type"], expires_in=60 * 30)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
):
    auth_service.revoke_all_tokens(current_user["user_id"])
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    user_auth = auth_service.get_user_auth(current_user["user_id"])
    return UserInfo(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=user_auth.get("is_active", True) if user_auth else True,
    )


@router.get("/profile", response_model=ProfileInfo)
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    """Full diet/demographic profile for the signed-in user."""
    return ProfileInfo(**user_service.get_profile_dict(current_user["user_id"]))


@router.put("/profile", response_model=ProfileInfo)
async def update_profile(payload: ProfilePayload, current_user: dict = Depends(get_current_active_user)):
    """Save onboarding / profile edits (persists + bridges to Neo4j)."""
    saved = user_service.save_profile(current_user["user_id"], payload.model_dump())
    return ProfileInfo(**saved)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_active_user),
):
    ok = auth_service.change_password(
        current_user["user_id"], password_data.current_password, password_data.new_password
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    return {"message": "Password changed successfully. Please login again."}


@router.get("/users", response_model=list[UserInfo])
async def list_users(current_user: dict = Depends(require_role("admin"))):
    return [UserInfo(**u) for u in auth_service.list_users()]


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, current_user: dict = Depends(require_role("admin"))):
    if role not in ("user", "admin", "moderator"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if not auth_service.update_user_role(user_id, role):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    if not auth_service.deactivate_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deactivated successfully"}


@router.put("/users/{user_id}/activate")
async def activate_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    if not auth_service.activate_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User activated successfully"}
