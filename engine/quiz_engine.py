# Docker 源码学习系统 — 测验引擎

"""
完整的题库管理、测验生成、自动评分、反馈系统。
"""

import json
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from .knowledge_graph import kg, mastery, MEMORY_DIR

# ============================================================
# 路径
# ============================================================
QUESTIONS_DIR = Path(__file__).parent.parent / "questions"
HISTORY_DIR = QUESTIONS_DIR / "history"

# ============================================================
# 题目数据结构
# ============================================================

QUESTION_TYPES = [
    "multiple_choice",      # 选择题（单选/多选）
    "true_false",           # 判断题
    "fill_blank",           # 填空题
    "code_analysis",        # 代码分析题
    "concept_discrimination", # 概念辨析题
    "design",               # 架构设计题
    "sorting",              # 排序题
]

QUESTION_SCHEMA = {
    "id": "string, 唯一标识",
    "type": "string, 题型",
    "difficulty": "float, 0.0-1.0",
    "body": "string, 题目内容",
    "concepts": ["string, 关联概念"],
    "prerequisites": ["string, 前置知识"],
    "options": ["string, 选项（选择题）"],
    "answer": "string, 正确答案",
    "explanation": "string, 解析",
    "source": "string, 来源（manual/generated/book）",
}


class Question:
    """题目对象"""

    def __init__(self, qid: str, qtype: str, difficulty: float,
                 body: str, concepts: list, answer: str = "",
                 explanation: str = "", options: list = None,
                 prerequisites: list = None, source: str = "manual"):
        self.id = qid
        self.type = qtype
        self.difficulty = difficulty
        self.body = body
        self.concepts = concepts
        self.answer = answer
        self.explanation = explanation
        self.options = options or []
        self.prerequisites = prerequisites or []
        self.source = source

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "difficulty": self.difficulty,
            "body": self.body,
            "concepts": self.concepts,
            "answer": self.answer,
            "explanation": self.explanation,
            "options": self.options,
            "prerequisites": self.prerequisites,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            qid=d["id"], qtype=d["type"], difficulty=d.get("difficulty", 0.5),
            body=d["body"], concepts=d.get("concepts", []),
            answer=d.get("answer", ""), explanation=d.get("explanation", ""),
            options=d.get("options", []), prerequisites=d.get("prerequisites", []),
            source=d.get("source", "manual"),
        )


class QuizSession:
    """测验会话"""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.questions: list[Question] = []
        self.current_index = 0
        self.answers: list[dict] = []  # {"question_id": str, "user_answer": str, "correct": bool, "score": float}
        self.started_at = datetime.now().isoformat()
        self.finished_at: Optional[str] = None
        self.concept_focus = ""
        self.difficulty = 0.5

    @property
    def is_active(self) -> bool:
        return self.finished_at is None and len(self.questions) > 0

    @property
    def current_question(self) -> Optional[Question]:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    @property
    def progress(self) -> str:
        return f"{self.current_index}/{len(self.questions)}"

    @property
    def score(self) -> float:
        if not self.answers:
            return 0.0
        correct = sum(1 for a in self.answers if a.get("correct"))
        return correct / len(self.answers)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "questions": [q.id for q in self.questions],
            "current_index": self.current_index,
            "answers": self.answers,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "concept_focus": self.concept_focus,
            "difficulty": self.difficulty,
            "score": self.score,
        }

    def save(self):
        """保存会话状态"""
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        f = HISTORY_DIR / f"{self.session_id}_{self.started_at[:10]}.jsonl"
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(self.to_dict(), ensure_ascii=False) + "\n")


# ============================================================
# 题库管理器
# ============================================================

