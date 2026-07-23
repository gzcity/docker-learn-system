#!/usr/bin/env bash
# ============================================================
# Docker 源码学习系统 — 一键启动 Web UI
# 用法：bash run_webui.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🐳 Docker 源码学习系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查 Streamlit
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 正在安装 Streamlit..."
    pip install streamlit -q
    echo ""
fi

echo "🚀 启动 Web UI..."
echo "   访问地址: http://localhost:8501"
echo "   按 Ctrl+C 停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

streamlit run web_ui/app.py --server.runOnSave true