#!/bin/bash
# ============================================================
# Docker 源码学习系统 — 入口脚本
# ============================================================
set -e

MODE="${1:-app}"

echo "============================================"
echo " Docker 源码学习系统 v1.0"
echo " 模式: ${MODE}"
echo "============================================"

# 等待依赖服务就绪
wait_for_services() {
    echo "→ 等待 Neo4j 就绪..."
    until cypher-shell -u "${NEO4J_USER:-neo4j}" \
                       -p "${NEO4J_PASSWORD:-learn1234}" \
                       -a "${NEO4J_URI:-bolt://neo4j:7687}" \
                       "RETURN 1" > /dev/null 2>&1; do
        sleep 2
    done
    echo "  ✓ Neo4j 就绪"

    echo "→ 等待 ChromaDB 就绪..."
    until curl -s "http://${CHROMA_HOST:-chroma}:${CHROMA_PORT:-8000}/api/v1/heartbeat" > /dev/null 2>&1; do
        sleep 2
    done
    echo "  ✓ ChromaDB 就绪"
}

# 初始化知识图谱
init_knowledge_graph() {
    echo "→ 初始化知识图谱..."
    if [ -f /workspace/init/seed.cypher ]; then
        cypher-shell -u "${NEO4J_USER:-neo4j}" \
                     -p "${NEO4J_PASSWORD:-learn1234}" \
                     -a "${NEO4J_URI:-bolt://neo4j:7687}" \
                     -f /workspace/init/seed.cypher
        echo "  ✓ 知识图谱初始化完成"
    else
        echo "  - 未找到 seed.cypher，跳过初始化"
    fi
}

# 启动应用模式
start_app() {
    wait_for_services
    init_knowledge_graph

    echo "→ 启动学习系统 Agent..."
    exec copaw-agent run \
        --workspace /workspace \
        --config /workspace/config/agent.yaml \
        --persona "${ACTIVE_PERSONA:-socratic}" \
        --port 8080
}

# 启动定时任务模式
start_cron() {
    wait_for_services

    echo "→ 启动定时任务..."
    exec copaw-agent cron \
        --config /workspace/config/cron.yaml
}

# 执行数据库迁移/维护
run_migration() {
    echo "→ 执行数据迁移..."
    exec python /workspace/init/migrate.py
}

# 主逻辑
case "${MODE}" in
    app)
        start_app
        ;;
    cron)
        start_cron
        ;;
    migrate)
        run_migration
        ;;
    shell)
        exec /bin/bash
        ;;
    *)
        echo "未知模式: ${MODE}"
        echo "可用模式: app, cron, migrate, shell"
        exit 1
        ;;
esac