class QuestionBank:
    """题库管理器"""

    def __init__(self, data_dir: Path = QUESTIONS_DIR):
        self.data_dir = data_dir
        self.questions: dict[str, Question] = {}
        self._loaded = False

    def load(self):
        """加载所有题目"""
        if self._loaded:
            return

        # 1. 从 EXAMPLES.md 加载
        examples_file = self.data_dir / "EXAMPLES.md"
        if examples_file.exists():
            self._parse_examples(examples_file)

        # 2. 从 manual/ 目录加载
        manual_dir = self.data_dir / "manual"
        if manual_dir.exists():
            for f in manual_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    for item in data if isinstance(data, list) else [data]:
                        q = Question.from_dict(item)
                        self.questions[q.id] = q
                except:
                    pass

        self._loaded = True
        print(f"[题库] 加载完成: {len(self.questions)} 道题")

    def _parse_examples(self, filepath: Path):
        """解析 EXAMPLES.md 中的题目"""
        content = filepath.read_text(encoding="utf-8")
        sections = content.split("\n---\n")

        for section in sections:
            if not section.strip():
                continue

            qid = ""
            qtype = ""
            difficulty = 0.5
            body = ""
            concepts = []
            prerequisites = []
            options = []
            answer = ""
            explanation = ""

            lines = section.strip().split("\n")
            in_options = False
            in_body = False

            for line in lines:
                line = line.strip()

                # 提取题目 ID
                if line.startswith("### Q"):
                    qid = "Q" + line.split("Q")[1].split(":")[0].strip()
                    continue

                # 提取类型
                if line.startswith("**类型**"):
                    type_text = line.split("：")[1] if "：" in line else line.split(":")[1]
                    if "选择" in type_text:
                        qtype = "multiple_choice"
                    elif "判断" in type_text:
                        qtype = "true_false"
                    elif "填空" in type_text:
                        qtype = "fill_blank"
                    elif "代码分析" in type_text:
                        qtype = "code_analysis"
                    elif "概念辨析" in type_text:
                        qtype = "concept_discrimination"
                    elif "设计" in type_text:
                        qtype = "design"
                    elif "排序" in type_text:
                        qtype = "sorting"
                    elif "综合" in type_text:
                        qtype = "design"
                    continue

                # 提取概念
                if line.startswith("**概念**"):
                    concept_text = line.split("：")[1] if "：" in line else line.split(":")[1]
                    concepts = [c.strip().strip("`") for c in concept_text.replace("→", ",").split(",")]
                    continue

                # 提取难度
                if line.startswith("**难度**"):
                    try:
                        diff_text = line.split("：")[1] if "：" in line else line.split(":")[1]
                        difficulty = float(diff_text.strip())
                    except:
                        pass
                    continue

                # 提取前置知识
                if line.startswith("**前置知识**"):
                    pre_text = line.split("：")[1] if "：" in line else line.split(":")[1]
                    prerequisites = [p.strip().strip("`") for p in pre_text.replace("→", ",").split(",")]
                    continue

                # 提取正确答案
                if line.startswith("**正确答案**"):
                    answer = line.split("：")[1] if "：" in line else line.split(":")[1]
                    # 清理格式
                    answer = answer.strip().strip("**").strip("`")
                    continue

                # 提取解析
                if line.startswith("**解析**"):
                    explanation = line.split("：")[1] if "：" in line else line.split(":")[1]
                    continue

                # 提取参考答案
                if line.startswith("**参考答案**"):
                    in_body = False
                    in_options = False
                    answer = line.split("：")[1] if "：" in line else line.split(":")[1]
                    continue

                # 选项
                if re.match(r'^[A-E]\.\s', line):
                    options.append(line)
                    in_options = True
                    continue

                # 题目正文（从 **题目** 到 **参考答案**/**正确答案** 之间）
                if line.startswith("**题目**") or line.startswith("**题目**："):
                    in_body = True
                    continue

                # 停止收集正文
                if line.startswith("**参考答案**") or line.startswith("**正确答案**") or line.startswith("**解析**"):
                    in_body = False
                    continue

                if in_body and line:
                    # 保留代码块，保留问题行，保留所有内容
                    if body:
                        body += "\n" + line
                    else:
                        body = line

            if qid and body:
                q = Question(
                    qid=qid, qtype=qtype, difficulty=difficulty,
                    body=body, concepts=concepts, answer=answer,
                    explanation=explanation, options=options,
                    prerequisites=prerequisites, source="manual",
                )
                self.questions[q.id] = q

    def get_question(self, qid: str) -> Optional[Question]:
        self.load()
        return self.questions.get(qid)

    def get_questions_by_concept(self, concept: str) -> list[Question]:
        """获取关联某个概念的所有题目"""
        self.load()
        results = []
        for q in self.questions.values():
            if any(concept in c or c in concept for c in q.concepts):
                results.append(q)
        return results

    def get_questions_by_difficulty(self, min_diff: float = 0.0,
                                     max_diff: float = 1.0) -> list[Question]:
        """获取指定难度范围的题目"""
        self.load()
        return [q for q in self.questions.values()
                if min_diff <= q.difficulty <= max_diff]

    def generate_quiz(self, concept: str = "", count: int = 3,
                       difficulty: float = 0.5, session_id: str = "default") -> QuizSession:
        """生成测验"""
        self.load()
        session = QuizSession(session_id)
        session.difficulty = difficulty

        # 确定题目范围
        candidates = []
        if concept:
            candidates = self.get_questions_by_concept(concept)
            session.concept_focus = concept

        if not candidates:
            # 从所有题目中选择
            candidates = list(self.questions.values())

        # 按难度筛选
        diff_range = 0.2
        candidates = [q for q in candidates
                      if difficulty - diff_range <= q.difficulty <= difficulty + diff_range]

        # 如果还不够，放宽限制
        if len(candidates) < count:
            candidates = list(self.questions.values())

        # 随机选择
        random.shuffle(candidates)
        selected = candidates[:count]

        # 填充到会话
        session.questions = selected
        session.save()
        return session

    def auto_generate(self, concept_name: str) -> Optional[Question]:
        """从概念自动生成题目"""
        c = kg.get_concept(concept_name)
        if not c:
            return None

        qid = f"auto_{concept_name}_{datetime.now().strftime('%H%M%S')}"

        # 如果有误解，生成判断题
        if c.misconceptions:
            mc = random.choice(c.misconceptions)
            q = Question(
                qid=qid, qtype="true_false", difficulty=c.difficulty,
                body=f"{mc['pattern']}（对/错）",
                concepts=[concept_name],
                answer="错",
                explanation=mc.get("correction", ""),
                source="generated",
            )
            return q

        # 生成选择题
        related = kg.get_related_concepts(concept_name)
        if related:
            distractors = [r.name for r in related[:3]]
            q = Question(
                qid=qid, qtype="multiple_choice", difficulty=c.difficulty,
                body=f"「{concept_name}」在 Docker 架构中的主要作用是什么？",
                concepts=[concept_name],
                answer=c.definition[:80],
                explanation=f"参考：{c.definition}",
                options=[c.definition[:80]] + distractors,
                source="generated",
            )
            return q

        return None


