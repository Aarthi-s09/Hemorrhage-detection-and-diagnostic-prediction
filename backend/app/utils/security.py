"""
Security Utilities - Authentication dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole


# HTTP Bearer security scheme - AUTO AUTH enabled (no tokens required)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user - AUTO AUTH enabled for development"""
    # Authentication disabled - return mock user based on any identifier
    # You can pass a header like X-User-Role to switch between doctor/radiologist
    
    # Check if there's a default user, create if not
    user = db.query(User).filter(User.email == "doctor@test.com").first()
    if not user:
        # Create default doctor user
        from app.schemas.user import UserCreate
        user_data = UserCreate(
            email="doctor@test.com",
            password="Test123456",
            full_name="Development Doctor",
            role="doctor"
        )
        user = AuthService.create_user(db, user_data)
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_roles: list[UserRole]):
    """Dependency factory for role-based access control"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_radiologist(current_user: User = Depends(get_current_active_user)) -> User:
    """Require radiologist role - DISABLED for development"""
    # Role check disabled for development
    return current_user


def require_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    """Require doctor role - DISABLED for development"""
    # Role check disabled for development
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role - DISABLED for development"""
    # Role check disabled for development
    return current_user
