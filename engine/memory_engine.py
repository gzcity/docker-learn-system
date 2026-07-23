# Docker 源码学习系统 — 长期记忆引擎

"""
跨会话长期记忆、用户画像、学习历史、会话恢复。
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from .knowledge_graph import kg, MEMORY_DIR, daily_log
from .mastery_engine import mastery_v2, get_retention_rate

# ============================================================
# 路径
# ============================================================
MEMORY_FILE = MEMORY_DIR / "long_term_memory.json"
SESSION_FILE = MEMORY_DIR / "last_session.json"
PROFILE_FILE = MEMORY_DIR / "profile.json"


# ============================================================
# 记忆记录
# ============================================================

class MemoryRecord:
    """长期记忆记录"""

    def __init__(self, key: str, category: str, content: dict,
                 timestamp: str = ""):
        self.key = key
        self.category = category  # profile | learning | misconception | insight | session
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "category": self.category,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            key=d["key"],
            category=d["category"],
            content=d.get("content", {}),
            timestamp=d.get("timestamp", ""),
        )


# ============================================================
# 长期记忆管理器
# ============================================================

class LongTermMemory:
    """长期记忆管理器"""

    def __init__(self, data_dir: Path = MEMORY_DIR):
        self.data_dir = data_dir
        self.memories: dict[str, MemoryRecord] = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                for item in data:
                    r = MemoryRecord.from_dict(item)
                    self.memories[r.key] = r
            except Exception as e:
                print(f"[记忆] 加载失败: {e}")
        self._loaded = True

    def save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self.memories.values()]
        MEMORY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, key: str, category: str, content: dict):
        """添加记忆记录"""
        self.load()
        self.memories[key] = MemoryRecord(key, category, content)
        self.save()

    def get(self, key: str) -> Optional[dict]:
        self.load()
        r = self.memories.get(key)
        return r.content if r else None

    def get_by_category(self, category: str) -> list[MemoryRecord]:
        self.load()
        return [r for r in self.memories.values() if r.category == category]

    def search(self, query: str) -> list[MemoryRecord]:
        """搜索记忆"""
        self.load()
        results = []
        q = query.lower()
        for r in self.memories.values():
            text = json.dumps(r.content, ensure_ascii=False).lower()
            if q in text or q in r.key.lower():
                results.append(r)
        return results

    def summarize(self) -> dict:
        """生成记忆摘要"""
        self.load()

        learning = self.get_by_category("learning")
        misconceptions = self.get_by_category("misconception")
        insights = self.get_by_category("insight")

        # 按日期分组学习记录
        by_date = {}
        for r in learning:
            date = r.timestamp[:10]
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(r.content.get("concept", ""))

        # 统计
        total_concepts = set()
        for records in by_date.values():
            total_concepts.update(records)

        return {
            "total_sessions": len(learning),
            "total_days": len(by_date),
            "concepts_learned": len(total_concepts),
            "misconceptions_corrected": len(misconceptions),
            "insights_recorded": len(insights),
            "recent_days": sorted(by_date.keys(), reverse=True)[:7],
        }

    def cleanup(self, max_age_days: int = 90):
        """清理过期记忆"""
        self.load()
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        to_delete = []
        for key, r in self.memories.items():
            if r.timestamp < cutoff and r.category in ("session", "learning"):
                to_delete.append(key)
        for key in to_delete:
            del self.memories[key]
        if to_delete:
            self.save()
        return len(to_delete)

    def get_misconception_recurrence(self) -> list[dict]:
        """检测误解复发"""
        self.load()
        misconceptions = self.get_by_category("misconception")

        # 统计每个误解的出现次数
        pattern_counts = {}
        for r in misconceptions:
            pattern = r.content.get("pattern", "")
            if pattern not in pattern_counts:
                pattern_counts[pattern] = {
                    "pattern": pattern,
                    "count": 0,
                    "dates": [],
                    "concept": r.content.get("concept", ""),
                }
            pattern_counts[pattern]["count"] += 1
            pattern_counts[pattern]["dates"].append(r.timestamp[:10])

        # 返回出现超过 1 次的误解
        recurrences = [v for v in pattern_counts.values() if v["count"] > 1]
        return sorted(recurrences, key=lambda x: x["count"], reverse=True)


# ============================================================
# 用户画像
# ============================================================

class UserProfile:
    """用户画像管理器"""

    def __init__(self):
        self.profile = self._default()
        self._loaded = False

    def _default(self) -> dict:
        return {
            "learner_type": "explorer",  # explorer | structured | practitioner
            "preferred_persona": "socratic",
            "session_count": 0,
            "total_minutes": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "strengths": [],
            "weaknesses": [],
            "interests": [],
            "notes": {},
        }

    def load(self):
        if self._loaded:
            return
        if PROFILE_FILE.exists():
            try:
                self.profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
            except:
                self.profile = self._default()
        self._loaded = True

    def save(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.profile["last_seen"] = datetime.now().isoformat()
        PROFILE_FILE.write_text(
            json.dumps(self.profile, ensure_ascii=False, indent=2), encoding="utf-8")

    def update_strengths_weaknesses(self):
        """从掌握度数据更新强弱项"""
        self.load()
        all_concepts = kg.get_all_concepts()
        strong = []
        weak = []
        for c in all_concepts:
            rec = mastery_v2.get(c.name)
            if rec.attempts > 0 and rec.level >= 0.7:
                strong.append(c.name)
            elif rec.attempts > 0 and rec.level < 0.3:
                weak.append(c.name)
            elif rec.attempts == 0:
                weak.append(c.name)
        self.profile["strengths"] = strong[:5]
        self.profile["weaknesses"] = weak[:5]
        self.save()

    def record_interest(self, concept: str):
        self.load()
        if concept not in self.profile["interests"]:
            self.profile["interests"].append(concept)
            self.profile["interests"] = self.profile["interests"][-10:]
        self.save()

    def get_greeting(self) -> str:
        """生成欢迎语"""
        self.load()
        weak = self.profile.get("weaknesses", [])
        strong = self.profile.get("strengths", [])
        session_count = self.profile.get("session_count", 0)

        if session_count == 0:
            return "欢迎来到 Docker 源码学习系统！试试「帮助」查看所有功能。"

        parts = []
        if strong:
            parts.append(f"上次你的强项是 {strong[0].split(' (')[0]}")
        if weak:
            parts.append(f"建议先复习 {weak[0].split(' (')[0]}")

        greeting = "欢迎回来！"
        if parts:
            greeting += " " + "，".join(parts) + "。"
        return greeting


# ============================================================
# 会话管理器
# ============================================================

class SessionManager:
    """会话状态管理"""

    @staticmethod
    def save_session(context: dict):
        """保存会话状态"""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "saved_at": datetime.now().isoformat(),
            "context": {
                "current_concept": context.get("current_concept", ""),
                "concept_path": context.get("concept_path", []),
                "active_persona": context.get("active_persona", "socratic"),
                "dialogue_count": context.get("dialogue_count", 0),
            },
            "mastery_summary": {
                c.name: {
                    "level": mastery_v2.get(c.name).level,
                    "attempts": mastery_v2.get(c.name).attempts,
                    "next_review": mastery_v2.get(c.name).next_review,
                }
                for c in kg.get_all_concepts()
            },
        }
        SESSION_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def load_session() -> Optional[dict]:
        """加载已保存的会话"""
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
                return data.get("context")
            except:
                pass
        return None

    @staticmethod
    def get_recovery_prompt() -> str:
        """生成会话恢复提示"""
        context = SessionManager.load_session()
        if not context:
            return ""

        current = context.get("current_concept", "")
        path = context.get("concept_path", [])
        persona = context.get("active_persona", "socratic")
        count = context.get("dialogue_count", 0)

        parts = ["📋 **会话已恢复**"]
        if current:
            parts.append(f"上次学习: {current}")
        if path:
            parts.append(f"学习路径: {' → '.join(path[-3:])}")
        parts.append(f"人格风格: {persona}")
        if count > 0:
            parts.append(f"已有 {count} 轮对话")
        parts.append("输入「帮助」查看所有命令。")

        return "\n".join(parts)


# ============================================================
# 每日学习总结
# ============================================================

class DailySummary:
    """每日学习总结生成器"""

    @staticmethod
    def generate() -> str:
        """生成今日学习总结"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = MEMORY_DIR / f"{today}.md"

        lines = [
            f"## 📅 每日学习总结 — {today}",
            "",
        ]

        # 1. 今日学习内容
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            # 统计对话次数
            dialogues = content.count("### 对话")
            notes = content.count("### 笔记")
            lines.append(f"**学习记录**: {dialogues} 轮对话, {notes} 条笔记")
        else:
            lines.append("**学习记录**: 今日暂无记录")
        lines.append("")

        # 2. 掌握度变化
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        new_learned = [r for r in records if r.attempts == 1]
        due = [r for r in records if r.next_review and r.next_review <= today]

        if practiced:
            avg_level = sum(r.level for r in practiced) / len(practiced)
            lines.append(f"**掌握度**: 平均 {avg_level:.0%}")
        if new_learned:
            lines.append(f"**新学概念**: {len(new_learned)} 个")
        if due:
            lines.append(f"**到期复习**: {len(due)} 个概念")
        lines.append("")

        # 3. 明日推荐
        lines.append("**明日推荐**:")
        weak = mastery_v2.get_weakest_concepts(3)
        for r in weak:
            lines.append(f"- 复习 {r.concept}（掌握度: {r.level:.0%}）")
        lines.append("")
        lines.append("💡 试试「快速练习」开始今日练习。")

        return "\n".join(lines)

    @staticmethod
    def recommend() -> list[str]:
        """推荐今日学习内容"""
        today = datetime.now().strftime("%Y-%m-%d")
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]

        # 优先级: 到期复习 > 薄弱点 > 新概念
        due = [r for r in records if r.next_review and r.next_review <= today]
        weak = mastery_v2.get_weakest_concepts(3)
        untouched = [c.name for c in all_concepts if mastery_v2.get(c.name).attempts == 0]

        recommendations = []
        if due:
            recommendations.append(f"📌 到期复习: {due[0].concept}")
        if weak:
            recommendations.append(f"📌 薄弱点: {weak[0].concept}")
        if untouched:
            recommendations.append(f"📌 新概念: {untouched[0]}")

        return recommendations or ["📌 复习所有已学概念"]


# ============================================================
# 全局实例
# ============================================================

long_term_memory = LongTermMemory()
user_profile = UserProfile()
session_manager = SessionManager()
daily_summary = DailySummary()