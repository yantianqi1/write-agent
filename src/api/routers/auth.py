"""
认证路由

提供用户登录、令牌刷新等认证相关API
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..middleware.auth import create_access_token, refresh_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# ============================================================
# 请求/响应模型
# ============================================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求（简化版本）"""
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user_id: str


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    token: str


# ============================================================
# 简化的用户存储（生产环境应使用数据库）
# ============================================================

# 简化版本：硬编码一个测试用户
# 生产环境应该使用数据库存储用户信息
DEMO_USERS = {
    "admin": {
        "id": "user_admin",
        "username": "admin",
        # 密码: admin123 (实际应用中应该使用哈希)
        "password": "admin123",
    },
    "demo": {
        "id": "user_demo",
        "username": "demo",
        # 密码: demo123
        "password": "demo123",
    },
}


def verify_user(username: str, password: str) -> Dict[str, Any] | None:
    """
    验证用户凭据

    Args:
        username: 用户名
        password: 密码

    Returns:
        用户信息字典，验证失败返回 None
    """
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return {
            "id": user["id"],
            "username": user["username"],
        }
    return None


# ============================================================
# API 端点
# ============================================================

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest) -> TokenResponse:
    """
    用户登录

    使用用户名和密码换取访问令牌

    - **username**: 用户名
    - **password**: 密码

    返回包含访问令牌的响应
    """
    user = verify_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = create_access_token(
        user_id=user["id"],
        extra_data={"username": user["username"]},
    )

    logger.info(f"User logged in: {user['username']}")

    # 计算过期时间（秒）
    from ..middleware.auth import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expires_in = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=user["id"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest) -> TokenResponse:
    """
    刷新访问令牌

    使用有效令牌获取新的访问令牌

    - **token**: 当前有效的访问令牌
    """
    try:
        new_token = refresh_access_token(data.token)

        # 计算过期时间（秒）
        from ..middleware.auth import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        expires_in = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # 解析用户 ID
        import jwt
        from ..middleware.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        payload = jwt.decode(new_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub", "")

        return TokenResponse(
            access_token=new_token,
            token_type="bearer",
            expires_in=expires_in,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
        )


@router.post("/verify")
async def verify_token(token: str) -> Dict[str, Any]:
    """
    验证令牌有效性

    返回令牌包含的用户信息
    """
    from ..middleware.auth import decode_token

    try:
        payload = decode_token(token)
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "expires_at": payload.get("exp"),
        }
    except HTTPException:
        return {
            "valid": False,
            "error": "令牌无效或已过期",
        }


@router.get("/me")
async def get_current_user_info() -> Dict[str, Any]:
    """
    获取当前用户信息

    需要认证，返回当前登录用户的信息
    """
    # 这个端点通过中间件或依赖注入获取用户
    # 简化版本返回演示信息
    return {
        "message": "使用 Bearer 令牌访问受保护的端点",
        "demo_users": list(DEMO_USERS.keys()),
    }


__all__ = ["router"]
