# Contributing to Docker Source Code Learning System

🎉 First off, thanks for considering contributing! This project thrives on community input.

## 🚀 Quick Ways to Contribute

### 🌐 Web UI
The biggest impact you can make. The system is CLI-only — a web interface would 3x adoption.
- **Streamlit** frontend (quickest path)
- **React + FastAPI** (full-featured)
- **VS Code extension** (developer-friendly)

### 🔬 Real Go AST Parsing
The research engine currently uses knowledge graph data. Connect it to real Docker source code:
- Parse Go packages, interfaces, structs, functions
- Extract call relationships from AST
- Generate concept definitions from code comments

### 🗄️ Neo4j Backend
The knowledge graph engine is designed to support Neo4j. Implement the switch:
- See `engine/knowledge_graph.py` — the `Neo4jKnowledgeGraph` class is ready
- Add Cypher queries for concept relations
- Add Docker Compose Neo4j configuration

### 🧪 Question Bank
More questions = better learning. Add questions in `questions/EXAMPLES.md`:
- 8 question types supported
- 5 difficulty levels (0.1 - 0.9)
- Must link to existing concepts
- See existing questions for format

### 🌍 English Content
Translate concepts, misconceptions, and knowledge base content to English.

### 📚 Books
Write chapters for the interactive book system in `books/`:
- Markdown format with code links
- Concept annotations
- Chapter-end quiz questions

## 🧠 Development Guide

### Architecture Overview

```
engine/              ← Core logic (10 modules, 6,300 lines)
agents/              ← Agent role definitions
docker-knowledge/    ← Knowledge graph seed data
questions/           ← Question bank
personas/            ← Persona configurations
books/               ← Interactive book content
memory/              ← User learning memory (runtime)
```

### Key Design Principles

1. **Knowledge graph is the heart** — all features revolve around concepts and their relationships
2. **Context flows naturally** — users don't "switch pages", they continue conversations
3. **Agents are glue, not pages** — no UI for "question bank", just natural language
4. **Learning is a loop** — dialogue → weak spots → quiz → update mastery → recommend → continue

### Coding Style

- Pure Python 3.10+, no external dependencies
- Docstrings in Chinese (English welcome for new code)
- One class per major responsibility
- Functions should be < 50 lines

## 📋 Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-idea`)
3. Commit your changes
4. Push and open a PR
5. Wait for review

## 💡 Ideas & Questions

Open an issue! Tag it with:
- `enhancement` — new features
- `bug` — something's broken
- `question` — need help understanding
- `good-first-issue` — for newcomers

---

**Thank you for being part of this project!** 🌟