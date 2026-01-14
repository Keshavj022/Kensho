"""
Authentication and Authorization API routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from loguru import logger

from ..models.auth_schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserInfo,
    PasswordChangeRequest,
)
from ..services import auth_service, user_service
from ..dependencies import get_current_user, get_current_active_user, require_role

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    """
    try:
        # Register user in auth service
        auth_user = auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            user_id=user_data.user_id,
            role=user_data.role
        )

        # Create tokens
        tokens = auth_service.create_tokens(auth_user)

        # Store user in knowledge graph if available
        if user_service and hasattr(user_service, 'create_user'):
            # Create a basic user profile
            from ..models import User, UserProfile, DietaryInfo, UserPreferences, DietaryType
            user_profile = User(
                profile=UserProfile(
                    name=user_data.username,
                    location="",
                    age=None
                ),
                dietary=DietaryInfo(
                    type=DietaryType.NON_VEGETARIAN,
                    restrictions=[],
                    goals=[]
                ),
                preferences=UserPreferences()
            )
            user_service.create_user(auth_user["user_id"], user_profile)

        logger.info(f"User registered: {auth_user['username']}")

        return UserInfo(
            user_id=auth_user["user_id"],
            username=auth_user["username"],
            email=auth_user["email"],
            role=auth_user["role"],
            is_active=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login and get access token
    """
    try:
        # Authenticate user
        user_data = auth_service.authenticate_user(
            username=credentials.username,
            password=credentials.password
        )

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        tokens = auth_service.create_tokens(user_data)

        logger.info(f"User logged in: {user_data['username']}")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=1800  # 30 minutes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)

        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenResponse(
            access_token=tokens["access_token"],
            token_type=tokens["token_type"],
            expires_in=1800
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """
    Logout and revoke refresh tokens
    """
    try:
        # Revoke all refresh tokens for the user
        auth_service.revoke_all_tokens(current_user["user_id"])

        logger.info(f"User logged out: {current_user['username']}")

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """
    Get current user information
    """
    user_auth = auth_service.get_user_auth(current_user["user_id"])

    return UserInfo(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=user_auth.get("is_active", True) if user_auth else True
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user password
    """
    try:
        user_auth = auth_service.get_user_auth(current_user["user_id"])
        if not user_auth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not auth_service.verify_password(password_data.current_password, user_auth["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

        # Update password
        user_auth["hashed_password"] = auth_service.hash_password(password_data.new_password)
        auth_service._save_auth_data()

        # Revoke all tokens to force re-login
        auth_service.revoke_all_tokens(current_user["user_id"])

        logger.info(f"Password changed for user: {current_user['username']}")

        return {"message": "Password changed successfully. Please login again."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/users", response_model=list[UserInfo])
async def list_users(
    current_user: dict = Depends(require_role("admin"))
):
    """
    List all users (admin only)
    """
    try:
        users = []
        for user_id, user_auth in auth_service.users_auth.items():
            users.append(UserInfo(
                user_id=user_auth["user_id"],
                username=user_auth["username"],
                email=user_auth["email"],
                role=user_auth.get("role", "user"),
                is_active=user_auth.get("is_active", True)
            ))

        return users

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Update user role (admin only)
    """
    try:
        if role not in ["user", "admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user', 'admin', or 'moderator'"
            )

        success = auth_service.update_user_role(user_id, role)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"User role updated to {role}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Deactivate a user account (admin only)
    """
    try:
        success = auth_service.deactivate_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": "User deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Activate a user account (admin only)
    """
    try:
        success = auth_service.activate_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": "User activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )
