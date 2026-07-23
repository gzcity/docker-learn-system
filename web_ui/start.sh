#!/usr/bin/env bash
# ============================================================
# Docker 源码学习系统 — Web UI 启动脚本
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🐳 Docker 源码学习系统 — Web UI"
echo "================================="
echo ""

# 检查 streamlit 是否安装
if ! command -v streamlit &> /dev/null; then
    echo "📦 正在安装 Streamlit..."
    pip install streamlit -q
    echo ""
fi

echo "🚀 启动 Web UI..."
echo "   访问地址: http://localhost:8501"
echo ""

cd "$PROJECT_DIR"
streamlit run web_ui/app.py --server.runOnSave true