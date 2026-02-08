"""
输入验证与安全头中间件

提供XSS防护、输入验证和安全HTTP头设置
"""

import re
import html
import logging
from typing import Optional, Set, List, Any
from urllib.parse import urlunparse

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class InputValidator:
    """
    输入验证工具类

    提供字符串清理、XSS检测等功能
    """

    # XSS攻击模式
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<img[^>]*onerror',
        r'<svg[^>]*>.*?</svg>',
        r'eval\s*\(',
        r'expr\s*ession',
        r'@import',
    ]

    # 编译正则表达式
    _xss_regex = re.compile(
        '|'.join(XSS_PATTERNS),
        re.IGNORECASE | re.DOTALL
    )

    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"(\bor\b|\band\b).*=.*\bor\b|\band\b",
        r";\s*(drop|delete|insert|update|exec|execute)",
        r"\bunion\s+select\b",
        r"\bselect\b.*\bfrom\b",
    ]

    _sql_injection_regex = re.compile(
        '|'.join(SQL_INJECTION_PATTERNS),
        re.IGNORECASE | re.DOTALL
    )

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """
        清理字符串输入

        Args:
            value: 原始字符串
            max_length: 最大长度限制

        Returns:
            清理后的字符串
        """
        if not isinstance(value, str):
            return ""

        # 截断过长字符串
        if len(value) > max_length:
            value = value[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")

        # 移除null字节
        value = value.replace('\x00', '')

        # HTML转义（如果包含HTML实体）
        if '<' in value or '>' in value:
            value = html.escape(value)

        return value.strip()

    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """
        检测输入是否包含XSS攻击代码

        Args:
            value: 待检测字符串

        Returns:
            True表示检测到XSS攻击
        """
        if not isinstance(value, str):
            return False

        # 使用正则表达式检测
        if cls._xss_regex.search(value):
            logger.warning(f"XSS pattern detected in input: {value[:100]}...")
            return True

        return False

    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        检测输入是否包含SQL注入攻击

        Args:
            value: 待检测字符串

        Returns:
            True表示检测到SQL注入
        """
        if not isinstance(value, str):
            return False

        if cls._sql_injection_regex.search(value):
            logger.warning(f"SQL injection pattern detected: {value[:100]}...")
            return True

        return False

    @classmethod
    def validate_message_content(cls, content: str, max_length: int = 50000) -> str:
        """
        验证聊天消息内容

        Args:
            content: 消息内容
            max_length: 最大长度

        Returns:
            清理后的内容

        Raises:
            HTTPException: 检测到恶意内容时
        """
        if not isinstance(content, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content must be a string",
            )

        content = content.strip()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty",
            )

        if len(content) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message content exceeds maximum length of {max_length}",
            )

        # XSS检测
        if cls.detect_xss(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content contains potentially malicious code",
            )

        return content

    @classmethod
    def validate_project_name(cls, name: str) -> str:
        """验证项目名称"""
        name = cls.sanitize_string(name, max_length=200)

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name cannot be empty",
            )

        return name

    @classmethod
    def validate_chapter_content(cls, content: str, max_length: int = 100000) -> str:
        """验证章节内容"""
        if not isinstance(content, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chapter content must be a string",
            )

        content = content.strip()

        if len(content) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chapter content exceeds maximum length of {max_length}",
            )

        # 基本XSS检测
        if cls.detect_xss(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chapter content contains potentially malicious code",
            )

        return content

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """验证URL格式"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @classmethod
    def sanitize_dict(cls, data: dict, max_depth: int = 5) -> dict:
        """
        递归清理字典中的所有字符串值

        Args:
            data: 输入字典
            max_depth: 最大递归深度

        Returns:
            清理后的字典
        """
        def _sanitize(value: Any, depth: int) -> Any:
            if depth > max_depth:
                return None

            if isinstance(value, str):
                return cls.sanitize_string(value)
            elif isinstance(value, dict):
                return {
                    k: _sanitize(v, depth + 1)
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                return [_sanitize(item, depth + 1) for item in value]
            else:
                return value

        return _sanitize(data, 0)


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    输入验证中间件

    自动验证请求体中的输入，检测XSS和注入攻击
    """

    # 不需要验证的路径
    EXCLUDE_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/health",
    }

    # 不需要验证的Content-Type
    EXCLUDE_CONTENT_TYPES = {
        "multipart/form-data",
    }

    def __init__(
        self,
        app: ASGIApp,
        validator: Optional[InputValidator] = None,
        exclude_paths: Optional[Set[str]] = None,
    ):
        """
        初始化验证中间件

        Args:
            app: ASGI应用
            validator: 输入验证器实例
            exclude_paths: 排除的路径
        """
        super().__init__(app)
        self.validator = validator or InputValidator()
        self.exclude_paths = exclude_paths or self.EXCLUDE_PATHS

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，验证输入
        """
        path = request.url.path

        # 跳过排除的路径
        if path in self.exclude_paths:
            return await call_next(request)

        # 跳过特定Content-Type
        content_type = request.headers.get("content-type", "")
        if any(excluded in content_type for excluded in self.EXCLUDE_CONTENT_TYPES):
            return await call_next(request)

        # 对于POST/PUT/PATCH请求，读取并验证请求体
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                # 读取请求体
                body = await request.body()

                # 解析JSON（如果是JSON格式）
                if "application/json" in content_type:
                    import json
                    try:
                        data = json.loads(body.decode())
                        # 递归验证字典
                        sanitized = self.validator.sanitize_dict(data)

                        # 如果检测到变化，替换请求体
                        if sanitized != data:
                            # 创建新的请求对象
                            from fastapi import Request
                            modified_body = json.dumps(sanitized).encode()
                            request._body = modified_body
                    except json.JSONDecodeError:
                        pass  # 不是有效的JSON，跳过
            except Exception as e:
                logger.warning(f"Validation error: {e}")
                # 不阻止请求，只记录警告

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全HTTP头中间件

    添加各种安全相关的HTTP响应头
    """

    # 默认安全头
    DEFAULT_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        ),
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    }

    def __init__(
        self,
        app: ASGIApp,
        headers: Optional[dict] = None,
        csp_enabled: bool = True,
        hsts_enabled: bool = True,
    ):
        """
        初始化安全头中间件

        Args:
            app: ASGI应用
            headers: 自定义安全头（与默认头合并）
            csp_enabled: 是否启用CSP（开发环境可能需要关闭）
            hsts_enabled: 是否启用HSTS（HTTPS环境下）
        """
        super().__init__(app)
        self.headers = {**self.DEFAULT_HEADERS, **(headers or {})}

        # 根据配置调整头
        if not csp_enabled:
            self.headers.pop("Content-Security-Policy", None)
        if not hsts_enabled:
            self.headers.pop("Strict-Transport-Security", None)

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，添加安全头
        """
        response = await call_next(request)

        # 添加安全头
        for key, value in self.headers.items():
            response.headers[key] = value

        return response


class CORSSecurityMiddleware:
    """
    CORS安全配置辅助类

    提供更严格的CORS配置建议
    """

    @staticmethod
    def get_allowed_origins(env: str = "development") -> list[str]:
        """
        获取允许的来源

        Args:
            env: 环境 (development, staging, production)

        Returns:
            允许的来源列表
        """
        if env == "production":
            # 生产环境应该使用具体域名
            return [
                "https://yourdomain.com",
                "https://www.yourdomain.com",
            ]
        elif env == "staging":
            return [
                "https://staging.yourdomain.com",
            ]
        else:
            # 开发环境
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ]

    @staticmethod
    def get_cors_config(env: str = "development") -> dict:
        """
        获取CORS配置

        Args:
            env: 环境名称

        Returns:
            CORS配置字典
        """
        return {
            "allow_origins": CORSecurityMiddleware.get_allowed_origins(env),
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "X-Request-ID",
            ],
            "max_age": 600,  # 预检请求缓存时间
        }


class ContentLengthMiddleware(BaseHTTPMiddleware):
    """
    内容长度限制中间件

    防止过大的请求体
    """

    def __init__(
        self,
        app: ASGIApp,
        max_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """
        初始化内容长度中间件

        Args:
            app: ASGI应用
            max_size: 最大请求体大小（字节）
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """
        检查请求体大小
        """
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request entity too large",
                            "message": f"Request body exceeds maximum size of {self.max_size} bytes",
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)


__all__ = [
    "InputValidator",
    "ValidationMiddleware",
    "SecurityHeadersMiddleware",
    "CORSecurityMiddleware",
    "ContentLengthMiddleware",
]
