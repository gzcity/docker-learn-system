# Docker 源码学习系统 — 知识图谱引擎

"""
文件版知识图谱引擎。
在没有 Neo4j 的环境下，使用文件系统 + 内存缓存来管理知识图谱。
当 Neo4j 可用时，可无缝切换到数据库模式。
"""

import json
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

# ============================================================
# 数据目录
# ============================================================
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "docker-knowledge"
QUESTIONS_DIR = BASE_DIR / "questions"
MEMORY_DIR = BASE_DIR / "memory"
PERSONAS_DIR = BASE_DIR / "personas"


# ============================================================
# 核心数据结构
# ============================================================

class Concept:
    """知识图谱中的概念节点"""
    def __init__(self, name: str, definition: str = "",
                 difficulty: float = 0.5, code_ref: str = "",
                 prerequisites: list = None, related: list = None,
                 misconceptions: list = None, english_name: str = "",
                 english_definition: str = ""):
        self.name = name
        self.definition = definition
        self.difficulty = difficulty
        self.code_ref = code_ref
        self.prerequisites = prerequisites or []
        self.related = related or []
        self.misconceptions = misconceptions or []
        self.english_name = english_name
        self.english_definition = english_definition

    def to_dict(self):
        return {
            "name": self.name,
            "definition": self.definition,
            "difficulty": self.difficulty,
            "code_ref": self.code_ref,
            "prerequisites": self.prerequisites,
            "related": self.related,
            "misconceptions": self.misconceptions,
            "english_name": self.english_name,
            "english_definition": self.english_definition,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            definition=d.get("definition", ""),
            difficulty=d.get("difficulty", 0.5),
            code_ref=d.get("code_ref", ""),
            prerequisites=d.get("prerequisites", []),
            related=d.get("related", []),
            misconceptions=d.get("misconceptions", []),
            english_name=d.get("english_name", ""),
            english_definition=d.get("english_definition", ""),
        )


