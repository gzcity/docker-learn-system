# Docker 源码学习系统 — 知识库管理器

"""
知识库管理、书籍阅读、笔记管理。
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from .knowledge_graph import kg, BASE_DIR

# ============================================================
# 路径
# ============================================================
KNOWLEDGE_DIR = BASE_DIR / "docker-knowledge"
BOOKS_DIR = BASE_DIR / "books"
NOTES_DIR = BASE_DIR / "notes"


# ============================================================
# 知识库管理器
# ============================================================

class KnowledgeBase:
    """知识库管理器"""

    def __init__(self, data_dir: Path = KNOWLEDGE_DIR):
        self.data_dir = data_dir
        self._structure = None

    def load_structure(self) -> dict:
        """加载知识库结构"""
        if self._structure:
            return self._structure
        f = self.data_dir / "structure.json"
        if f.exists():
            self._structure = json.loads(f.read_text(encoding="utf-8"))
        else:
            self._structure = {"categories": []}
        return self._structure

    def get_categories(self) -> list[dict]:
        """获取所有分类"""
        s = self.load_structure()
        return sorted(s.get("categories", []), key=lambda c: c.get("order", 0))

    def get_knowledge_files(self, category_id: str = None) -> list[dict]:
        """获取知识文档列表"""
        if category_id:
            dir_path = self.data_dir / category_id
            if not dir_path.exists():
                return []
            files = []
            for f in sorted(dir_path.glob("*.md")):
                files.append({
                    "path": str(f.relative_to(self.data_dir)),
                    "name": f.stem,
                    "title": self._extract_title(f),
                })
            return files
        else:
            all_files = []
            for cat in self.get_categories():
                cid = cat["id"]
                files = self.get_knowledge_files(cid)
                for f in files:
                    f["category"] = cat["name"]
                all_files.extend(files)
            return all_files

    def _extract_title(self, filepath: Path) -> str:
        """从 Markdown 文件提取标题"""
        content = filepath.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        return filepath.stem

    def read_file(self, category_id: str, filename: str) -> Optional[str]:
        """读取知识文档内容"""
        f = self.data_dir / category_id / filename
        if not f.exists():
            # 尝试无扩展名
            f = self.data_dir / category_id / f"{filename}.md"
        if f.exists():
            return f.read_text(encoding="utf-8")
        return None

    def search(self, query: str) -> list[dict]:
        """搜索知识库"""
        results = []
        query_lower = query.lower()
        for cat in self.get_categories():
            cid = cat["id"]
            dir_path = self.data_dir / cid
            if not dir_path.exists():
                continue
            for f in dir_path.glob("*.md"):
                content = f.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # 找到匹配行作为摘要
                    snippet = ""
                    for line in content.split("\n"):
                        if query_lower in line.lower():
                            snippet = line.strip()[:100]
                            break
                    results.append({
                        "category": cat["name"],
                        "file": f.stem,
                        "title": self._extract_title(f),
                        "snippet": snippet,
                        "path": str(f.relative_to(self.data_dir)),
                    })
        return results

    def get_overview(self) -> str:
        """获取知识库概览"""
        lines = ["## 📚 知识库\n"]
        for cat in self.get_categories():
            files = self.get_knowledge_files(cat["id"])
            lines.append(f"### {cat['name']}")
            lines.append(f"*{cat['description']}*")
            for f in files:
                lines.append(f"- {f['title']}")
            lines.append("")
        return "\n".join(lines)


# ============================================================
# 书籍管理器
# ============================================================

class BookManager:
    """书籍管理器"""

    def __init__(self, books_dir: Path = BOOKS_DIR):
        self.books_dir = books_dir
        self._books = None

    def list_books(self) -> list[dict]:
        """列出所有书籍"""
        books = []
        if not self.books_dir.exists():
            return books
        for d in self.books_dir.iterdir():
            if d.is_dir():
                meta_file = d / "book.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    meta["dir"] = str(d)
                    books.append(meta)
        return books

    def get_book(self, book_id: str) -> Optional[dict]:
        """获取书籍元数据"""
        for b in self.list_books():
            if b.get("id") == book_id:
                return b
        return None

    def read_chapter(self, book_id: str, chapter_id: str) -> Optional[str]:
        """读取章节内容"""
        book_dir = self.books_dir / book_id
        if not book_dir.exists():
            return None
        meta = self.get_book(book_id)
        if not meta:
            return None
        for ch in meta.get("chapters", []):
            if ch["id"] == chapter_id:
                f = book_dir / ch["file"]
                if f.exists():
                    return f.read_text(encoding="utf-8")
                return None
        return None

    def get_book_progress(self, book_id: str, user_id: str = "default") -> dict:
        """获取阅读进度"""
        progress_file = self.books_dir / book_id / "notes" / f"{user_id}_progress.json"
        default = {
            "book_id": book_id,
            "current_chapter": "01",
            "completed_chapters": [],
            "last_read": None,
        }
        if progress_file.exists():
            data = json.loads(progress_file.read_text(encoding="utf-8"))
            return {**default, **data}
        return default

    def save_progress(self, book_id: str, chapter_id: str, user_id: str = "default"):
        """保存阅读进度"""
        progress = self.get_book_progress(book_id, user_id)
        progress["current_chapter"] = chapter_id
        if chapter_id not in progress["completed_chapters"]:
            progress["completed_chapters"].append(chapter_id)
        progress["last_read"] = datetime.now().isoformat()
        progress_dir = self.books_dir / book_id / "notes"
        progress_dir.mkdir(parents=True, exist_ok=True)
        (progress_dir / f"{user_id}_progress.json").write_text(
            json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_book_overview(self, book_id: str) -> Optional[str]:
        """获取书籍概览"""
        meta = self.get_book(book_id)
        if not meta:
            return None
        lines = [
            f"## 📖 {meta['title']}",
            f"",
            f"*作者*：{meta.get('author', '未知')}  |  *难度*：{meta.get('difficulty', '未知')}",
            f"",
            f"{meta.get('description', '')}",
            f"",
            f"### 章节列表",
        ]
        for ch in meta.get("chapters", []):
            lines.append(f"- **{ch['id']}**. {ch['title']} ({ch.get('estimated_minutes', '?')}分钟)")
        lines.append("")
        lines.append("输入 `看书 <章号>` 开始阅读，例如 `看书 01`")
        return "\n".join(lines)


# ============================================================
# 笔记管理器
# ============================================================

class NoteManager:
    """笔记管理器"""

    def __init__(self, notes_dir: Path = NOTES_DIR):
        self.notes_dir = notes_dir
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def add_note(self, content: str, concept: str = "", book: str = "",
                 chapter: str = "", user_id: str = "default") -> dict:
        """添加笔记"""
        note = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "content": content,
            "concept": concept,
            "book": book,
            "chapter": chapter,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "tags": [],
        }
        # 自动提取标签
        for tag in ["docker", "runc", "containerd", "shim", "镜像", "容器",
                     "网络", "存储", "源码", "架构", "性能", "调试"]:
            if tag in content:
                note["tags"].append(tag)

        # 保存到用户笔记文件
        self._save_note(note)
        return note

    def _save_note(self, note: dict):
        """保存笔记到文件"""
        user_file = self.notes_dir / f"{note['user_id']}.jsonl"
        with open(user_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(note, ensure_ascii=False) + "\n")

    def search_notes(self, query: str, user_id: str = "default") -> list[dict]:
        """搜索笔记"""
        results = []
        user_file = self.notes_dir / f"{user_id}.jsonl"
        if not user_file.exists():
            return results
        query_lower = query.lower()
        with open(user_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    note = json.loads(line)
                    if query_lower in note.get("content", "").lower():
                        results.append(note)
                    elif query_lower in note.get("concept", "").lower():
                        results.append(note)
                    elif query_lower in ",".join(note.get("tags", [])):
                        results.append(note)
                except:
                    continue
        return results[::-1]  # 最新在前

    def list_notes(self, user_id: str = "default", limit: int = 20) -> list[dict]:
        """列出最近笔记"""
        notes = []
        user_file = self.notes_dir / f"{user_id}.jsonl"
        if not user_file.exists():
            return notes
        with open(user_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    notes.append(json.loads(line))
                except:
                    continue
        return notes[::-1][:limit]

    def export_notes(self, user_id: str = "default", format: str = "md") -> str:
        """导出笔记"""
        notes = self.list_notes(user_id, limit=1000)
        if format == "md":
            lines = ["# 学习笔记\n"]
            for note in notes:
                lines.append(f"## {note['created_at'][:10]} {note['created_at'][11:16]}")
                if note.get("concept"):
                    lines.append(f"**概念**：{note['concept']}")
                lines.append("")
                lines.append(note["content"])
                if note.get("tags"):
                    lines.append(f"*标签：{'、'.join(note['tags'])}*")
                lines.append("")
                lines.append("---")
                lines.append("")
            return "\n".join(lines)
        return json.dumps(notes, ensure_ascii=False, indent=2)


# ============================================================
# 全局实例
# ============================================================

kb = KnowledgeBase()
bm = BookManager()
nm = NoteManager()