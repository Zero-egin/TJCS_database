"""
核心模块导出
"""
from app.core.config import (
    DATABASE_URL,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CORS_ORIGINS,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.core.deps import (
    get_db,
    get_current_user,
    get_current_active_user,
    require_admin,
    require_super_admin,
    require_operator_or_admin,
    require_permission,
    require_any_permission,
    require_role,
    require_roles,
    has_permission,
)

__all__ = [
    # config
    "DATABASE_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "CORS_ORIGINS",
    # security
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    # deps
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_super_admin",
    "require_operator_or_admin",
    "require_permission",
    "require_any_permission",
    "require_role",
    "require_roles",
    "has_permission",
]

