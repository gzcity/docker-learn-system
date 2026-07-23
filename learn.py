#!/usr/bin/env python3
"""Docker 学习系统命令行入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.orchestrator import main, process_input, create_context, initialize
from engine.knowledge_graph import kg, mastery


def init():
    """初始化系统"""
    print("正在初始化 Docker 学习系统...")
    initialize()
    print("就绪！输入「learn」启动交互式学习。")
    print("或输入「learn --one-shot <问题>」直接提问。")


def one_shot(query: str):
    """单次问答模式"""
    initialize()
    ctx = create_context()
    result = process_input(query, ctx)
    print(result["response"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--one-shot":
        one_shot(" ".join(sys.argv[2:]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--init":
        init()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        initialize()
        ctx = create_context()
        from engine.orchestrator import handle_status
        print(handle_status(ctx))
    else:
        main()