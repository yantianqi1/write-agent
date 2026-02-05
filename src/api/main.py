"""
WriteAgent API 服务入口

FastAPI应用主文件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from .routers import (
    health_router,
    chat_router,
    projects_router,
    generation_router,
)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(chat_router)
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


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("👋 WriteAgent API shutting down...")


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
