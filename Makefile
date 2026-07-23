# ============================================================
# Docker 源码学习系统 — Makefile
# ============================================================
# 快速命令合集
# ============================================================

.PHONY: build up down logs shell reset ps init-source

# 默认目标
all: build up

# ---- 构建 ----
build:
	docker compose -f deploy/docker-compose.yml build

# ---- 启动 ----
up:
	docker compose -f deploy/docker-compose.yml up -d

# ---- 启动并查看日志 ----
up-logs:
	docker compose -f deploy/docker-compose.yml up

# ---- 停止 ----
down:
	docker compose -f deploy/docker-compose.yml down

# ---- 查看日志 ----
logs:
	docker compose -f deploy/docker-compose.yml logs -f

# ---- 查看日志（仅 app） ----
logs-app:
	docker compose -f deploy/docker-compose.yml logs -f app

# ---- 查看状态 ----
ps:
	docker compose -f deploy/docker-compose.yml ps

# ---- 进入容器 ----
shell:
	docker compose -f deploy/docker-compose.yml exec app /bin/bash

# ---- 进入 Neo4j 浏览器 ----
# 打开 http://localhost:7474 即可

# ---- 重置所有数据 ----
reset:
	docker compose -f deploy/docker-compose.yml down -v
	rm -rf volumes/neo4j/data volumes/chroma volumes/memory
	@echo "所有数据已清除"

# ---- 初始化 Docker 源码 ----
init-source:
	@if [ ! -d "volumes/docker-source" ]; then \
		echo "克隆 Docker 官方源码..."; \
		git clone --depth 1 https://github.com/docker/docker.git volumes/docker-source; \
		echo "  ✓ 完成"; \
	else \
		echo "Docker 源码已存在，更新中..."; \
		cd volumes/docker-source && git pull; \
		echo "  ✓ 完成"; \
	fi

# ---- 运行知识图谱迁移 ----
migrate:
	docker compose -f deploy/docker-compose.yml exec app /entrypoint.sh migrate

# ---- 导出学习数据 ----
export:
	docker compose -f deploy/docker-compose.yml exec app tar czf /tmp/learning-data.tar.gz /workspace/memory /workspace/notes
	docker compose -f deploy/docker-compose.yml cp app:/tmp/learning-data.tar.gz ./learning-data.tar.gz
	@echo "学习数据已导出: learning-data.tar.gz"

# ---- 查看帮助 ----
help:
	@echo "Docker 源码学习系统 — 快速命令"
	@echo "===================="
	@echo "make build      构建镜像"
	@echo "make up         启动服务"
	@echo "make down       停止服务"
	@echo "make logs       查看所有日志"
	@echo "make logs-app   查看应用日志"
	@echo "make ps         查看服务状态"
	@echo "make shell      进入容器"
	@echo "make reset      重置所有数据"
	@echo "make init-source 初始化 Docker 源码"
	@echo "make export     导出学习数据"
	@echo "make migrate    执行知识图谱迁移"