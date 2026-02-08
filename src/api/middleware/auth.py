"""
JWT认证中间件

提供JWT令牌创建、验证和用户认证功能
"""

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import logging

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "write-agent-secret-key-change-in-production"  # 应从环境变量读取
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


class TokenPayload:
    """JWT令牌载荷"""

    def __init__(self, user_id: str, **extra_data):
        self.user_id = user_id
        self.extra_data = extra_data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {"sub": self.user_id}
        data.update(self.extra_data)
        return data


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    创建JWT访问令牌

    Args:
        user_id: 用户ID
        expires_delta: 过期时间增量，默认7天
        extra_data: 额外的载荷数据

    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    if extra_data:
        payload.update(extra_data)

    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    验证并解码JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的载荷字典

    Raises:
        HTTPException: 令牌无效或已过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Expired token used")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def refresh_access_token(token: str) -> str:
    """
    刷新访问令牌

    Args:
        token: 原令牌

    Returns:
        新的JWT令牌
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    extra_data = {k: v for k, v in payload.items() if k not in ["sub", "exp", "iat", "type"]}
    return create_access_token(user_id, extra_data=extra_data)


# 安全实例，用于依赖注入
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    依赖注入：获取当前认证用户

    用法:
        @router.get("/protected")
        async def protected_route(current_user: Dict = Depends(get_current_user)):
            if not current_user:
                raise HTTPException(401, "Not authenticated")
            ...

    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭证

    Returns:
        用户信息字典，未认证时返回None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id:
            return {
                "id": user_id,
                "token_payload": payload,
            }
    except HTTPException:
        pass

    return None


async def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    依赖注入：要求用户必须认证

    用法:
        @router.get("/protected")
        async def protected_route(user: Dict = Depends(require_auth)):
            ...

    Args:
        current_user: 当前用户（可选）

    Returns:
        用户信息字典

    Raises:
        HTTPException: 用户未认证
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT认证中间件

    可选择性应用于路由，默认不强制要求认证
    可通过环境变量或配置启用全局认证

    中间件会将解码的用户信息存储在 request.state.user 中
    """

    def __init__(
        self,
        app: ASGIApp,
        require_auth: bool = False,
        exclude_paths: Optional[list[str]] = None,
    ):
        """
        初始化认证中间件

        Args:
            app: ASGI应用
            require_auth: 是否要求全局认证（默认False）
            exclude_paths: 排除的路径（无需认证的路径）
        """
        super().__init__(app)
        self.require_auth = require_auth
        self.exclude_paths = set(exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
        ])

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，验证JWT令牌

        将用户信息存储在 request.state.user 中
        """
        path = request.url.path

        # 检查是否排除路径
        if path in self.exclude_paths:
            return await call_next(request)

        # 获取Authorization头
        auth_header = request.headers.get("Authorization")

        user = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 移除 "Bearer " 前缀
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                user = {
                    "id": user_id,
                    "token_payload": payload,
                }
            except HTTPException as e:
                # 如果要求认证但令牌无效，返回错误
                if self.require_auth:
                    return JSONResponse(
                        status_code=e.status_code,
                        content={"detail": e.detail},
                    )

        # 如果要求认证但无用户，返回401
        if self.require_auth and user is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
            )

        # 将用户信息存储在request.state中
        request.state.user = user

        return await call_next(request)


def require_auth_decorator(require: bool = True):
    """
    路由认证装饰器

    用法:
        @router.get("/protected")
        @require_auth_decorator()
        async def protected_route(request: Request):
            user = request.state.user
            ...

        @router.get("/optional")
        @require_auth_decorator(require=False)
        async def optional_route(request: Request):
            user = request.state.user
            ...

    Args:
        require: 是否要求认证
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 尝试从kwargs获取request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            for value in kwargs.values():
                if isinstance(value, Request):
                    request = value
                    break

            if request:
                user = getattr(request.state, "user", None)
                if require and user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "create_access_token",
    "decode_token",
    "refresh_access_token",
    "get_current_user",
    "require_auth",
    "AuthMiddleware",
    "require_auth_decorator",
    "security",
]