class MasteryRecord:
    """掌握度记录"""
    def __init__(self, concept: str, level: float = 0.0,
                 attempts: int = 0, correct: int = 0,
                 last_practiced: str = "", next_review: str = ""):
        self.concept = concept
        self.level = level
        self.attempts = attempts
        self.correct = correct
        self.last_practiced = last_practiced
        self.next_review = next_review
        self.misconceptions_corrected = []

    @property
    def accuracy(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts

    def to_dict(self):
        return {
            "concept": self.concept,
            "level": self.level,
            "attempts": self.attempts,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "last_practiced": self.last_practiced,
            "next_review": self.next_review,
            "misconceptions_corrected": self.misconceptions_corrected,
        }


# ============================================================
# 知识图谱引擎
# ============================================================

class KnowledgeGraph:
    """知识图谱管理器（文件版）"""

    def __init__(self, data_dir: Path = KNOWLEDGE_DIR):
        self.data_dir = data_dir
        self.concepts: dict[str, Concept] = {}
        self._loaded = False

    def load(self):
        """从 Markdown 文件加载知识图谱"""
        if self._loaded:
            return

        concepts_file = self.data_dir / "CONCEPTS.md"
        if not concepts_file.exists():
            print(f"[知识图谱] 未找到概念文件: {concepts_file}")
            return

        content = concepts_file.read_text(encoding="utf-8")
        self._parse_concepts(content)
        self._loaded = True
        print(f"[知识图谱] 加载完成: {len(self.concepts)} 个概念")

    def _parse_concepts(self, content: str):
        """解析 Markdown 格式的概念定义"""
        sections = re.split(r'\n### ', content)
        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split('\n')
            name = lines[0].strip().rstrip()
            english_name = ""
            definition = ""
            english_definition = ""
            difficulty = 0.5
            code_ref = ""
            prerequisites = []
            related = []
            misconceptions = []
            current_mc = None

            for line in lines[1:]:
                line = line.strip()
                if line.startswith('- **English**:'):
                    english_name = line.replace('- **English**:', '').strip()
                elif line.startswith('- **定义**：'):
                    definition = line.replace('- **定义**：', '').strip()
                elif line.startswith('- **English definition**:'):
                    english_definition = line.replace('- **English definition**:', '').strip()
                elif line.startswith('- **关联概念**：'):
                    rel_text = line.replace('- **关联概念**：', '').strip()
                    related = [c.strip().strip('`') for c in rel_text.split('→')]
                elif line.startswith('- **前置知识**：'):
                    pre_text = line.replace('- **前置知识**：', '').strip()
                    prerequisites = [c.strip().strip('`') for c in pre_text.split('→')]
                elif line.startswith('- **代码引用**：'):
                    code_ref = line.replace('- **代码引用**：', '').strip()
                elif line.startswith('- **初始难度**：'):
                    diff_text = line.replace('- **初始难度**：', '').strip().replace('/5', '')
                    try:
                        difficulty = int(diff_text) / 5.0
                    except:
                        difficulty = 0.5
                elif line.startswith('- **"') and '** ❌' in line:
                    if current_mc:
                        misconceptions.append(current_mc)
                    pattern = line.split('- **"')[1].split('"**')[0]
                    current_mc = {"pattern": pattern, "severity": "major", "correction": "", "keywords": []}
                elif line.startswith('纠正：') and current_mc:
                    current_mc["correction"] = line.replace('纠正：', '').strip()
                elif line.startswith('Correction:') and current_mc:
                    current_mc["correction_en"] = line.replace('Correction:', '').strip()
                elif line.startswith('- **') and '** ❌' in line:
                    pattern = line.split('- **')[1].split('**')[0]
                    correction = line.split('❌')[1].strip() if '❌' in line else ""
                    misconceptions.append({"pattern": pattern, "severity": "major", "correction": correction, "keywords": []})

            if current_mc:
                misconceptions.append(current_mc)

            if name and definition:
                self.concepts[name] = Concept(
                    name=name, definition=definition, difficulty=difficulty,
                    code_ref=code_ref, prerequisites=prerequisites,
                    related=related, misconceptions=misconceptions,
                    english_name=english_name, english_definition=english_definition,
                )

    def get_concept(self, name: str) -> Optional[Concept]:
        self.load()
        return self.concepts.get(name)

    def search_concepts(self, query: str) -> list[Concept]:
        self.load()
        results = []
        q = query.lower()
        for name, c in self.concepts.items():
            if q in name.lower() or q in c.definition.lower():
                results.append(c)
        return results

    def get_related_concepts(self, name: str) -> list[Concept]:
        c = self.get_concept(name)
        if not c:
            return []
        return [self.get_concept(r.strip()) for r in c.related if self.get_concept(r.strip())]

    def get_prerequisites(self, name: str) -> list[Concept]:
        c = self.get_concept(name)
        if not c:
            return []
        return [self.get_concept(p.strip()) for p in c.prerequisites if self.get_concept(p.strip())]

    def detect_misconception(self, concept_name: str, user_input: str) -> Optional[dict]:
        """检测用户输入中是否包含常见误解"""
        c = self.get_concept(concept_name)
        if not c or not c.misconceptions:
            return None
        for mc in c.misconceptions:
            # 精确匹配：整句包含模式
            if mc["pattern"] in user_input:
                return mc
            # 关键词匹配：检查任何部分关键词
            pattern = mc["pattern"]
            for sep in ["就是", "是", "的", "了", "能"]:
                pattern = pattern.replace(sep, " ")
            words = [w for w in pattern.split() if len(w) >= 1]
            matched = sum(1 for w in words if len(w) >= 2 and w in user_input)
            if matched == len(words) and len(words) > 0:
                return mc
            # 宽松匹配：至少匹配 2 个词（不考虑长度）
            if len(words) >= 2:
                matched = sum(1 for w in words if w in user_input)
                if matched >= 2:
                    return mc
        return None

    def get_all_concepts(self) -> list[Concept]:
        self.load()
        return list(self.concepts.values())

    def get_learning_path(self, start: str, target: str) -> list[str]:
        """BFS 查找学习路径"""
        visited = set()
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == target:
                return path
            if node in visited:
                continue
            visited.add(node)
            c = self.get_concept(node)
            if c:
                for rel in c.related:
                    if rel.strip() not in visited:
                        queue.append(path + [rel.strip()])
        return []


# ============================================================
# 掌握度管理器
# ============================================================

class MasteryManager:
    def __init__(self, data_dir: Path = MEMORY_DIR):
        self.data_dir = data_dir
        self.records: dict[str, MasteryRecord] = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        f = self.data_dir / "mastery.json"
        if f.exists():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for item in data:
                    r = MasteryRecord(
                        concept=item["concept"], level=item.get("level", 0.0),
                        attempts=item.get("attempts", 0), correct=item.get("correct", 0),
                        last_practiced=item.get("last_practiced", ""),
                        next_review=item.get("next_review", ""),
                    )
                    r.misconceptions_corrected = item.get("misconceptions_corrected", [])
                    self.records[r.concept] = r
            except Exception as e:
                print(f"[掌握度] 加载失败: {e}")
        self._loaded = True

    def save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self.records.values()]
        (self.data_dir / "mastery.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, concept: str) -> MasteryRecord:
        self.load()
        if concept not in self.records:
            self.records[concept] = MasteryRecord(concept=concept)
        return self.records[concept]

    def update(self, concept: str, correct: bool, difficulty: float = 0.5):
        record = self.get(concept)
        record.attempts += 1
        if correct:
            record.correct += 1
            record.level = min(1.0, record.level + 0.05 * difficulty)
        else:
            record.level = max(0.0, record.level - 0.03)
        record.last_practiced = datetime.now().strftime("%Y-%m-%d")
        self.save()

    def record_misconception(self, concept: str, pattern: str):
        record = self.get(concept)
        record.misconceptions_corrected.append({
            "pattern": pattern,
            "corrected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        record.level = max(0.0, record.level - 0.1)
        self.save()

    def get_weakest_concepts(self, top_n: int = 5) -> list[MasteryRecord]:
        self.load()
        return sorted([r for r in self.records.values() if r.attempts > 0], key=lambda r: r.level)[:top_n]

    def get_due_reviews(self) -> list[MasteryRecord]:
        self.load()
        today = datetime.now().strftime("%Y-%m-%d")
        return [r for r in self.records.values() if r.next_review and r.next_review <= today]


# ============================================================
# 会话上下文
# ============================================================

class SessionContext:
    def __init__(self, session_id: str = "default", memory_dir: Path = MEMORY_DIR):
        self.session_id = session_id
        self.memory_dir = memory_dir
        self.current_concept = ""
        self.concept_path = []
        self.active_persona = "socratic"
        self.dialogue_history = []
        self.recently_viewed = []
        self.pending_questions = []
        self.research_mode = False
        self.user_profile = {}

    def set_concept(self, concept: str):
        self.current_concept = concept
        if concept not in self.concept_path:
            self.concept_path.append(concept)
        if concept not in self.recently_viewed:
            self.recently_viewed.append(concept)

    def add_dialogue(self, user_input: str, response: str):
        self.dialogue_history.append({
            "user": user_input,
            "agent": response,
            "timestamp": datetime.now().isoformat(),
        })

    def get_context_prompt(self) -> str:
        parts = [
            f"当前概念: {self.current_concept or '无'}",
            f"学习路径: {' → '.join(self.concept_path[-5:]) if self.concept_path else '无'}",
            f"当前人格: {self.active_persona}",
            f"最近看过: {', '.join(self.recently_viewed[-3:]) if self.recently_viewed else '无'}",
        ]
        if self.pending_questions:
            parts.append(f"未完成题目: {len(self.pending_questions)} 道")
        return "\n".join(parts)


# ============================================================
# 每日日志
# ============================================================

class DailyLog:
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = memory_dir / f"{self.today}.md"

    def append(self, content: str):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(content + "\n")

    def get_today_log(self) -> str:
        if self.log_file.exists():
            return self.log_file.read_text(encoding="utf-8")
        return ""

    def log_learning(self, concept: str, duration: int, mastery_delta: float):
        entry = (f"- {self.today} {datetime.now().strftime('%H:%M')} "
                 f"学习 {concept} ({duration}分钟, 掌握度变化: {mastery_delta:+.2f})")
        self.append(entry)


# ============================================================
# 初始化
# ============================================================

kg = KnowledgeGraph()
mastery = MasteryManager()
daily_log = DailyLog()


def initialize():
    kg.load()
    print(f"  ✓ 知识图谱: {len(kg.concepts)} 个概念")
    print(f"  ✓ 掌握度记录: {len(mastery.records)} 个")
    print(f"  ✓ 日志系统: 就绪")


def create_context(session_id: str = "default") -> SessionContext:
    return SessionContext(session_id=session_id, memory_dir=MEMORY_DIR)