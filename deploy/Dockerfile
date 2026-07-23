# ============================================================
# Docker 源码学习系统 — Dockerfile
# ============================================================
# 基于 CoPaw Agent 运行时的多阶段构建
# ============================================================

# ---- 第一阶段：基础环境 ----
FROM python:3.11-slim AS base

LABEL maintainer="Docker Learning System"
LABEL description="Multi-agent Docker source code learning system"

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# ---- 第二阶段：构建依赖 ----
FROM base AS builder

WORKDIR /build

# 安装 Python 依赖
COPY deploy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- 第三阶段：运行环境 ----
FROM base AS runtime

WORKDIR /workspace

# 从构建阶段复制 Python 包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 创建必要的目录结构
RUN mkdir -p /workspace/{data,memory,notes,config} \
    && mkdir -p /docker-source

# ============================================================
# 复制系统文件
# ============================================================

# 知识图谱种子数据
COPY docker-knowledge/ /workspace/data/docker-knowledge/

# 题库
COPY questions/ /workspace/data/questions/

# 人格预设
COPY personas/ /workspace/data/personas/

# 书籍
COPY books/ /workspace/data/books/

# Agent 定义
COPY agents/ /workspace/data/agents/

# 命令定义
COPY commands/ /workspace/data/commands/

# 初始化脚本
COPY deploy/init/ /workspace/init/

# 配置文件
COPY deploy/config/ /workspace/config/

# ============================================================
# 入口脚本
# ============================================================
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]

# 默认启动模式：app（也可用 cron）
CMD ["app"]