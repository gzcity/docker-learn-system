# Docker 源码学习系统 — 掌握度引擎

"""
SM-2 间隔重复算法 + 遗忘曲线 + 关联传播 + 掌握度预测。
升级替换 knowledge_graph.py 中基础的 MasteryManager。
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .knowledge_graph import (
    kg, MEMORY_DIR, MasteryRecord
)

# ============================================================
# SM-2 参数
# ============================================================
SM2_DEFAULT_EF = 2.5  # 默认易度因子
SM2_MIN_EF = 1.3      # 最小易度因子
SM2_INTERVALS = [1, 6]  # 初次复习间隔（天）：第1次1天，第2次6天
SM2_MAX_INTERVAL = 365  # 最大间隔
DECAY_RATE = 0.02      # 遗忘曲线衰减率
PROPAGATION_RATE = 0.3 # 关联概念传播率


# ============================================================
# 增强掌握度记录
# ============================================================

class EnhancedMasteryRecord(MasteryRecord):
    """SM-2 增强版掌握度记录"""

    def __init__(self, concept: str, level: float = 0.0,
                 attempts: int = 0, correct: int = 0,
                 last_practiced: str = "", next_review: str = "",
                 easiness: float = SM2_DEFAULT_EF,
                 interval: int = 0,
                 repetitions: int = 0,  # 连续正确次数
                 history: list = None):
        super().__init__(concept, level, attempts, correct,
                         last_practiced, next_review)
        self.easiness = easiness        # SM-2 易度因子
        self.interval = interval        # 当前间隔（天）
        self.repetitions = repetitions  # 连续正确次数
        self.history = history or []    # 练习历史 [(date, correct, score)]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "easiness": self.easiness,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "history": self.history,
        })
        return d


# ============================================================
# SM-2 算法
# ============================================================

def sm2_update(record: EnhancedMasteryRecord, q: int) -> dict:
    """
    SM-2 间隔重复算法。
    q: 质量评分 (0-5)
      - 0: 完全忘记
      - 1: 错误，但看到答案后记住了
      - 2: 错误，但答案不难
      - 3: 正确，但费力
      - 4: 正确，有点犹豫
      - 5: 完全正确，轻松
    返回: delta 信息
    """
    new_ef = record.easiness + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = max(SM2_MIN_EF, new_ef)

    if q >= 3:
        # 正确
        if record.repetitions == 0:
            new_interval = 1
        elif record.repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(record.interval * new_ef)
        new_interval = min(new_interval, SM2_MAX_INTERVAL)
        new_repetitions = record.repetitions + 1
    else:
        # 错误
        new_interval = 1
        new_repetitions = 0

    return {
        "easiness": new_ef,
        "interval": new_interval,
        "repetitions": new_repetitions,
        "next_review": (datetime.now() + timedelta(days=new_interval)).strftime("%Y-%m-%d"),
    }


# ============================================================
# 遗忘曲线
# ============================================================

def forgetting_curve(elapsed_days: float, level: float) -> float:
    """
    遗忘曲线：基于 Ebbinghaus 遗忘曲线。
    返回当前记忆保留率 (0-1)。
    """
    if elapsed_days <= 0:
        return 1.0
    # 指数衰减: R = e^(-t/S)
    # S = 强度 = 基础强度 * (1 + level * 10)
    strength = 1 + level * 10
    retention = math.exp(-DECAY_RATE * elapsed_days / strength)
    return max(0.0, retention)


def get_retention_rate(record: EnhancedMasteryRecord) -> float:
    """计算当前记忆保留率"""
    if not record.last_practiced:
        return 1.0
    try:
        last = datetime.strptime(record.last_practiced, "%Y-%m-%d")
        elapsed = (datetime.now() - last).days
        return forgetting_curve(elapsed, record.level)
    except:
        return 1.0


# ============================================================
# 掌握度管理器 (升级版)
# ============================================================

class MasteryManagerV2:
    """
    SM-2 间隔重复掌握度管理器。
    替换 knowledge_graph 中的基础 MasteryManager。
    """

    def __init__(self, data_dir: Path = MEMORY_DIR):
        self.data_dir = data_dir
        self.records: dict[str, EnhancedMasteryRecord] = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        f = self.data_dir / "mastery.json"
        if f.exists():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for item in data:
                    r = EnhancedMasteryRecord(
                        concept=item["concept"],
                        level=item.get("level", 0.0),
                        attempts=item.get("attempts", 0),
                        correct=item.get("correct", 0),
                        last_practiced=item.get("last_practiced", ""),
                        next_review=item.get("next_review", ""),
                        easiness=item.get("easiness", SM2_DEFAULT_EF),
                        interval=item.get("interval", 0),
                        repetitions=item.get("repetitions", 0),
                        history=item.get("history", []),
                    )
                    r.misconceptions_corrected = item.get("misconceptions_corrected", [])
                    self.records[r.concept] = r
            except Exception as e:
                print(f"[掌握度V2] 加载失败: {e}")
        self._loaded = True

    def save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self.records.values()]
        (self.data_dir / "mastery.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, concept: str) -> EnhancedMasteryRecord:
        self.load()
        if concept not in self.records:
            self.records[concept] = EnhancedMasteryRecord(concept=concept)
        return self.records[concept]

    def update(self, concept: str, correct: bool, difficulty: float = 0.5):
        """SM-2 更新掌握度"""
        record = self.get(concept)
        record.attempts += 1
        if correct:
            record.correct += 1

        # 将正确/错误转为 SM-2 质量评分
        q = 4 if correct else 1
        # 根据难度调整
        if difficulty > 0.7:
            q = max(0, q - 1)  # 难题降低评分
        elif difficulty < 0.3:
            q = min(5, q + 1)  # 简单题提高评分

        # SM-2 更新
        sm2_result = sm2_update(record, q)
        record.easiness = sm2_result["easiness"]
        record.interval = sm2_result["interval"]
        record.repetitions = sm2_result["repetitions"]
        record.next_review = sm2_result["next_review"]

        # 掌握度计算：基于重复次数和正确率
        if record.attempts > 0:
            accuracy = record.correct / record.attempts
            retention = min(1.0, record.interval / 30) if record.interval > 0 else 0.1
            # 掌握度 = 正确率 * 0.6 + 间隔衰减 * 0.4
            record.level = accuracy * 0.6 + min(1.0, retention) * 0.4

        record.last_practiced = datetime.now().strftime("%Y-%m-%d")

        # 记录历史
        record.history.append({
            "date": record.last_practiced,
            "correct": correct,
            "q": q,
            "level": round(record.level, 3),
        })

        # 关联传播：更新相关概念
        self._propagate_update(concept, correct)
        self.save()

    def _propagate_update(self, concept: str, correct: bool):
        """关联概念掌握度传播"""
        c = kg.get_concept(concept)
        if not c:
            # 尝试模糊匹配
            matches = kg.search_concepts(concept)
            if matches:
                c = matches[0]
            else:
                return

        delta = 0.02 if correct else -0.01
        for related_name in c.related:
            related_record = self.get(related_name.strip())
            if related_record.attempts == 0:
                # 从未练习过的关联概念，获得部分掌握度
                related_record.level = max(0.0, min(1.0, related_record.level + delta * PROPAGATION_RATE))

    def record_misconception(self, concept: str, pattern: str):
        record = self.get(concept)
        record.misconceptions_corrected.append({
            "pattern": pattern,
            "corrected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        record.level = max(0.0, record.level - 0.1)
        self.save()

    def get_weakest_concepts(self, top_n: int = 5) -> list[EnhancedMasteryRecord]:
        self.load()
        practiced = [r for r in self.records.values() if r.attempts > 0]
        unpracticed = [r for r in self.records.values() if r.attempts == 0 and r.level < 0.3]
        combined = sorted(practiced, key=lambda r: r.level) + sorted(unpracticed, key=lambda r: r.level)
        return combined[:top_n]

    def get_due_reviews(self) -> list[EnhancedMasteryRecord]:
        """获取到期复习的概念"""
        self.load()
        today = datetime.now().strftime("%Y-%m-%d")
        return [r for r in self.records.values()
                if r.attempts > 0 and r.next_review and r.next_review <= today]

    def get_retention_summary(self) -> list[dict]:
        """获取所有概念的保留率摘要"""
        self.load()
        summaries = []
        for name, record in self.records.items():
            retention = get_retention_rate(record)
            c = kg.get_concept(name)
            summaries.append({
                "concept": name,
                "level": record.level,
                "retention": retention,
                "attempts": record.attempts,
                "next_review": record.next_review,
                "difficulty": c.difficulty if c else 0.5,
                "status": self._get_status(record, retention),
            })
        return summaries

    @staticmethod
    def _get_status(record: EnhancedMasteryRecord, retention: float) -> str:
        if record.attempts == 0:
            return "未学习"
        if record.next_review and record.next_review <= datetime.now().strftime("%Y-%m-%d"):
            return "待复习"
        if retention < 0.5:
            return "需巩固"
        if record.level >= 0.8:
            return "精通"
        if record.level >= 0.5:
            return "进行中"
        return "初学"

    def predict_next_review(self, concept: str) -> str:
        """预测下次复习时间"""
        record = self.get(concept)
        if record.attempts == 0:
            return "尚未练习，建议立即开始学习"
        if record.next_review:
            today = datetime.now()
            try:
                review_date = datetime.strptime(record.next_review, "%Y-%m-%d")
                days_left = (review_date - today).days
                if days_left < 0:
                    return f"已过期 {abs(days_left)} 天，建议立即复习"
                elif days_left == 0:
                    return "今天应复习"
                else:
                    return f"{days_left} 天后应复习"
            except:
                pass
        return "未知"


# ============================================================
# 练习计划
# ============================================================

class PracticePlanner:
    """练习计划生成器"""

    def __init__(self, mastery: MasteryManagerV2):
        self.mastery = mastery

    def plan_daily(self, count: int = 5) -> list[dict]:
        """生成每日练习计划"""
        # 优先级：到期复习 > 薄弱点 > 关联概念 > 未学习
        plan = []

        # 1. 到期复习
        due = self.mastery.get_due_reviews()
        due = sorted(due, key=lambda r: r.interval or 0)[:3]
        for r in due:
            plan.append({
                "concept": r.concept,
                "reason": "到期复习",
                "priority": 1,
                "retention": get_retention_rate(r),
            })

        # 2. 薄弱点
        weak = self.mastery.get_weakest_concepts(5)
        for r in weak:
            if r.concept not in [p["concept"] for p in plan]:
                plan.append({
                    "concept": r.concept,
                    "reason": "掌握度薄弱",
                    "priority": 2,
                    "retention": get_retention_rate(r),
                })

        # 3. 未学习
        concepts = kg.get_all_concepts()
        for c in concepts:
            record = self.mastery.get(c.name)
            if record.attempts == 0 and c.name not in [p["concept"] for p in plan]:
                plan.append({
                    "concept": c.name,
                    "reason": "未学习",
                    "priority": 3,
                    "retention": 1.0,
                })

        return plan[:count]

    def suggest_concepts(self, count: int = 3) -> list[str]:
        """建议需要练习的概念"""
        plan = self.plan_daily(count)
        return [p["concept"] for p in plan]


# ============================================================
# 练习报告
# ============================================================

class PracticeReport:
    """练习报告生成器"""

    @staticmethod
    def generate_text(concepts: list[str], mastery: MasteryManagerV2) -> str:
        """为指定概念生成练习报告"""
        lines = []
        for concept_name in concepts:
            record = mastery.get(concept_name)
            retention = get_retention_rate(record)
            c = kg.get_concept(concept_name)

            bars = "█" * int(record.level * 20) + "░" * (20 - int(record.level * 20))
            retention_bars = "█" * int(retention * 20) + "░" * (20 - int(retention * 20))

            lines.append(f"**{concept_name}**")
            lines.append(f"  掌握度: {bars} {record.level:.0%}")
            lines.append(f"  记忆率: {retention_bars} {retention:.0%}")
            if record.attempts > 0:
                lines.append(f"  练习: {record.attempts} 次, 正确率: {record.accuracy:.0%}")
                lines.append(f"  间隔: {record.interval} 天, EF: {record.easiness:.2f}")
                lines.append(f"  下次复习: {record.next_review or '未安排'}")
            else:
                lines.append(f"  状态: 未练习")
            if c and c.difficulty:
                diff_stars = "⭐" * int(c.difficulty * 5)
                lines.append(f"  难度: {diff_stars}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_mermaid_heatmap(concepts: list[str], mastery: MasteryManagerV2) -> str:
        """生成 Mermaid 热力图"""
        lines = [
            "```mermaid",
            "%%{init: {'theme': 'base', 'themeVariables': {'primaryBorderColor': '#333'}}}%%",
            "gantt",
            f"    title 掌握度热力图 ({datetime.now().strftime('%Y-%m-%d')})",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat  %m/%d",
            "",
        ]

        for concept_name in concepts:
            record = mastery.get(concept_name)
            level = record.level
            # 根据掌握度选择颜色
            if level >= 0.8:
                section = "精通"
            elif level >= 0.5:
                section = "进行中"
            else:
                section = "需加强"

            days = max(1, record.interval or 1)
            start = record.last_practiced or datetime.now().strftime("%Y-%m-%d")
            lines.append(f"    section {section}")

            label = f"{concept_name[:15]} ({level:.0%})"
            lines.append(f"    {label} :{start}, {days}d")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def generate_overview(mastery: MasteryManagerV2) -> str:
        """生成总览报告"""
        all_concepts = kg.get_all_concepts()
        total = len(all_concepts)
        records = [mastery.get(c.name) for c in all_concepts]

        attempted = sum(1 for r in records if r.attempts > 0)
        avg_level = sum(r.level for r in records) / total if total > 0 else 0
        due = len(mastery.get_due_reviews())
        weak = mastery.get_weakest_concepts(3)

        # 掌握度分布
        levels = {"精通 (≥80%)": 0, "进行中 (50-79%)": 0, "需加强 (20-49%)": 0, "未学习 (<20%)": 0}
        for r in records:
            if r.level >= 0.8:
                levels["精通 (≥80%)"] += 1
            elif r.level >= 0.5:
                levels["进行中 (50-79%)"] += 1
            elif r.level >= 0.2:
                levels["需加强 (20-49%)"] += 1
            else:
                levels["未学习 (<20%)"] += 1

        # 进度条
        pct = attempted / total * 100 if total > 0 else 0
        bar_len = 30
        filled = int(pct / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        lines = [
            "## 📊 掌握度总览",
            "",
            f"**学习进度**",
            f"[{bar}] {attempted}/{total} ({pct:.0f}%)",
            "",
            f"**平均掌握度**: {avg_level:.0%}",
            f"**到期复习**: {due} 个概念",
            "",
            "**掌握度分布**:",
        ]
        for label, count in levels.items():
            bar = "█" * count + "░" * (max(10, total) - count)
            lines.append(f"  {label}: {bar} {count}")

        if weak:
            lines.append("")
            lines.append("**需要加强**:")
            for r in weak:
                lines.append(f"  - {r.concept} (掌握度: {r.level:.0%})")

        lines.append("")
        lines.append("💡 试试「练习」开始每日练习，或「复习」巩固错题。")

        return "\n".join(lines)


# ============================================================
# 练习会话
# ============================================================

class PracticeSession:
    """练习会话管理器"""

    def __init__(self, mastery: MasteryManagerV2):
        self.mastery = mastery
        self.planner = PracticePlanner(mastery)
        self.mode = "quick"  # quick | deep | review
        self.concepts: list[str] = []
        self.current_index = 0
        self.results: list[dict] = []

    def start_quick(self, count: int = 5) -> list[str]:
        """快速模式：从到期复习和薄弱点选择"""
        self.mode = "quick"
        plan = self.planner.plan_daily(count)
        self.concepts = [p["concept"] for p in plan]
        self.current_index = 0
        self.results = []
        return self.concepts

    def start_deep(self, concept: str) -> list[str]:
        """深度模式：深入某个概念及其关联"""
        self.mode = "deep"
        visited = [concept]
        c = kg.get_concept(concept)
        if c:
            for rel in c.related[:3]:
                visited.append(rel.strip())
        self.concepts = visited
        self.current_index = 0
        self.results = []
        return self.concepts

    def start_review(self) -> list[str]:
        """复习模式：只复习到期和薄弱点"""
        self.mode = "review"
        due = self.mastery.get_due_reviews()
        weak = self.mastery.get_weakest_concepts(5)
        reviewed = set()
        for r in due + weak:
            if r.concept not in reviewed:
                reviewed.add(r.concept)
        self.concepts = list(reviewed)[:5]
        self.current_index = 0
        self.results = []
        return self.concepts

    @property
    def current_concept(self) -> str:
        if 0 <= self.current_index < len(self.concepts):
            return self.concepts[self.current_index]
        return ""

    @property
    def progress(self) -> str:
        return f"{self.current_index}/{len(self.concepts)}"

    @property
    def is_active(self) -> bool:
        return self.current_index < len(self.concepts)

    def record_result(self, correct: bool, difficulty: float = 0.5):
        """记录练习结果"""
        concept = self.current_concept
        self.mastery.update(concept, correct, difficulty)
        self.results.append({
            "concept": concept,
            "correct": correct,
            "timestamp": datetime.now().isoformat(),
        })
        self.current_index += 1

    def get_report(self) -> str:
        """生成练习报告"""
        total = len(self.results)
        correct = sum(1 for r in self.results if r["correct"])
        if total == 0:
            return "暂无练习记录。"

        concepts_practiced = [r["concept"] for r in self.results]
        summaries = [self.mastery.get(c) for c in concepts_practiced]

        lines = [
            f"## 📝 练习报告 ({self.mode}模式)",
            "",
            f"完成: {correct}/{total} 正确",
            f"得分: {correct/total:.0%}",
            "",
            "**概念掌握度变化**:",
        ]
        for r, s in zip(self.results, summaries):
            status = "✅" if r["correct"] else "❌"
            lines.append(f"  {status} {r['concept']}: 掌握度 {s.level:.0%}")

        return "\n".join(lines)


# ============================================================
# 全局实例
# ============================================================

mastery_v2 = MasteryManagerV2()
practice_planner = PracticePlanner(mastery_v2)
practice_report = PracticeReport()