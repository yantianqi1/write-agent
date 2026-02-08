"""
WriteAgent API 服务入口

FastAPI应用主文件
"""

from fastapi import FastAPI
from dotenv import load_dotenv

# 加载环境变量（在导入其他模块之前）
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from .routers import (
    health_router,
    chat_router,
    projects_router,
    generation_router,
)
from .routers import chat_stream_router
from .database import init_db, close_db
from .middleware import add_timing_middleware
from .middleware.monitoring import MonitoringMiddleware, start_background_sampler
from .cache import get_cache
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.validation import SecurityHeadersMiddleware, ValidationMiddleware, ContentLengthMiddleware

# 创建FastAPI应用
app = FastAPI(
    title="WriteAgent API",
    description="AI小说创作助手后端API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# 中间件注册顺序（重要）:
# CORS → SecurityHeaders → ContentLength → Auth → RateLimit → Validation → Monitoring → Performance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全HTTP头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 内容长度限制中间件（10MB）
app.add_middleware(ContentLengthMiddleware, max_size=10 * 1024 * 1024)

# JWT认证中间件（可选启用，默认不强制要求）
require_auth = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
app.add_middleware(AuthMiddleware, require_auth=require_auth)

# 速率限制中间件
rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
if rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# 输入验证中间件
app.add_middleware(ValidationMiddleware)

# 添加性能监控中间件
add_timing_middleware(app, slow_query_threshold=1.0)

# 添加监控中间件（记录请求指标）
app.add_middleware(MonitoringMiddleware)

# 注册路由
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(chat_stream_router)  # 添加流式聊天路由
app.include_router(projects_router)
app.include_router(generation_router)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
        }
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    import logging
    logging.basicConfig(level=logging.INFO)
    print("🚀 WriteAgent API starting...")

    # 启动后台资源采样线程
    try:
        start_background_sampler(interval=1)
        print("✓ Monitoring sampler started")
    except Exception as e:
        print(f"⚠ Failed to start monitoring sampler: {e}")

    # 检查 Redis 连接（如果配置了）
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url and "redis" in redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            print("✓ Redis connection established")
        except Exception as e:
            print(f"⚠ Redis connection failed, falling back to memory cache: {e}")

    # 启动缓存自动清理任务
    try:
        cache = get_cache()
        cleanup_interval = int(os.getenv("CACHE_CLEANUP_INTERVAL", "300"))
        await cache.start_cleanup_task(interval_seconds=cleanup_interval)
        print("✓ Cache cleanup task started")
    except Exception as e:
        print(f"⚠ Failed to start cache cleanup task: {e}")

    # 初始化数据库
    try:
        await init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        raise


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("👋 WriteAgent API shutting down...")

    # 停止缓存清理任务
    try:
        cache = get_cache()
        await cache.stop_cleanup_task()
        print("✓ Cache cleanup task stopped")
    except Exception as e:
        print(f"⚠ Error stopping cache cleanup: {e}")

    # 关闭数据库连接
    try:
        await close_db()
        print("✓ Database connection closed")
    except Exception as e:
        print(f"✗ Error closing database: {e}")


if __name__ == "__main__":
    import uvicorn
    import yaml

    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            api_config = config.get("api", {})
            host = api_config.get("host", "0.0.0.0")
            port = api_config.get("port", 8000)
            reload = api_config.get("reload", True)
    except:
        host = "0.0.0.0"
        port = 8000
        reload = True

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )
