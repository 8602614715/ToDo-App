"""
Role-Based Access Control (RBAC) utilities
"""
from functools import wraps
from fastapi import HTTPException, Depends
from typing import Annotated, List, Optional
from ToDoApp.routers.auth import get_current_user

# Define role hierarchy
ROLE_HIERARCHY = {
    "superuser": 4,
    "admin": 3,
    "manager": 2,
    "user": 1,
    "guest": 0
}

def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific roles for access
    Usage: @require_role(["admin", "manager"])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find user_dependency in kwargs
            user = None
            for key, value in kwargs.items():
                if isinstance(value, dict) and "user_role" in value:
                    user = value
                    break
            
            if not user:
                # Try to get from dependencies
                for arg in args:
                    if isinstance(arg, dict) and "user_role" in arg:
                        user = arg
                        break
            
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_role = user.get("user_role", "").lower()
            
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_min_role(min_role: str):
    """
    Decorator to require minimum role level
    Usage: @require_min_role("manager")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for key, value in kwargs.items():
                if isinstance(value, dict) and "user_role" in value:
                    user = value
                    break
            
            if not user:
                for arg in args:
                    if isinstance(arg, dict) and "user_role" in arg:
                        user = arg
                        break
            
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_role = user.get("user_role", "").lower()
            min_level = ROLE_HIERARCHY.get(min_role.lower(), 0)
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            
            if user_level < min_level:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Minimum role required: {min_role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_role_access(user: dict, required_roles: List[str]) -> bool:
    """Check if user has one of the required roles"""
    user_role = user.get("user_role", "").lower()
    return user_role in [r.lower() for r in required_roles]


def check_min_role(user: dict, min_role: str) -> bool:
    """Check if user has minimum role level"""
    user_role = user.get("user_role", "").lower()
    min_level = ROLE_HIERARCHY.get(min_role.lower(), 0)
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    return user_level >= min_level


def get_user_role(user: dict) -> str:
    """Get user role from user dict"""
    return user.get("user_role", "user").lower()


def is_admin(user: dict) -> bool:
    """Check if user is admin or superuser"""
    role = get_user_role(user)
    return role in ["admin", "superuser"]


def is_manager_or_above(user: dict) -> bool:
    """Check if user is manager or above"""
    return check_min_role(user, "manager")
