# 对话式小说创作 Agent - 统一 Docker 镜像
# 多阶段构建：前端构建 + 后端运行 + Nginx 反向代理

# ==================== Stage 1: 构建前端 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 复制整个前端目录
COPY frontend/ .

# 安装依赖并构建
RUN npm install --legacy-peer-deps && \
    npm run build

# ==================== Stage 2: 准备后端 ====================
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装系统依赖（包含 Nginx）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY src/ ./src/
COPY config/ ./config/

# 创建数据目录
RUN mkdir -p /app/data /var/log/supervisor /run/nginx

# ==================== Stage 3: 最终镜像 ====================
FROM backend

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/.next/standalone /app/frontend/
COPY --from=frontend-builder /app/public /app/frontend/public/
COPY --from=frontend-builder /app/.next/static /app/frontend/.next/static/

# 复制 Nginx 配置
COPY docker/nginx.conf /etc/nginx/nginx.conf

# 复制 Supervisor 配置
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# 使用 Supervisor 同时运行 Nginx 和后端 API
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
