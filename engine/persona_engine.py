# Docker 源码学习系统 — 人格预设引擎

"""
多人格教学系统：加载、切换、堆栈、模板渲染、自适应切换。
"""

import json
import re
from pathlib import Path
from typing import Optional

from .knowledge_graph import kg, MEMORY_DIR
from .mastery_engine import mastery_v2

# ============================================================
# 路径
# ============================================================
PERSONAS_DIR = Path(__file__).parent.parent / "personas"


# ============================================================
# 人格定义
# ============================================================

PERSONA_DEFINITIONS = {
    "socratic": {
        "name": "socratic",
        "display_name": "苏格拉底",
        "style": "反问引导，不直接给答案",
        "question_style": "open_ended",
        "visualization_style": "conceptual",
        "code_preference": "minimal",
        "description": "用反问引导你自己发现答案，适合喜欢思考的学习者",
        "tags": ["思考型", "推理", "基础"],
        "system_prompt": """你是一个苏格拉底式的导师。你的核心教学方法是反问。

规则：
1. 从不直接给答案。用问题引导用户自己发现答案。
2. 当用户说"我不懂"时，先问"你觉得哪里开始不懂的？"
3. 每个问题追问至少 2-3 轮，确保用户真正理解。
4. 如果用户连续答错 3 次，才给出提示，但不要直接给答案。""",
    },
    "professor": {
        "name": "professor",
        "display_name": "教授",
        "style": "系统化、结构化、严谨",
        "question_style": "structured",
        "visualization_style": "systematic",
        "code_preference": "detailed",
        "description": "系统化、结构化教学，适合喜欢严格知识体系的学习者",
        "tags": ["系统化", "严谨", "深入"],
        "system_prompt": """你是一个大学教授，正在讲授《Docker 源码分析》课程。

规则：
1. 每次讲解先给出大纲，再逐一展开。
2. 使用"首先、其次、最后"等结构化的表达。
3. 每个概念都要给出精确定义。
4. 引用源码时标注文件路径和行号。
5. 每讲完一个知识点，做一个小结。""",
    },
    "practitioner": {
        "name": "practitioner",
        "display_name": "实践者",
        "style": "代码驱动、动手导向",
        "question_style": "code_focused",
        "visualization_style": "code_flow",
        "code_preference": "always_show",
        "description": "代码驱动，动手实践，适合喜欢边做边学的学习者",
        "tags": ["动手", "实战", "代码"],
        "system_prompt": """你是一个经验丰富的 Docker 贡献者，相信"代码是最好的文档"。

规则：
1. 优先用代码说明问题。
2. 每次讲解先打开实际源码文件。
3. 鼓励用户自己修改代码试试。
4. 分享实际开发中的经验和坑。
5. 提供可运行的代码片段和调试技巧。""",
    },
    "storyteller": {
        "name": "storyteller",
        "display_name": "说书人",
        "style": "类比驱动、故事化",
        "question_style": "analogy_based",
        "visualization_style": "narrative",
        "code_preference": "minimal",
        "description": "用故事和比喻讲解技术，适合喜欢直观理解的初学者",
        "tags": ["直观", "类比", "入门"],
        "system_prompt": """你是一个讲故事的人，用比喻和故事来解释技术概念。

规则：
1. 每个概念先用一个生活化的比喻引入。
2. 比喻要贴切，不能歪曲技术本质。
3. 讲完故事后，再映射到技术细节。
4. 故事要有趣，让人容易记住。
5. 复杂的流程用"角色扮演"的方式讲。""",
    },
    "coach": {
        "name": "coach",
        "display_name": "教练",
        "style": "目标导向、激励驱动",
        "question_style": "progressive",
        "visualization_style": "progress_tracking",
        "code_preference": "balanced",
        "description": "目标导向，关注进度，适合需要监督和激励的学习者",
        "tags": ["目标", "激励", "进度"],
        "system_prompt": """你是一个学习教练，关注用户的进步和动力。

规则：
1. 每次学习开始前设定明确目标。
2. 把大目标拆成小步骤。
3. 及时肯定用户的进步。
4. 遇到困难时，鼓励但不催促。
5. 定期回顾学习进度。""",
    },
    "debugger": {
        "name": "debugger",
        "display_name": "调试者",
        "style": "问题导向、逆向思考",
        "question_style": "problem_based",
        "visualization_style": "debugging_flow",
        "code_preference": "trace_level",
        "description": "从问题出发逆向分析，适合喜欢调试和追根究底的学习者",
        "tags": ["问题", "逆向", "调试"],
        "system_prompt": """你是一个调试专家，擅长从问题中学习。

规则：
1. 遇到问题先问"什么现象？"
2. 从现象反推代码路径。
3. 用"假设-验证"的方式引导思考。
4. 教用户如何阅读错误日志和调用栈。
5. 分享调试工具和技巧。""",
    },
    "minimalist": {
        "name": "minimalist",
        "display_name": "极简者",
        "style": "最简回答、直奔重点",
        "question_style": "concise",
        "visualization_style": "minimal",
        "code_preference": "key_lines_only",
        "description": "直奔重点，少即是多，适合想快速获取答案的复习者",
        "tags": ["简洁", "高效", "复习"],
        "system_prompt": """你是一个极简主义者，相信"少即是多"。

规则：
1. 用最少的文字回答核心问题。
2. 每个回答不超过 3 句话。
3. 只回答用户问的，不扩展。
4. 用代码代替解释（如果代码更简洁）。
5. 用户需要更多细节时，主动问。""",
    },
    "devils_advocate": {
        "name": "devils_advocate",
        "display_name": "唱反调",
        "style": "挑战观点、引发批判性思考",
        "question_style": "debate",
        "visualization_style": "comparison",
        "code_preference": "balanced",
        "description": "挑战你的观点，适合想深入理解技术边界的高级学习者",
        "tags": ["批判", "辩论", "高级"],
        "system_prompt": """你是一个"唱反调"的角色，专门挑战用户已有的观点，促进深度思考。

规则：
1. 当用户表达肯定观点时，主动提出反例。
2. 挑战热门观点和"最佳实践"。
3. 引导用户从多个角度思考问题。
4. 不为了反对而反对，每个反论都有依据。
5. 通过辩论帮助用户建立更全面的理解。""",
    },
}


