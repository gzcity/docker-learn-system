# 🐳 Docker Source Code Learning System

> **An AI-native, multi-agent system that teaches you Docker internals through conversation, quizzes, spaced repetition, and deep research — all powered by a knowledge graph.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code lines](https://img.shields.io/badge/code-7000%2B%20Python-blueviolet)](.)
[![Agents](https://img.shields.io/badge/agents-8-orange)](./agents)
[![Concepts](https://img.shields.io/badge/concepts-16-ff69b4)](./docker-knowledge)
[![Questions](https://img.shields.io/badge/questions-30-9cf)](./questions)
[![Web UI](https://img.shields.io/badge/Web%20UI-Streamlit-FF4B4B)](./web_ui)
[![Stars](https://img.shields.io/github/stars/gzcity/docker-learn-system?style=social)](https://github.com/gzcity/docker-learn-system)

---

**🇨🇳 中文说明：** 这是一个智能体原生的 Docker 源码学习系统，整合对话、解题、测验、深度研究、可视化、知识库、间隔重复和长期记忆。点击 [这里](./README.zh.md) 查看中文版。

---

## 📸 Demo

<details>
<summary>📺 CLI Demo (click to expand)</summary>

```text
$ python3 learn.py

🐳 Docker 源码学习系统 v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 16个核心概念 | 30道题目 | 8种人格
🎯 学习系统已就绪，开始你的 Docker 源码之旅！

> 什么是容器运行时？

🧠 容器运行时 (Container Runtime)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

一句话定义：
  负责管理容器完整生命周期的底层软件组件

核心组成：
  • runc    — 实际创建和运行容器进程（OCI 实现）
  • containerd — 高级运行时，管理镜像传输和容器生命周期
  • shim    — 连接 containerd 和 runc 的桥梁

> 画一下容器运行时的架构图

📊 容器运行时架构图
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

graph TD
    DockerCLI["docker CLI"] --> DockerDaemon["dockerd"]
    DockerDaemon --> Containerd["containerd"]
    Containerd --> Shim["containerd-shim"]
    Shim --> Runc["runc"]
    Runc --> Container["容器进程"]
    ...

> 考考我关于 cgroups 的题

📝 测验：cgroups
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1 (选择题):
cgroups 在 Docker 中主要用于什么？

A. 网络隔离
B. 进程视图隔离
C. 资源限制和监控
D. 文件系统隔离

✅ 正确！cgroups 的核心作用是资源限制和监控。
```

</details>

---

## 🎯 Why This Exists

Learning Docker source code has a steep learning curve:

- **Docker's codebase** is 2M+ lines of Go — where do you even start?
- **Existing tools** are either docs (passive) or tutorials (linear) — none adapt to **you**
- **Learning drops off** without spaced repetition — the brain forgets

**This system solves all three.** It's like having a personal tutor who:

1. 📖 **Knows the codebase** — maps concepts to actual source files
2. 🧠 **Remembers what you know** — adapts difficulty and pace
3. 🔄 **Reviews at the right time** — SM-2 spaced repetition
4. 🎭 **Teaches in your style** — 8 teaching personas (Socratic, Professor, Coach...)
5. 🔍 **Goes deep** — generates research reports with architecture diagrams

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Conversational Tutor** | Ask anything about Docker internals. The system retrieves knowledge graph context, checks your mastery level, and adapts the explanation. |
| 📝 **Quiz Engine** | 8 question types (choice, true/false, fill-blank, code analysis, etc.), 5 scoring methods. Difficulty adapts to your mastery. |
| 🔄 **Spaced Repetition** | SM-2 algorithm with forgetting curve modeling. Automatically schedules reviews when you're about to forget. |
| 🎭 **8 Teaching Personas** | Socratic, Professor, Practitioner, Storyteller, Coach, Debugger, Minimalist, Devil's Advocate. |
| 📊 **Visualization Engine** | 8 diagram types rendered as images: architecture, call chain, class diagram, data flow, learning path, knowledge graph, progress, heatmap. |
| 🔍 **Go AST Parsing** | Real Docker source code analysis — fetch from GitHub, parse structs/interfaces/functions, generate source reports. |
| 🔬 **Deep Research** | Generates structured research reports with code references, architecture analysis, design patterns, and concept relationships. |
| 📚 **Knowledge Base + Books** | Structured Docker knowledge + interactive books with progress tracking. |
| 📓 **Note System** | Notes auto-link to concepts. Supports semantic search and Markdown export. |
| 🧠 **Long-term Memory** | Cross-session context recovery. Remembers what you learned, weak spots, misconceptions, and preferences. |
| 🎯 **Adaptive Learning Path** | 4 stages (Beginner → Advanced → Proficient → Expert), BFS prerequisite planning. |
| 🖥️ **Web UI** | Streamlit interface with Plotly charts, Mermaid diagrams, persona switcher, mastery dashboard. |
| ❌ **Misconception Detection** | DeepTutor-inspired Expectation-Misconception framework. Catches misunderstandings and corrects them in real-time. |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│      │  Natural      │  │  Visualization │  │  File/Code   │       │
│      │  Language     │  │  Output        │  │  Export      │       │
│      └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────────┼──────────────────┼──────────────────┼──────────────┘
              │                  │                  │
┌─────────────┼──────────────────┼──────────────────┼──────────────┐
│             ▼                  ▼                  ▼              │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │                ORCHESTRATOR LAYER                       │  │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│    │  │  Tutor   │ │Researcher│ │QuizMaster│ │Visualizer│   │  │
│    │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │   │  │
│    │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │  │
│    │  ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐              │  │
│    │  │  Coach   │ │ Librarian│ │  Scribe  │              │  │
│    │  │  Agent   │ │  Agent   │ │  Agent   │              │  │
│    │  └──────────┘ └──────────┘ └──────────┘              │  │
│    └───────────────────────────┬──────────────────────────┘  │  │
│                               │                              │  │
│    ┌───────────────────────────┼──────────────────────────┐  │  │
│    │            ▼              ▼              ▼            │  │  │
│    │    ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │  │  │
│    │    │Knowledge │  │Long-term     │  │  Tools       │  │  │  │
│    │    │ Graph    │  │Memory (MCP)  │  │(Browser/CLI) │  │  │  │
│    │    │ (File)   │  │ (Vector+File)│  │              │  │  │  │
│    │    └──────────┘  └──────────────┘  └──────────────┘  │  │  │
│    └──────────────────────────────────────────────────────┘  │  │
│                   DATA & INFRASTRUCTURE LAYER                 │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Agent Collaboration

| Agent | Role | Core Capability |
|-------|------|-----------------|
| **Orchestrator** | Scheduler | Intent recognition, context management, Agent routing |
| **Tutor** | Teacher | Concept explanation, knowledge transfer, adaptive teaching |
| **Researcher** | Researcher | Source code analysis, research report generation |
| **QuizMaster** | Examiner | Quiz generation, auto-scoring, difficulty adaptation |
| **Visualizer** | Visualizer | Diagram generation, architecture drawing |
| **Librarian** | Librarian | Knowledge base management, books, notes |
| **Coach** | Coach | Practice planning, spaced repetition, mastery tracking |
| **Scribe** | Scribe | Session recording, note generation, memory updates |

---

## 🚀 Quick Start

### CLI Mode (Zero Dependencies)

```bash
git clone https://github.com/gzcity/docker-learn-system.git
cd docker-learn-system
python3 learn.py
```

### Web UI Mode (Recommended)

```bash
pip install streamlit plotly
streamlit run web_ui/app.py
```

Then open **http://localhost:8501**. Includes:
- 💬 Chat interface
- 📊 Dashboard with Plotly charts
- 📚 Knowledge graph browser
- 📝 Interactive quiz
- 🎯 Mastery heatmap with retention curves
- 📈 Mermaid diagram gallery (8 types)
- 🔍 Go source code analysis
- 📖 Interactive books
- 📓 Notes with search/export

### First Steps

```text
> 引导                 # New user onboarding
> 总览                 # Learning dashboard overview
> 什么是容器运行时      # Ask about a concept
> 考考我               # Take a quiz
> 画一下架构图         # Visualize the architecture
> 用教授风格           # Switch persona to Professor
> 深入容器运行时       # Deep research mode
> 我的掌握度           # Check mastery levels
```

---

## 🎭 Teaching Personas

| Persona | Style |
|---------|-------|
| Socrates | Questions back, makes you think |
| Professor | Structured, rigorous, systematic |
| Practitioner | Code-first, hands-on |
| Storyteller | Analogies, narratives, intuitions |
| Coach | Goal-oriented, motivational |
| Debugger | Problem-first, reverse thinking |
| Minimalist | Shortest path to the answer |
| Devil's Advocate | Challenges assumptions |

Switch anytime: `> 用教练风格` or `> 苏格拉底模式`

---

## 🧩 Knowledge Graph (16 Core Concepts)

Each concept includes:
- **Definition** & **difficulty rating**
- **Prerequisites** & **related concepts**
- **Source code references** (file paths)
- **Common misconceptions** (DeepTutor Expectation-Misconception framework)

Concepts: Container, Image, Layer, Container Runtime, Dockerd, Client, API Types, Runtime, Network, Volume, Dockerfile, Registry, Reference, Cgroups, Namespaces, UnionFS

---

## 🧠 Spaced Repetition (SM-2)

- **Forgetting curve**: mastery decays exponentially over time
- **Association propagation**: improving one concept boosts related ones by 30%
- **Due review prediction**: automatically identifies concepts needing review

---

## 🗺️ Project Structure

```
docker-learn-system/
├── README.md              ← This file
├── README.zh.md           ← Chinese version
├── learn.py               ← CLI entry point
├── engine/                ← Core engine (7,000+ lines)
│   ├── orchestrator.py    ← Main orchestrator
│   ├── knowledge_graph.py ← Knowledge graph engine
│   ├── knowledge_base.py  ← Knowledge base + books + notes
│   ├── quiz_engine.py     ← Quiz & scoring engine
│   ├── mastery_engine.py  ← SM-2 mastery engine
│   ├── visualization_engine.py ← 8 diagram types
│   ├── research_engine.py ← Deep research reports
│   ├── go_ast_parser.py   ← Go source code parser
│   ├── memory_engine.py   ← Long-term memory
│   ├── persona_engine.py  ← 8 personas + learning path
│   └── dashboard_engine.py ← Dashboard + flows + UX
├── agents/                ← Agent role definitions
├── docker-knowledge/      ← Knowledge graph seed data
├── questions/             ← Question bank (30 questions)
├── personas/              ← Persona configurations
├── books/                 ← Interactive book (7 chapters)
├── web_ui/                ← Streamlit Web UI
└── deploy/                ← Docker deployment
```

---

## 📊 Stats

| Metric | Value |
|--------|-------|
| Python code lines | ~7,000 |
| Engine modules | 11 |
| Agent roles | 8 |
| Core concepts | 16 |
| Common misconceptions | 20 |
| Questions | 30 (8 types, 5 difficulties) |
| Teaching personas | 8 |
| Visualization types | 8 |
| Docker source categories | 15 |
| Book chapters | 7 |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ (pure, no external deps) |
| **Knowledge Graph** | File-based (engine supports Neo4j switch) |
| **Memory** | File system + JSON (vector DB ready) |
| **Visualization** | Mermaid diagrams + Plotly charts |
| **CLI** | Native terminal (no framework) |
| **Deployment** | Docker Compose (Neo4j + ChromaDB + App) |

---

## 🎯 Implementation Status

| Phase | Name | Status |
|-------|------|--------|
| P0 | Foundation + Knowledge Graph + Dialogue | ✅ |
| P1 | Knowledge Base + Books + Notes | ✅ |
| P2 | Quiz Engine + Scoring | ✅ |
| P3 | Mastery Model + Spaced Repetition | ✅ |
| P4 | Deep Research + Visualization | ✅ |
| P5 | Long-term Memory + Context Recovery | ✅ |
| P6 | Persona System + Adaptive Learning Path | ✅ |
| P7 | Dashboard + Learning Loops + UX | ✅ |
| P8 | Go AST Parser + Web UI Charts | ✅ |

---

## 🤝 Contributing

This is a project that could go many directions. Contributions welcome!

**Ideas to explore:**
- 🌐 **React frontend** — replace Streamlit with a modern UI
- 🗄️ **Neo4j backend** — for large-scale knowledge graphs
- 🌍 **English content** — translate concepts and questions
- 🧪 **More questions** — expand the question bank (target 100+)
- 📱 **API mode** — expose as a REST/gRPC service
- 🔌 **VS Code extension** — learn Docker in your editor

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [DeepTutor](http://deeptutor.memphis.edu/) — the Expectation-Misconception framework
- Built on research in spaced repetition (SM-2 algorithm)
- Docker knowledge based on the actual Docker CE source code

---

**⭐ If you find this project useful, give it a star! It helps others discover it.**