# ============================================================
# 评分器
# ============================================================

class Scorer:
    """自动评分器"""

    @staticmethod
    def score(qtype: str, user_answer: str, correct_answer: str) -> dict:
        """评分，返回 {correct, score, feedback}"""
        if qtype == "true_false":
            return Scorer._score_true_false(user_answer, correct_answer)
        elif qtype == "multiple_choice":
            return Scorer._score_multiple_choice(user_answer, correct_answer)
        elif qtype == "fill_blank":
            return Scorer._score_fill_blank(user_answer, correct_answer)
        elif qtype == "sorting":
            return Scorer._score_sorting(user_answer, correct_answer)
        else:
            # 开放题，语义匹配
            return Scorer._score_open(user_answer, correct_answer)

    @staticmethod
    def _score_true_false(user: str, correct: str) -> dict:
        user_clean = user.strip().lower()
        correct_clean = correct.strip().lower()

        is_correct = (
            (user_clean in ("对", "正确", "true", "t", "yes", "y") and
             correct_clean in ("对", "正确", "true", "t", "yes", "y")) or
            (user_clean in ("错", "错误", "false", "f", "no", "n") and
             correct_clean in ("错", "错误", "false", "f", "no", "n"))
        )

        if is_correct:
            return {"correct": True, "score": 1.0, "feedback": "✅ 回答正确！"}
        else:
            expected = "对" if correct_clean in ("对", "正确", "true") else "错"
            return {
                "correct": False, "score": 0.0,
                "feedback": f"❌ 回答错误。正确答案是：{expected}",
            }

    @staticmethod
    def _score_multiple_choice(user: str, correct: str) -> dict:
        user_clean = user.strip().upper()
        correct_clean = correct.strip().upper()

        if user_clean == correct_clean:
            return {"correct": True, "score": 1.0, "feedback": "✅ 回答正确！"}
        else:
            return {
                "correct": False, "score": 0.0,
                "feedback": f"❌ 回答错误。正确答案是：{correct_clean}",
            }

    @staticmethod
    def _score_fill_blank(user: str, correct: str) -> dict:
        user_clean = user.strip().lower()
        correct_clean = correct.strip().lower()

        # 精确匹配（单关键词短答案，长度接近）
        if user_clean == correct_clean:
            return {"correct": True, "score": 1.0, "feedback": "✅ 完全正确！"}

        # 多关键词场景：逗号分隔的多个答案
        if "," in correct_clean:
            correct_parts = [p.strip() for p in correct_clean.split(",")]
            user_parts = [p.strip() for p in user_clean.replace("，", ",").split(",")]
            matched = sum(1 for cp in correct_parts if any(cp == up for up in user_parts))
            if matched == len(correct_parts):
                return {"correct": True, "score": 1.0, "feedback": "✅ 完全正确！"}
            if matched >= len(correct_parts) * 0.5:
                return {
                    "correct": False, "score": 0.5,
                    "feedback": f"⚠️ 部分正确。正确答案包含：{correct}",
                }
            return {
                "correct": False, "score": 0.0,
                "feedback": f"❌ 回答错误。正确答案是：{correct}",
            }

        # 单关键词：精确匹配
        if len(user_clean) <= len(correct_clean) + 2:
            if user_clean == correct_clean:
                return {"correct": True, "score": 1.0, "feedback": "✅ 完全正确！"}

        # 关键词匹配（长答案/多关键词场景）
        keywords = [k.strip().lower() for k in correct_clean.replace(",", " ").split()
                    if len(k.strip()) > 1]
        matched = sum(1 for k in keywords if k in user_clean)

        # 单关键词时使用精确匹配，避免子串匹配误判
        if len(keywords) == 1:
            if user_clean == keywords[0]:
                return {"correct": True, "score": 1.0, "feedback": "✅ 完全正确！"}
            else:
                return {
                    "correct": False, "score": 0.0,
                    "feedback": f"❌ 回答错误。正确答案是：{correct}",
                }

        if matched >= len(keywords) * 0.7:
            return {"correct": True, "score": 0.8, "feedback": "✅ 基本正确，但可以更精确。"}
        elif matched >= len(keywords) * 0.4:
            return {
                "correct": False, "score": 0.4,
                "feedback": f"⚠️ 部分正确。正确答案：{correct}",
            }
        else:
            return {
                "correct": False, "score": 0.0,
                "feedback": f"❌ 回答错误。正确答案是：{correct}",
            }

    @staticmethod
    def _score_sorting(user: str, correct: str) -> dict:
        user_clean = user.strip().replace("→", " ").replace(">", " ").replace(",", " ")
        correct_clean = correct.strip().replace("→", " ").replace(">", " ").replace(",", " ")

        user_parts = [p.strip() for p in user_clean.split() if p.strip()]
        correct_parts = [p.strip() for p in correct_clean.split() if p.strip()]

        if user_parts == correct_parts:
            return {"correct": True, "score": 1.0, "feedback": "✅ 排序完全正确！"}

        # 部分正确
        correct_count = sum(1 for i, p in enumerate(user_parts)
                           if i < len(correct_parts) and p == correct_parts[i])
        ratio = correct_count / len(correct_parts) if correct_parts else 0
        if ratio >= 0.5:
            return {
                "correct": False, "score": ratio,
                "feedback": f"⚠️ 部分正确（{correct_count}/{len(correct_parts)}）。正确顺序：{correct}",
            }
        return {
            "correct": False, "score": 0.0,
            "feedback": f"❌ 顺序错误。正确顺序：{correct}",
        }

    @staticmethod
    def _score_open(user: str, correct: str) -> dict:
        """开放题评分（基于关键词匹配）"""
        user_lower = user.lower()
        correct_lower = correct.lower()

        # 提取关键词
        keywords = [k.strip().lower() for k in re.split(r'[，。、；：\s\n,.!?]', correct_lower)
                    if len(k.strip()) > 2]
        matched = sum(1 for k in keywords if k in user_lower)

        if len(keywords) == 0:
            return {"correct": True, "score": 1.0, "feedback": "已收到你的回答。"}

        ratio = matched / len(keywords)
        if ratio >= 0.7:
            return {"correct": True, "score": 0.8, "feedback": "✅ 回答得很好，覆盖了大部分要点！"}
        elif ratio >= 0.4:
            return {
                "correct": False, "score": 0.5,
                "feedback": f"⚠️ 回答了一部分要点。参考答案要点：{correct[:100]}",
            }
        else:
            return {
                "correct": False, "score": 0.2,
                "feedback": f"💡 可以参考以下思路：{correct[:100]}",
            }


