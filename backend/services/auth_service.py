"""
Authentication and Authorization Service
Handles user authentication, JWT tokens, and password management
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger

from ..config import settings
from .knowledge_graph_service import knowledge_graph_service

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration - Use settings
from ..config import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS


class AuthService:
    """Service for authentication and authorization"""

    def __init__(self):
        """Initialize auth service"""
        self.users_auth_file = os.path.join(settings.DATA_DIR, "users_auth.json")
        self.users_auth: Dict[str, Dict[str, Any]] = {}
        self._load_auth_data()

    def _load_auth_data(self):
        """Load authentication data from file"""
        try:
            if os.path.exists(self.users_auth_file):
                with open(self.users_auth_file, "r") as f:
                    self.users_auth = json.load(f)
                logger.info(f"Loaded {len(self.users_auth)} user authentication records")
            else:
                logger.info("No existing auth data file found")
        except Exception as e:
            logger.error(f"Error loading auth data: {str(e)}")
            self.users_auth = {}

    def _save_auth_data(self):
        """Save authentication data to file"""
        try:
            os.makedirs(settings.DATA_DIR, exist_ok=True)
            with open(self.users_auth_file, "w") as f:
                json.dump(self.users_auth, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auth data: {str(e)}")

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return None

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        user_id: Optional[str] = None,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Register a new user"""
        # Check if username or email already exists
        for user_data in self.users_auth.values():
            if user_data.get("username") == username:
                raise ValueError("Username already exists")
            if user_data.get("email") == email:
                raise ValueError("Email already exists")

        # Generate user_id if not provided
        if not user_id:
            user_id = f"user_{len(self.users_auth) + 1}_{int(datetime.utcnow().timestamp())}"

        # Hash password
        hashed_password = self.hash_password(password)

        # Create user auth record
        user_auth = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "refresh_tokens": []
        }

        self.users_auth[user_id] = user_auth
        self._save_auth_data()

        logger.info(f"User registered: {username} ({user_id})")

        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "role": role
        }

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user"""
        # Find user by username or email
        user_auth = None
        for user_data in self.users_auth.values():
            if user_data.get("username") == username or user_data.get("email") == username:
                user_auth = user_data
                break

        if not user_auth:
            logger.warning(f"User not found: {username}")
            return None

        if not user_auth.get("is_active", True):
            logger.warning(f"User account is inactive: {username}")
            return None

        # Verify password
        if not self.verify_password(password, user_auth["hashed_password"]):
            logger.warning(f"Invalid password for user: {username}")
            return None

        return {
            "user_id": user_auth["user_id"],
            "username": user_auth["username"],
            "email": user_auth["email"],
            "role": user_auth.get("role", "user")
        }

    def create_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create access and refresh tokens for a user"""
        token_data = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data.get("role", "user")
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        # Store refresh token
        user_id = user_data["user_id"]
        if user_id in self.users_auth:
            if "refresh_tokens" not in self.users_auth[user_id]:
                self.users_auth[user_id]["refresh_tokens"] = []
            self.users_auth[user_id]["refresh_tokens"].append(refresh_token)
            self._save_auth_data()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh an access token using a refresh token"""
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id or user_id not in self.users_auth:
            return None

        # Verify refresh token is in user's token list
        user_auth = self.users_auth[user_id]
        if refresh_token not in user_auth.get("refresh_tokens", []):
            logger.warning(f"Refresh token not found for user: {user_id}")
            return None

        # Create new access token
        token_data = {
            "sub": user_id,
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }

        access_token = self.create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    def revoke_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Revoke a refresh token"""
        if user_id not in self.users_auth:
            return False

        refresh_tokens = self.users_auth[user_id].get("refresh_tokens", [])
        if refresh_token in refresh_tokens:
            refresh_tokens.remove(refresh_token)
            self.users_auth[user_id]["refresh_tokens"] = refresh_tokens
            self._save_auth_data()
            return True

        return False

    def revoke_all_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user"""
        if user_id not in self.users_auth:
            return False

        self.users_auth[user_id]["refresh_tokens"] = []
        self._save_auth_data()
        return True

    def get_user_auth(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user authentication data"""
        return self.users_auth.get(user_id)

    def update_user_role(self, user_id: str, role: str) -> bool:
        """Update user role"""
        if user_id not in self.users_auth:
            return False

        self.users_auth[user_id]["role"] = role
        self._save_auth_data()
        return True

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        if user_id not in self.users_auth:
            return False

        self.users_auth[user_id]["is_active"] = False
        self.revoke_all_tokens(user_id)
        self._save_auth_data()
        return True

    def activate_user(self, user_id: str) -> bool:
        """Activate a user account"""
        if user_id not in self.users_auth:
            return False

        self.users_auth[user_id]["is_active"] = True
        self._save_auth_data()
        return True


# Global auth service instance
auth_service = AuthService()
