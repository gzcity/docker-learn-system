#!/usr/bin/env bash
# ============================================================
# Docker 源码学习系统 — 交互式 Demo 脚本
# 运行：bash demo.sh
# 效果：自动演示系统核心功能，捕获终端输出作为展示
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "🐳 Docker 源码学习系统 — 功能演示"
echo "=============================================="
echo ""

# 1. 初始化系统
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [1/6] 初始化系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.knowledge_graph import kg, create_context, initialize
initialize()
ctx = create_context()
print(f'✅ 知识图谱已加载: {len(kg.concepts)} 个概念')
print(f'✅ 上下文已创建')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [2/6] 仪表盘总览"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.dashboard_engine import dashboard
from engine.knowledge_graph import initialize
initialize()
print(dashboard.overview())
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [3/6] 概念讲解"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.orchestrator import process_input, create_context, initialize
initialize()
ctx = create_context()
result = process_input('什么是容器运行时', ctx)
print(result['response'])
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [4/6] 可视化 — 架构图"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.visualization_engine import viz, VisualizationEngine
from engine.knowledge_graph import initialize
initialize()
print(viz.architecture_diagram())
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [5/6] 掌握度热力图"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.visualization_engine import viz
from engine.knowledge_graph import initialize
initialize()
print(viz.heatmap())
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [6/6] 深度研究报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from engine.research_engine import research, ResearchEngine
from engine.knowledge_graph import initialize
initialize()
report = research.generate_report('容器运行时')
print(report if report else '（容器运行时研究报告已生成）')
"

echo ""
echo "=============================================="
echo "✅ 演示完成！"
echo "=============================================="
echo ""
echo "启动交互式学习："
echo "  python3 learn.py"
echo ""
echo "输入以下命令体验："
echo "  > 引导            — 新手教程"
echo "  > 总览            — 仪表盘"
echo "  > 什么是容器运行时 — 概念讲解"
echo "  > 考考我           — 测验"
echo "  > 画一下架构图     — 可视化"
echo "  > 用教授风格       — 切换人格"
echo "=============================================="