# ============================================================
# 人格引擎
# ============================================================

class PersonaEngine:
    """人格预设引擎"""

    def __init__(self):
        self.personas = PERSONA_DEFINITIONS
        self.stack = []  # 人格栈，支持回溯

    def list_personas(self) -> list[dict]:
        """列出所有可用人格"""
        return [{
            "id": p["name"],
            "name": p["display_name"],
            "style": p["style"],
            "description": p["description"],
            "tags": p["tags"],
        } for p in self.personas.values()]

    def get_persona(self, persona_id: str) -> Optional[dict]:
        """获取人格定义"""
        return self.personas.get(persona_id)

    def switch(self, persona_id: str, context_persona: str,
               push_to_stack: bool = True) -> str:
        """切换人格，返回切换消息"""
        if persona_id not in self.personas:
            available = ", ".join([p["display_name"] for p in self.personas.values()])
            return f"❌ 未知人格「{persona_id}」。可用：{available}"

        if push_to_stack and context_persona:
            self.stack.append(context_persona)

        p = self.personas[persona_id]
        return f"✅ 已切换到「{p['display_name']}」风格\n*{p['style']}*"

    def pop_stack(self) -> Optional[str]:
        """弹出上一人格"""
        if self.stack:
            return self.stack.pop()
        return None

    def get_stack_depth(self) -> int:
        return len(self.stack)

    def get_stack_info(self) -> list[str]:
        """获取人格栈信息"""
        result = []
        for i, pid in enumerate(self.stack):
            p = self.personas.get(pid)
            name = p["display_name"] if p else pid
            result.append(f"{i+1}. {name}")
        return result

    def get_persona_description(self, persona_id: str) -> str:
        """获取人格的详细描述"""
        p = self.personas.get(persona_id)
        if not p:
            return "未知人格"
        lines = [
            f"## 🎭 {p['display_name']}",
            f"*{p['style']}*",
            "",
            f"**描述**: {p['description']}",
            f"**提问风格**: {p['question_style']}",
            f"**可视化风格**: {p['visualization_style']}",
            f"**代码偏好**: {p['code_preference']}",
            f"**标签**: {', '.join(p['tags'])}",
            "",
            f"**教学风格**:",
            p["system_prompt"],
        ]
        return "\n".join(lines)

    def recommend_persona(self, context: dict) -> str:
        """根据学习上下文推荐人格"""
        # 基于掌握度
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0

        # 基于当前阶段
        if avg_level < 0.3:
            # 初学者 → 说书人 or 苏格拉底
            return "storyteller"
        elif avg_level < 0.6:
            # 进阶 → 教授 or 实践者
            return "professor"
        elif avg_level < 0.8:
            # 中等 → 教练 or 调试者
            return "coach"
        else:
            # 高级 → 唱反调 or 极简者
            return "devils_advocate"

    def apply_persona_style(self, response: str, persona_id: str) -> str:
        """根据人格风格调整响应格式"""
        p = self.personas.get(persona_id)
        if not p:
            return response

        style = p["question_style"]

        if style == "concise":
            # 极简风格：只保留前 3 句
            lines = response.strip().split("\n")
            non_empty = [l for l in lines if l.strip()]
            return "\n".join(non_empty[:3])

        if style == "structured":
            # 教授风格：确保有标题结构
            if not response.startswith("##"):
                response = f"## 讲解\n\n{response}"
            return response

        if style == "code_focused":
            # 实践者风格：确保有代码块
            if "```" not in response:
                # 尝试添加代码引用
                response += "\n\n```go\n// 相关源码位置：\n// cmd/dockerd/dockerd.go\n```"
            return response

        if style == "analogy_based":
            # 说书人风格：确保有比喻引导
            if "比喻" not in response and "就像" not in response:
                response = f"💡 让我用一个比喻来说明：\n\n{response}"
            return response

        return response