# ============================================================
# 测验管理器
# ============================================================

class QuizManager:
    """测验管理器"""

    def __init__(self):
        self.bank = QuestionBank()
        self.active_sessions: dict[str, QuizSession] = {}
        self.history: dict[str, list] = {}

    def start_quiz(self, concept: str = "", count: int = 3,
                    difficulty: float = 0.5, session_id: str = "default") -> QuizSession:
        """开始测验"""
        session = self.bank.generate_quiz(
            concept=concept, count=count,
            difficulty=difficulty, session_id=session_id,
        )
        self.active_sessions[session_id] = session
        return session

    def answer_question(self, session_id: str, user_answer: str) -> dict:
        """作答当前题目"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return {"error": "没有活跃的测验会话。试试「出题」开始新测验。"}

        q = session.current_question
        if not q:
            return {"error": "已无更多题目。"}

        # 评分
        result = Scorer.score(q.type, user_answer, q.answer)

        # 记录答案
        session.answers.append({
            "question_id": q.id,
            "user_answer": user_answer,
            "correct": result["correct"],
            "score": result["score"],
        })

        # 更新掌握度
        for c in q.concepts:
            mastery.update(c, result["correct"], q.difficulty)

        # 构建反馈
        feedback = [
            f"## 第 {session.current_index + 1} 题 反馈",
            "",
            f"**{q.body[:80]}**",
            "",
            f"你的回答：{user_answer}",
            f"{result['feedback']}",
            "",
        ]
        if q.explanation:
            feedback.append(f"💡 {q.explanation}")
            feedback.append("")

        # 检查是否还有下一题
        session.current_index += 1
        if session.current_index >= len(session.questions):
            session.finished_at = datetime.now().isoformat()
            session.save()
            feedback.append("---")
            feedback.append(f"### 📊 测验完成！")
            feedback.append(f"总分：{session.score:.0%}（{int(session.score * len(session.answers))}/{len(session.answers)}）")
            feedback.append("")
            # 根据表现给出建议
            if session.score >= 0.8:
                feedback.append("🎉 表现优秀！可以进入下一阶段学习了。")
            elif session.score >= 0.5:
                feedback.append("💪 不错，但有些概念需要巩固。建议复习错题。")
            else:
                feedback.append("📚 需要加强基础。建议重新学习相关概念再做练习。")
            del self.active_sessions[session_id]
        else:
            # 显示下一题
            next_q = session.current_question
            feedback.append("---")
            feedback.append(f"### 下一题（{session.progress}）")
            feedback.append("")
            feedback.append(f"**{next_q.body}**")
            feedback.append("")
            if next_q.options:
                for opt in next_q.options:
                    feedback.append(opt)
            feedback.append("")
            feedback.append("*回复你的答案继续*")

        return {"feedback": "\n".join(feedback), "session": session}

    def get_quiz_status(self, session_id: str = "default") -> str:
        """获取测验状态"""
        session = self.active_sessions.get(session_id)
        if not session:
            return "当前没有活跃的测验。试试「出题」开始。"

        if not session.is_active:
            return "测验已完成。试试「出题」开始新测验。"

        q = session.current_question
        if not q:
            return "测验已全部完成。"

        lines = [
            f"## 📝 测验进行中（{session.progress}）",
            f"概念焦点：{session.concept_focus or '综合'}",
            f"难度：{session.difficulty:.1f}",
            "",
            f"**{q.body}**",
            "",
        ]
        if q.options:
            for opt in q.options:
                lines.append(opt)
        lines.append("")
        lines.append("*回复你的答案继续*")
        return "\n".join(lines)

    def get_history(self, session_id: str = "default", limit: int = 5) -> list[dict]:
        """获取测验历史"""
        history = []
        history_dir = HISTORY_DIR
        if not history_dir.exists():
            return history
        for f in sorted(history_dir.glob(f"{session_id}_*.jsonl"), reverse=True)[:limit]:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            history.append(json.loads(line))
                        except:
                            pass
        return history

    def get_quiz_history_text(self, session_id: str = "default") -> str:
        """获取测验历史文本"""
        history = self.get_history(session_id)
        if not history:
            return "暂无测验记录。"

        lines = ["## 📊 测验历史\n"]
        for h in history:
            score = h.get("score", 0)
            total = len(h.get("questions", []))
            date = h.get("started_at", "")[:10]
            concept = h.get("concept_focus", "综合")
            lines.append(f"- **{date}** | {concept} | {score:.0%} ({total} 题)")

        return "\n".join(lines)


# ============================================================
# 全局实例
# ============================================================

quiz_manager = QuizManager()