# ============================================================
# 学习路径引擎
# ============================================================

class LearningPathEngine:
    """自适应学习路径引擎"""

    def __init__(self):
        self.paths = {}  # concept -> list of recommended concepts in order

    def _build_prerequisite_graph(self) -> dict:
        """构建先修知识图谱"""
        all_concepts = kg.get_all_concepts()
        graph = {}
        for c in all_concepts:
            prerequisites = []
            for rel_name, rel_targets in c.relations.items():
                # 如果有关联关系，记录为潜在的先修
                if "依赖" in rel_name or "基础" in rel_name or "包含" in rel_name:
                    for target in rel_targets:
                        prerequisites.append(target)
            graph[c.name] = prerequisites
        return graph

    def assess(self) -> dict:
        """评估用户当前水平"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]

        total = len(all_concepts)
        learned = len(practiced)
        mastered = len([r for r in practiced if r.level >= 0.7])
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0

        if avg_level < 0.3:
            stage = "初学者"
        elif avg_level < 0.6:
            stage = "进阶者"
        elif avg_level < 0.8:
            stage = "熟练者"
        else:
            stage = "专家"

        weak = mastery_v2.get_weakest_concepts(5)
        strong = sorted([r for r in practiced if r.level >= 0.7],
                        key=lambda x: x.level, reverse=True)[:5]

        return {
            "stage": stage,
            "total_concepts": total,
            "learned_concepts": learned,
            "mastered_concepts": mastered,
            "average_level": avg_level,
            "weak_spots": [r.concept for r in weak],
            "strong_spots": [r.concept for r in strong],
        }

    def plan_path(self, target_concept: str = "") -> list[dict]:
        """规划学习路径"""
        all_concepts = kg.get_all_concepts()
        concept_map = {c.name: c for c in all_concepts}

        if target_concept and target_concept in concept_map:
            # 从目标概念 BFS 寻找先修路径
            target = concept_map[target_concept]
            path = self._bfs_prerequisites(target, concept_map)
        else:
            # 全局路径：按难度分组
            path = self._global_path(concept_map)

        return path

    def _bfs_prerequisites(self, target, concept_map) -> list[dict]:
        """BFS 寻找先修路径"""
        visited = set()
        queue = [target]
        order = []

        while queue:
            current = queue.pop(0)
            if current.name in visited:
                continue
            visited.add(current.name)

            # 找先修概念
            prereqs = []
            for rel_name, rel_targets in current.relations.items():
                if "依赖" in rel_name or "基础" in rel_name:
                    for t in rel_targets:
                        if t in concept_map:
                            prereqs.append(concept_map[t])

            for p in prereqs:
                if p.name not in visited:
                    queue.append(p)

            order.append(current)

        # 反转：先修在前
        order.reverse()

        return [{
            "concept": c.name,
            "status": "未学",
            "level": 0,
        } for c in order]

    def _global_path(self, concept_map) -> list[dict]:
        """全局路径：按分组推荐"""
        all_concepts = kg.get_all_concepts()

        # 分组
        groups = {
            "基础": [],
            "核心": [],
            "进阶": [],
            "深入": [],
        }

        for c in all_concepts:
            rec = mastery_v2.get(c.name)
            if any(kw in c.name for kw in ["容器", "镜像", "Docker"]):
                groups["基础"].append(c)
            elif any(kw in c.name for kw in ["运行时", "存储", "网络"]):
                groups["核心"].append(c)
            elif any(kw in c.name for kw in ["构建", "编排", "安全"]):
                groups["进阶"].append(c)
            else:
                groups["深入"].append(c)

        path = []
        for group_name, concepts in groups.items():
            for c in concepts:
                rec = mastery_v2.get(c.name)
                if rec.attempts > 0:
                    status = "已学" if rec.level >= 0.7 else "学习中"
                else:
                    status = "未学"
                path.append({
                    "concept": c.name,
                    "group": group_name,
                    "status": status,
                    "level": rec.level,
                    "next_review": rec.next_review or "",
                })

        return path

    def recommend_next(self, context: dict) -> dict:
        """推荐下一步学习内容"""
        all_concepts = kg.get_all_concepts()

        # 1. 到期复习优先
        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        due = [c.name for c in all_concepts
               if mastery_v2.get(c.name).next_review
               and mastery_v2.get(c.name).next_review <= today]

        if due:
            return {
                "type": "复习",
                "concept": due[0],
                "reason": "到期复习",
                "action": "复习",
            }

        # 2. 薄弱点优先
        weak = mastery_v2.get_weakest_concepts(3)
        attempted = [r for r in weak if r.attempts > 0]
        if attempted:
            return {
                "type": "强化",
                "concept": attempted[0].concept,
                "reason": f"薄弱点（掌握度 {attempted[0].level:.0%}）",
                "action": "练习",
            }

        # 3. 未学概念
        untouched = [c for c in all_concepts if mastery_v2.get(c.name).attempts == 0]
        if untouched:
            return {
                "type": "新学",
                "concept": untouched[0].name,
                "reason": "新概念探索",
                "action": "学习",
            }

        # 4. 复习已学
        return {
            "type": "复习",
            "concept": all_concepts[0].name,
            "reason": "系统性复习",
            "action": "复习",
        }

    def adapt_path(self, context: dict) -> list[dict]:
        """根据当前掌握度调整学习路径"""
        path = self.plan_path()
        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")

        for item in path:
            rec = mastery_v2.get(item["concept"])
            item["level"] = rec.level
            if rec.attempts > 0:
                item["status"] = "已学" if rec.level >= 0.7 else "学习中"
            if rec.next_review and rec.next_review <= today:
                item["status"] = "待复习"

        return path


# ============================================================
# 全局实例
# ============================================================

persona_engine = PersonaEngine()
learning_path = LearningPathEngine()