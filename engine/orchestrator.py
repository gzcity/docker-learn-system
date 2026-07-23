# Docker 学习系统 — 主编排器

"""
Docker 源码学习系统的核心编排器。
负责：意图识别、Agent 路由、上下文管理、学习流程控制。
集成 P2 题库 + 测验引擎。
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.knowledge_graph import (
    kg, mastery, daily_log, create_context, initialize,
    SessionContext, Concept, MasteryRecord
)
from engine.knowledge_base import (
    kb, bm, nm, NOTES_DIR, KnowledgeBase, BookManager, NoteManager
)
from engine.quiz_engine import quiz_manager, QuestionBank, QuizSession, Scorer
from engine.mastery_engine import (
    mastery_v2, practice_planner, practice_report, PracticeSession,
    PracticeReport, get_retention_rate,
)
from engine.visualization_engine import viz, VisualizationEngine
from engine.research_engine import research, ResearchEngine
from engine.memory_engine import (
    long_term_memory, user_profile, session_manager, daily_summary,
    LongTermMemory, UserProfile, SessionManager, DailySummary,
)
from engine.persona_engine import (
    persona_engine, learning_path,
    PersonaEngine, LearningPathEngine,
)
from engine.dashboard_engine import (
    dashboard, flow_engine, system_commands, ux,
    DashboardEngine, FlowEngine, SystemCommands, UXEngine,
)


# ============================================================
# 意图识别
# ============================================================

INTENT_PATTERNS = {
    "concept_question": [
        "什么是", "解释一下", "讲讲", "说说", "介绍", "了解",
        "what is", "explain", "tell me about",
    ],
    "deep_dive": [
        "深入", "源码", "底层原理", "如何工作", "工作原理",
        "under the hood", "source code",
    ],
    "quiz_start": [
        "出题", "考考", "测验", "考试", "来点题",
        "quiz", "test me", "exam",
    ],
    "quiz_status": [
        "当前题目", "当前测验", "我的题目",
        "quiz status", "current question",
    ],
    "quiz_history": [
        "测验历史", "测试历史", "历史记录", "答题记录", "做题记录",
        "quiz history", "test history",
    ],
    "practice": [
        "练习", "复习", "做题", "巩固",
        "practice", "review",
    ],
    "practice_quick": [
        "快速练习", "每日练习", "今天练什么",
        "quick practice", "daily practice",
    ],
    "practice_deep": [
        "深度练习", "深入练习",
        "deep practice", "deep review",
    ],
    "practice_review": [
        "复习", "错题",
        "review", "wrong",
    ],
    "practice_report": [
        "练习报告", "做题报告",
        "practice report", "exercise report",
    ],
    "mastery_view": [
        "掌握度", "学习进度", "学到哪",
        "mastery", "overview", "progress",
    ],
    "mastery_heatmap": [
        "热力图", "掌握度图",
        "heatmap", "mastery chart",
    ],
    "research": [
        "研究", "深度研究", "研究报告", "分析",
        "research", "deep research", "analysis",
    ],
    "source_analysis": [
        "源码分析", "代码分析", "源码路径",
        "source analysis", "code analysis",
    ],
    "visualize": [
        "画图", "可视化", "图表", "架构图", "流程图",
        "diagram", "visualize", "chart",
    ],
    "visualize_architecture": [
        "架构图", "架构层次", "层次图",
        "architecture", "architecture diagram",
    ],
    "visualize_callchain": [
        "调用链", "时序图", "流程图",
        "call chain", "sequence diagram", "flow chart",
    ],
    "visualize_learningpath": [
        "学习路径", "学习路线", "学习路线图",
        "learning path", "study path",
    ],
    "visualize_knowledgegraph": [
        "知识图谱", "图谱总览", "概念图",
        "knowledge graph", "concept map",
    ],
    "visualize_dataflow": [
        "数据流", "数据流向", "数据流图",
        "data flow", "dataflow diagram",
    ],
    "visualize_classdiagram": [
        "类图", "结构体图", "结构图",
        "class diagram", "struct diagram",
    ],
    "visualize_studyprogress": [
        "进度图", "学习进度图", "甘特图",
        "progress chart", "gantt chart",
    ],
    "memory_summary": [
        "记忆摘要", "学习总结", "总结",
        "memory summary", "summary",
    ],
    "memory_recommend": [
        "今日推荐", "推荐学习", "学什么",
        "recommend", "today's recommendation",
    ],
    "memory_recurrence": [
        "误解复发", "反复错误", "重复误解",
        "recurrence", "misconception recurrence",
    ],
    "daily_log": [
        "今日日志", "今日学习", "日志",
        "daily log", "today's log",
    ],
    "profile": [
        "我的画像", "学习画像", "用户画像",
        "my profile", "learner profile",
    ],
    "session_save": [
        "保存会话", "会话保存",
        "save session",
    ],
    "session_recover": [
        "恢复会话", "会话恢复",
        "recover session", "restore",
    ],
    "persona_list": [
        "人格列表", "可选人格", "人格风格", "有哪些人格",
        "persona list", "available personas",
    ],
    "persona_current": [
        "当前人格", "当前风格",
        "current persona", "current style",
    ],
    "persona_stack": [
        "人格栈", "回溯人格", "人格历史",
        "persona stack", "persona history",
    ],
    "persona_recommend": [
        "推荐人格", "人格推荐", "适合什么人格",
        "recommend persona",
    ],
    "persona_info": [
        "人格详情", "人格说明",
        "persona info", "persona details",
    ],
    "path_view": [
        "学习路径", "我的路径", "学习路线",
        "learning path", "study path", "my path",
    ],
    "path_assess": [
        "水平评估", "学习评估", "我的水平",
        "assessment", "level assessment",
    ],
    "path_recommend": [
        "下一步", "下一步学什么", "推荐学习",
        "next step", "what next",
    ],
    "dashboard": [
        "仪表盘", "学习总览", "总览",
        "dashboard", "overview",
    ],
    "discover_flow": [
        "发现", "发现新概念", "新概念",
        "discover", "explore",
    ],
    "weak_flow": [
        "薄弱闭环", "强化验证",
        "weak loop", "strengthen",
    ],
    "review_flow": [
        "复习闭环", "巩固推进",
        "review loop", "consolidate",
    ],
    "deep_flow": [
        "深入闭环", "研究理解",
        "deep loop", "research loop",
    ],
    "stats": [
        "统计", "学习统计", "学习数据",
        "stats", "statistics",
    ],
    "export_data": [
        "导出数据", "导出学习", "导出",
        "export data", "export learning",
    ],
    "reset_progress": [
        "重置进度", "重置学习", "重置",
        "reset progress", "reset learning",
    ],
    "onboarding": [
        "引导", "新手上路", "快速开始",
        "onboarding", "getting started", "welcome",
    ],
    "milestone": [
        "里程碑", "我的成就", "成就",
        "milestone", "achievement",
    ],
    "visualize": [
        "画图", "可视化", "图表", "架构图", "流程图",
        "diagram", "visualize", "chart",
    ],
    "book_reading": [
        "看书", "打开书", "章节", "书",
        "book", "chapter", "read",
    ],
    "note_taking": [
        "记笔记", "记录", "保存", "记住",
        "note", "remember", "save",
    ],
    "status_check": [
        "进度", "掌握度", "学到哪", "状态",
        "progress", "mastery", "status",
    ],
    "persona_switch": [
        "用.*风格", "切换.*人格", "换.*风格",
        "切换.*风格", "切换.*模式", "切换.*教学",
        "切换.*者", "切换.*人", "临时.*风格",
        "临时.*人格", "临时.*教学", "临时.*者",
        "临时.*人", "临时.*",
        "switch.*persona", "change.*style",
        "change.*persona", "use.*persona",
    ],
    "misconception": [
        "轻量级虚拟机", "每行都产生层", "删除文件.*减小",
        "docker 就是.*运行时", "runc 一直运行",
    ],
    "help": [
        "帮助", "help", "命令", "怎么用", "功能",
    ],
    "knowledge_search": [
        "搜索知识库", "查知识库",
        "search knowledge",
    ],
    "knowledge_browse": [
        "知识库", "浏览目录", "所有分类",
        "knowledge base", "browse",
    ],
    "book_read": [
        "看书", "打开书", "打开书籍", "阅读第",
        "book", "read chapter",
    ],
    "book_list": [
        "书籍", "有什么书", "书架",
        "books", "library",
    ],
    "book_progress": [
        "阅读进度", "读书进度", "看到哪",
        "reading progress",
    ],
    "note_search": [
        "找笔记", "搜索笔记", "查笔记",
        "search notes", "find notes",
    ],
    "note_list": [
        "我的笔记", "笔记列表", "所有笔记",
        "my notes", "notes list",
    ],
    "note_export": [
        "导出笔记", "笔记导出",
        "export notes",
    ],
}


def detect_intent(user_input: str, context: SessionContext = None) -> str:
    """识别用户意图（支持上下文感知）"""
    user_input_lower = user_input.lower().strip()

    # 先检测帮助
    for kw in INTENT_PATTERNS["help"]:
        if kw in user_input_lower:
            return "help"

    # 检测误解（高优先级）
    for kw in INTENT_PATTERNS["misconception"]:
        if kw in user_input_lower:
            return "misconception"

    # 检测人格切换（正则）
    for pattern in INTENT_PATTERNS["persona_switch"]:
        if re.search(pattern, user_input_lower):
            return "persona_switch"

    # 检测 quiz 相关意图
    for kw in INTENT_PATTERNS["quiz_history"]:
        if kw in user_input_lower:
            return "quiz_history"
    for kw in INTENT_PATTERNS["quiz_status"]:
        if kw in user_input_lower:
            return "quiz_status"
    for kw in INTENT_PATTERNS["quiz_start"]:
        if kw in user_input_lower:
            return "quiz_start"

    # 检测 dashboard + flow 相关意图（优先级高于 practice）
    for intent in ["dashboard", "discover_flow", "weak_flow",
                    "review_flow", "deep_flow",
                    "stats", "export_data", "reset_progress",
                    "onboarding", "milestone"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测 practice 相关意图（优先级高于 general）
    for kw in INTENT_PATTERNS["practice_report"]:
        if kw in user_input_lower:
            return "practice_report"
    for kw in INTENT_PATTERNS["mastery_heatmap"]:
        if kw in user_input_lower:
            return "mastery_heatmap"
    for kw in INTENT_PATTERNS["mastery_view"]:
        if kw in user_input_lower:
            return "mastery_view"
    for kw in INTENT_PATTERNS["practice_quick"]:
        if kw in user_input_lower:
            return "practice_quick"
    for kw in INTENT_PATTERNS["practice_review"]:
        if kw in user_input_lower:
            return "practice_review"
    for kw in INTENT_PATTERNS["practice_deep"]:
        if kw in user_input_lower:
            return "practice_deep"

    # 检测 persona + path 相关意图（优先级高于 visualize）
    for intent in ["path_view", "path_assess", "path_recommend",
                    "persona_list", "persona_current", "persona_stack",
                    "persona_recommend", "persona_info"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测 dashboard + flow 相关意图
    for intent in ["dashboard", "discover_flow", "weak_flow",
                    "review_flow", "deep_flow",
                    "stats", "export_data", "reset_progress",
                    "onboarding", "milestone"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测 visualize 相关意图
    for intent in ["visualize_classdiagram", "visualize_studyprogress",
                    "visualize_dataflow", "visualize_knowledgegraph",
                    "visualize_learningpath", "visualize_callchain",
                    "visualize_architecture", "visualize",
                    "source_analysis", "research"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测 memory 相关意图
    for intent in ["memory_summary", "memory_recommend", "memory_recurrence",
                    "daily_log", "profile", "session_save", "session_recover"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测 persona + path 相关意图
    for intent in ["persona_list", "persona_current", "persona_stack",
                    "persona_recommend", "persona_info",
                    "path_view", "path_assess", "path_recommend"]:
        for kw in INTENT_PATTERNS[intent]:
            if kw in user_input_lower:
                return intent

    # 检测其他特殊意图
    special_intents = ["deep_dive", "visualize",
                       "note_taking", "note_search", "note_list", "note_export",
                       "book_read", "book_list", "book_progress",
                       "knowledge_search", "knowledge_browse"]
    for intent in special_intents:
        for pattern in INTENT_PATTERNS[intent]:
            if pattern in user_input_lower:
                return intent

    # 再检查是否提到概念名
    if kg._loaded:
        sorted_names = sorted(kg.concepts.keys(), key=len, reverse=True)
        for name in sorted_names:
            cn_name = name.split(" (")[0].split("（")[0]
            if cn_name.lower() in user_input_lower or name.lower() in user_input_lower:
                return "concept_question"

    return "general"


# ============================================================
# 概念提取
# ============================================================

def extract_concepts(user_input: str) -> list[str]:
    """从用户输入中提取提到的概念（支持模糊匹配，优先长匹配）"""
    found = []
    user_input_lower = user_input.lower()
    if kg._loaded:
        sorted_names = sorted(kg.concepts.keys(), key=len, reverse=True)
        for name in sorted_names:
            cn_name = name.split(" (")[0].split("（")[0]
            if cn_name.lower() in user_input_lower or name.lower() in user_input_lower:
                found.append(name)
    return found


# ============================================================
# Agent 处理器
# ============================================================

def handle_concept_question(concept_name: str, context: SessionContext, persona: str = "socratic") -> str:
    """处理概念讲解请求"""
    concept = kg.get_concept(concept_name)
    if not concept:
        results = kg.search_concepts(concept_name)
        if not results:
            return f"我还没学到「{concept_name}」这个概念。试试其他关键词？"
        concept = results[0]

    context.set_concept(concept.name)
    record = mastery_v2.get(concept.name)

    lines = []
    lines.append(f"## {concept.name}")
    lines.append("")
    lines.append(f"**定义**：{concept.definition}")
    lines.append("")

    if concept.code_ref:
        lines.append(f"**代码引用**：{concept.code_ref}")
        lines.append("")

    # 关联概念
    related = kg.get_related_concepts(concept.name)
    if related:
        lines.append("**关联概念**：")
        for r in related:
            r_rec = mastery.get(r.name)
            level_str = f"（掌握度: {r_rec.level:.0%}）" if r_rec.attempts > 0 else ""
            lines.append(f"- {r.name} {level_str}")
        lines.append("")

    # 前置知识
    prereqs = kg.get_prerequisites(concept.name)
    if prereqs:
        lines.append("**前置知识**：")
        for p in prereqs:
            lines.append(f"- {p.name}")
        lines.append("")

    # 掌握度状态
    if record.attempts > 0:
        lines.append(f"**你的掌握度**：{record.level:.0%}（练习 {record.attempts} 次，正确率 {record.accuracy:.0%}）")
        lines.append("")

    # 学习建议
    if record.level < 0.3:
        lines.append("💡 **建议**：先理解基础概念，再做练习巩固。")
    elif record.level < 0.6:
        lines.append("💡 **建议**：试试做几道题检验理解。")
    else:
        lines.append("💡 **建议**：可以深入源码阅读了。")

    lines.append("")
    lines.append("想继续了解哪个方面？我可以：")
    lines.append("1. 深入讲解原理")
    lines.append("2. 出题考考你")
    lines.append("3. 关联其他概念")
    lines.append("")

    daily_log.log_learning(concept.name, 5, 0.0)

    return "\n".join(lines)


# ============================================================
# 测验处理器（新引擎）
# ============================================================

def handle_quiz_start(context: SessionContext, count: int = 3, difficulty: float = 0.5) -> str:
    """开始新测验"""
    # 确定概念焦点
    concept = context.current_concept or ""
    if not concept:
        # 从薄弱点选取
        weak = mastery.get_weakest_concepts(3)
        if weak:
            concept = weak[0].concept

    # 生成测验
    session = quiz_manager.start_quiz(
        concept=concept,
        count=count,
        difficulty=difficulty,
        session_id="default",
    )

    if not session.questions:
        return "题库为空，无法生成测验。先学点概念吧！"

    # 显示第一题
    first_q = session.current_question
    lines = [
        f"## 📝 测验开始！",
        f"概念焦点：{session.concept_focus or '综合'}",
        f"难度：{session.difficulty:.1f}",
        f"共 {len(session.questions)} 题",
        "",
        f"---",
        f"### 第 1 题（{session.progress}）",
        "",
        f"**{first_q.body}**",
        "",
    ]
    if first_q.options:
        for opt in first_q.options:
            lines.append(opt)
    lines.append("")
    lines.append("*回复你的答案继续*")

    return "\n".join(lines)


def handle_quiz_answer(user_input: str, context: SessionContext) -> str:
    """处理测验作答"""
    session_id = "default"
    result = quiz_manager.answer_question(session_id, user_input)

    if "error" in result:
        return result["error"]

    return result["feedback"]


def handle_quiz_status(context: SessionContext) -> str:
    """查看当前测验状态"""
    return quiz_manager.get_quiz_status("default")


def handle_quiz_history(context: SessionContext) -> str:
    """查看测验历史"""
    return quiz_manager.get_quiz_history_text("default")


# ============================================================
# 旧版测验（兼容，保留作为快速出题）
# ============================================================

def handle_quiz_legacy(context: SessionContext, count: int = 3, difficulty: float = 0.5) -> str:
    """旧版快速出题（生成简单判断题）"""
    concepts = []
    if context.current_concept:
        concepts.append(context.current_concept)
    else:
        weak = mastery.get_weakest_concepts(3)
        concepts = [r.concept for r in weak]

    if not concepts:
        all_names = list(kg.concepts.keys())
        core = [n for n in all_names if any(k in n for k in ["容器", "镜像", "层"])]
        concepts = core[:3] if core else all_names[:3]

    lines = [f"## 📝 快速测验（{len(concepts)} 道题）\n"]

    for i, concept_name in enumerate(concepts, 1):
        c = kg.get_concept(concept_name)
        if not c:
            continue

        lines.append(f"### 第 {i} 题：{concept_name}")
        lines.append("")

        if c.misconceptions:
            mc = c.misconceptions[0]
            lines.append(f"判断题：{mc['pattern']}（对/错）")
            lines.append("")
            lines.append(f"*（思考好后回复「对」或「错」）*")
        else:
            lines.append(f"简答题：请用一句话概括「{concept_name}」的核心作用。")
            lines.append("")
            lines.append(f"*（回复你的答案）*")

        lines.append("")
        context.pending_questions.append({
            "concept": concept_name,
            "type": "misconception" if c.misconceptions else "definition",
            "answer": "错" if c.misconceptions else c.definition,
        })

    return "\n".join(lines)


def handle_misconception_detection_and_correction(user_input: str, context: SessionContext) -> str:
    """检测并纠正误解"""
    for concept_name, concept in kg.concepts.items():
        mc = kg.detect_misconception(concept_name, user_input)
        if mc:
            context.set_concept(concept_name)
            mastery_v2.record_misconception(concept_name, mc["pattern"])

            return (
                f"🤔 我发现了一个关于「{concept_name}」的常见误解。\n\n"
                f"**你的想法**：{mc['pattern']}\n\n"
                f"**纠正**：{mc['correction']}\n\n"
                f"这其实是一个很常见的误解，很多人都会混淆。"
                f"我们可以深入聊聊 {concept_name} 的实际原理，帮你彻底理清这个概念。"
            )

    return None


# ============================================================
# 练习会话管理
# ============================================================

# 全局练习会话
practice_session = PracticeSession(mastery_v2)


def handle_practice_quick(context: SessionContext) -> str:
    """快速练习模式"""
    concepts = practice_session.start_quick(count=5)
    if not concepts:
        return "没有需要练习的概念。试试学点新东西！"

    lines = [
        f"## 🏃 快速练习 ({len(concepts)} 个概念)",
        "",
        "根据你的掌握度，建议练习以下概念：",
        "",
    ]
    for i, c in enumerate(concepts, 1):
        record = mastery_v2.get(c)
        retention = get_retention_rate(record)
        reason = "到期复习" if (record.next_review and record.next_review <= datetime.now().strftime("%Y-%m-%d")) else "需要巩固"
        lines.append(f"**{i}. {c}** — {reason}（掌握度: {record.level:.0%}，记忆率: {retention:.0%}）")

    lines.append("")
    lines.append("---")
    first = practice_session.current_concept
    if first:
        lines.append(f"### 开始：{first}")
        lines.append("")
        lines.append("复习一下这个概念，然后告诉我你记住了吗？")
        lines.append("回复「对」或「错」表示你是否掌握。")

    return "\n".join(lines)


def handle_practice_deep(context: SessionContext) -> str:
    """深度练习模式"""
    concept = context.current_concept
    if not concept:
        # 从薄弱点选
        weak = mastery_v2.get_weakest_concepts(1)
        if weak:
            concept = weak[0].concept
        else:
            return "请先指定一个概念，例如「深度练习 容器运行时」。"

    concepts = practice_session.start_deep(concept)
    lines = [
        f"## 🔬 深度练习：{concept}",
        "",
        "深入理解这个概念及其关联知识：",
        "",
    ]
    for i, c in enumerate(concepts, 1):
        record = mastery_v2.get(c)
        lines.append(f"**{i}. {c}**（掌握度: {record.level:.0%}）")

    lines.append("")
    lines.append("---")
    first = practice_session.current_concept
    if first:
        lines.append(f"### 开始：{first}")
        lines.append("")
        c = kg.get_concept(first)
        if c:
            lines.append(f"**定义**：{c.definition}")
            lines.append("")
        lines.append("理解了吗？回复「对」或「错」。")

    return "\n".join(lines)


def handle_practice_review(context: SessionContext) -> str:
    """复习模式"""
    concepts = practice_session.start_review()
    if not concepts:
        return "🎉 没有需要复习的概念！继续保持！"

    lines = [
        f"## 🔄 复习 ({len(concepts)} 个概念)",
        "",
        "这些概念需要巩固：",
        "",
    ]
    for i, c in enumerate(concepts, 1):
        record = mastery_v2.get(c)
        retention = get_retention_rate(record)
        lines.append(f"**{i}. {c}** — 记忆率: {retention:.0%}，上次练习: {record.last_practiced or '从未'}")

    lines.append("")
    lines.append("---")
    first = practice_session.current_concept
    if first:
        lines.append(f"### 开始：{first}")
        lines.append("")
        c = kg.get_concept(first)
        if c:
            lines.append(f"**定义**：{c.definition}")
            lines.append("")
        lines.append("理解了吗？回复「对」或「错」。")

    return "\n".join(lines)


def handle_practice_answer(user_input: str, context: SessionContext) -> str:
    """处理练习作答"""
    if not practice_session.is_active:
        return "当前没有活跃的练习。试试「快速练习」开始。"

    # 判断对/错
    user_clean = user_input.strip().lower()
    correct = user_clean in ("对", "正确", "true", "t", "yes", "y", "记住了", "理解", "是")

    concept = practice_session.current_concept
    c = kg.get_concept(concept)
    difficulty = c.difficulty if c else 0.5

    practice_session.record_result(correct, difficulty)

    record = mastery_v2.get(concept)
    status = "✅" if correct else "❌"

    lines = [
        f"{status} **{concept}** — 掌握度: {record.level:.0%}",
        f"间隔: {record.interval} 天 | EF: {record.easiness:.2f} | 下次复习: {record.next_review or '未安排'}",
    ]

    # 显示下个概念或完成报告
    if practice_session.is_active:
        next_concept = practice_session.current_concept
        lines.append("")
        lines.append("---")
        lines.append(f"### 下一个：{next_concept}")
        c_next = kg.get_concept(next_concept)
        if c_next:
            lines.append(f"**{c_next.definition}**")
        lines.append("")
        lines.append("理解了吗？回复「对」或「错」。")
    else:
        lines.append("")
        lines.append("---")
        lines.append(practice_session.get_report())

    return "\n".join(lines)


def handle_mastery_view(context: SessionContext) -> str:
    """掌握度总览"""
    return practice_report.generate_overview(mastery_v2)


def handle_mastery_heatmap(context: SessionContext) -> str:
    """掌握度热力图"""
    all_concepts = kg.get_all_concepts()
    names = [c.name for c in all_concepts]
    return practice_report.generate_mermaid_heatmap(names, mastery_v2)


def handle_practice_report(context: SessionContext) -> str:
    """练习报告"""
    concepts = [c.name for c in kg.get_all_concepts()]
    return practice_report.generate_text(concepts, mastery_v2)


# ============================================================
# 记忆处理器
# ============================================================

def handle_memory_summary(context: SessionContext) -> str:
    """学习记忆摘要"""
    summary = long_term_memory.summarize()
    lines = ["## 📋 学习记忆摘要\n"]
    lines.append(f"**学习天数**: {summary['total_days']} 天")
    lines.append(f"**学习会话**: {summary['total_sessions']} 次")
    lines.append(f"**已学概念**: {summary['concepts_learned']} 个")
    lines.append(f"**误解纠正**: {summary['misconceptions_corrected']} 次")
    lines.append(f"**记录洞见**: {summary['insights_recorded']} 条")

    if summary["recent_days"]:
        lines.append(f"\n**最近活动**: {', '.join(summary['recent_days'])}")

    # 掌握度概览
    all_concepts = kg.get_all_concepts()
    records = [mastery_v2.get(c.name) for c in all_concepts]
    practiced = [r for r in records if r.attempts > 0]
    if practiced:
        avg = sum(r.level for r in practiced) / len(practiced)
        lines.append(f"\n**平均掌握度**: {avg:.0%}")

    return "\n".join(lines)


def handle_memory_recommend(context: SessionContext) -> str:
    """今日推荐"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## 🎯 今日推荐 — {today}\n"]
    lines.extend(daily_summary.recommend())
    lines.append("\n💡 试试「快速练习」开始练习。")
    return "\n".join(lines)


def handle_memory_recurrence(context: SessionContext) -> str:
    """误解复发检测"""
    recurrences = long_term_memory.get_misconception_recurrence()
    if not recurrences:
        return "✅ 没有发现重复出现的误解，你的理解很扎实！"

    lines = ["## ⚠️ 误解复发检测\n"]
    for r in recurrences:
        lines.append(f"- **{r['pattern']}**（概念: {r['concept']}）")
        lines.append(f"  出现 {r['count']} 次: {', '.join(r['dates'])}")
        lines.append("")
    lines.append("建议重新学习相关概念，巩固理解。")
    return "\n".join(lines)


def handle_daily_log(context: SessionContext) -> str:
    """今日学习日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(__file__).parent.parent / "memory" / f"{today}.md"
    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        return f"## 📝 今日日志 ({today})\n\n{content}"
    return f"今日 ({today}) 暂无学习记录。"


def handle_profile(context: SessionContext) -> str:
    """用户画像"""
    user_profile.update_strengths_weaknesses()
    p = user_profile.profile
    lines = ["## 👤 学习画像\n"]
    lines.append(f"**学习类型**: {p.get('learner_type', 'explorer')}")
    lines.append(f"**偏好人格**: {p.get('preferred_persona', 'socratic')}")
    lines.append(f"**会话次数**: {p.get('session_count', 0)}")
    lines.append(f"\n**强项**: {', '.join(p.get('strengths', [])) or '暂无'}")
    lines.append(f"**弱项**: {', '.join(p.get('weaknesses', [])) or '暂无'}")
    if p.get("interests"):
        lines.append(f"**兴趣**: {', '.join(p['interests'])}")
    lines.append(f"\n**首次学习**: {p.get('first_seen', '')[:10]}")
    lines.append(f"**上次学习**: {p.get('last_seen', '')[:10]}")
    return "\n".join(lines)


def handle_session_save(context: SessionContext) -> str:
    """保存会话"""
    session_manager.save_session(context.__dict__)
    return "✅ 会话已保存。下次进入时自动恢复。"


def handle_session_recover(context: SessionContext) -> str:
    """恢复会话"""
    prompt = session_manager.get_recovery_prompt()
    if prompt:
        return prompt
    return "没有找到已保存的会话。"


# ============================================================
# 其他处理器
# ============================================================

def handle_status(context: SessionContext) -> str:
    """查看学习进度（使用新掌握度引擎）"""
    return practice_report.generate_overview(mastery_v2)


def handle_help() -> str:
    return """## 🐳 Docker 源码学习系统

### 学习命令
- **什么是 <概念>** - 讲解概念
- **深入 <概念>** - 深入源码原理
- **出题 / 考考我** - 开始测验（交互式）
- **当前题目** - 查看当前测验题目
- **测验历史** - 查看答题记录

### 练习与掌握度
- **快速练习** - 根据薄弱点生成练习计划
- **复习** - 到期概念复习
- **深度练习 <概念>** - 深入概念及其关联
- **掌握度** - 查看掌握度总览
- **热力图** - 查看掌握度可视化图表
- **练习报告** - 详细练习报告

### 深度研究
- **研究 <概念>** - 生成深度研究报告
- **源码分析 <概念>** - 源码路径分析

### 可视化
- **画图** - 查看所有图表类型
- **架构图 <概念>** - 生成架构层次图
- **调用链 <概念>** - 生成时序/流程图
- **学习路径** - 学习路线推荐
- **知识图谱** - 概念总览图
- **数据流 <概念>** - 数据流图
- **类图 <概念>** - 结构体关系图
- **进度图** - 学习进度甘特图

### 记忆与画像
- **总结** - 学习记忆摘要
- **今日推荐** - 今日学习推荐
- **误解复发** - 检测重复出现的误解
- **今日日志** - 查看今日学习日志
- **我的画像** - 学习画像
- **保存会话** - 保存当前会话状态
- **恢复会话** - 恢复上次会话

### 人格与路径
- **人格列表** - 查看所有可用人格
- **当前人格** - 查看当前人格详情
- **人格栈** - 查看人格切换历史
- **推荐人格** - 根据进度推荐人格
- **人格详情 <人格名>** - 查看人格详细说明
- **学习路径** - 查看自适应学习路径
- **水平评估** - 学习水平评估
- **下一步** - 推荐下一步学习内容

### 仪表盘与学习流
- **总览** - 学习总览
- **仪表盘** - 完整仪表盘（掌握度分布、到期复习、推荐）
- **统计** - 详细学习统计
- **发现** - 发现新概念 → 学习 → 练习
- **薄弱闭环** - 薄弱点 → 强化 → 验证
- **复习闭环** - 复习 → 巩固 → 推进
- **深入闭环 <概念>** - 疑问 → 研究 → 理解
- **里程碑** - 查看成就

### 系统管理
- **导出数据** - 导出学习数据（掌握度、路径、笔记、记忆）
- **重置进度** - 重置所有掌握度记录（需确认）
- **引导** - 新手引导

### 知识库
- **知识库** - 浏览知识库目录
- **搜索知识库 <关键词>** - 搜索知识文档

### 书籍
- **书籍** - 查看书架
- **看书 <章号>** - 开始阅读（如 `看书 01`）
- **阅读进度** - 查看阅读进度

### 笔记
- **记笔记 <内容>** - 记录学习笔记
- **我的笔记** - 查看所有笔记
- **找笔记 <关键词>** - 搜索笔记
- **导出笔记** - 导出为 Markdown 文件

### 人格切换
- **用苏格拉底风格** - 启发式提问
- **用教授风格** - 结构化讲解
- **用实战风格** - 代码驱动
- **用故事风格** - 比喻讲解
- **用教练风格** - 目标导向
- **用极简风格** - 精简回答
- **用魔鬼风格** - 辩论模式

### 其他
- **帮助** - 显示此帮助
"""


def handle_persona_switch(user_input: str, context: SessionContext) -> str:
    """切换人格（使用新版引擎，支持临时/永久切换）"""
    input_lower = user_input.lower()

    # 检测临时切换
    is_temporary = "临时" in input_lower or "暂时" in input_lower or "一次" in input_lower

    # 中英文简称映射（按长度降序，避免短字误匹配）
    short_names = {
        "苏格拉底": "socratic", "苏格": "socratic",
        "教授": "professor",
        "实践者": "practitioner", "实践": "practitioner", "实战": "practitioner",
        "说书人": "storyteller", "故事": "storyteller", "说书": "storyteller",
        "教练": "coach",
        "极简者": "minimalist", "极简": "minimalist",
        "唱反调": "devils_advocate", "魔鬼": "devils_advocate",
        "调试者": "debugger", "调试": "debugger",
    }

    for name, pid in short_names.items():
        if name in user_input:
            msg = persona_engine.switch(pid, context.active_persona,
                                        push_to_stack=is_temporary)
            context.active_persona = pid
            if is_temporary:
                msg += "\n（临时切换，下次对话自动恢复上一人格）"
            return msg

    available = "、".join([p["display_name"] for p in persona_engine.personas.values()])
    return f"支持的人格：{available}"

    available = "、".join([p["display_name"] for p in persona_engine.personas.values()])
    return f"支持的人格：{available}"


def handle_persona_list(context: SessionContext) -> str:
    """列出所有人格"""
    personas = persona_engine.list_personas()
    lines = ["## 🎭 可选人格风格\n"]
    for p in personas:
        active = " ⬅️ 当前" if p["id"] == context.active_persona else ""
        lines.append(f"**{p['name']}**{active}")
        lines.append(f"*{p['style']}*")
        lines.append(f"  {p['description']}")
        lines.append(f"  标签: {', '.join(p['tags'])}")
        lines.append("")
    lines.append("切换: 「切换苏格拉底风格」或「临时切换 教授风格」")
    return "\n".join(lines)


def handle_persona_current(context: SessionContext) -> str:
    """查看当前人格"""
    p = persona_engine.get_persona(context.active_persona)
    if not p:
        return f"当前人格: {context.active_persona}"
    return persona_engine.get_persona_description(context.active_persona)


def handle_persona_stack(context: SessionContext) -> str:
    """查看人格栈"""
    stack = persona_engine.get_stack_info()
    current = context.active_persona
    cp = persona_engine.get_persona(current)
    current_name = cp["display_name"] if cp else current

    lines = ["## 🎭 人格栈\n"]
    lines.append(f"**当前**: {current_name}")
    if stack:
        lines.append("**历史**:")
        lines.extend(stack)
    else:
        lines.append("**历史**: 无（尚未进行过临时切换）")
    lines.append("")
    lines.append("回溯: 输入「切换 上一人格」或「恢复人格」")
    return "\n".join(lines)


def handle_persona_recommend(context: SessionContext) -> str:
    """推荐人格"""
    recommended = persona_engine.recommend_persona(context.__dict__)
    p = persona_engine.get_persona(recommended)
    name = p["display_name"] if p else recommended

    lines = ["## 🎯 人格推荐\n"]
    lines.append(f"基于你的学习进度，建议切换到 **{name}** 风格。")
    if p:
        lines.append(f"*{p['style']}*")
        lines.append(f"  {p['description']}")
    lines.append("\n试试「切换 苏格拉底风格」")
    return "\n".join(lines)


def handle_persona_info(user_input: str, context: SessionContext) -> str:
    """查看人格详情"""
    for pid, p in persona_engine.personas.items():
        if p["display_name"] in user_input or pid in user_input.lower():
            return persona_engine.get_persona_description(pid)
    return "想了解哪个人格？试试「人格详情 苏格拉底」"


def handle_path_view(context: SessionContext) -> str:
    """查看学习路径"""
    path = learning_path.adapt_path(context.__dict__)

    lines = ["## 🗺️ 你的学习路径\n"]
    current_group = ""

    for item in path:
        group = item.get("group", "其他")
        if group != current_group:
            current_group = group
            lines.append(f"\n### {group}\n")

        if item["status"] == "已学":
            icon = "✅"
        elif item["status"] == "学习中":
            icon = "🔄"
        elif item["status"] == "待复习":
            icon = "📌"
        else:
            icon = "⬜"

        level_bar = "█" * int(item["level"] * 10) + "░" * (10 - int(item["level"] * 10))
        lines.append(f"{icon} **{item['concept']}**")
        lines.append(f"   掌握度: {level_bar} {item['level']:.0%}")

        if item["next_review"]:
            lines.append(f"   下次复习: {item['next_review']}")

    lines.append("\n💡 试试「下一步学什么」获取推荐。")
    return "\n".join(lines)


def handle_path_assess(context: SessionContext) -> str:
    """水平评估"""
    assessment = learning_path.assess()

    lines = ["## 📊 学习水平评估\n"]
    lines.append(f"**当前阶段**: {assessment['stage']}")
    lines.append(f"**总概念**: {assessment['total_concepts']} 个")
    lines.append(f"**已学**: {assessment['learned_concepts']} 个")
    lines.append(f"**精通**: {assessment['mastered_concepts']} 个")
    lines.append(f"**平均掌握度**: {assessment['average_level']:.0%}")
    lines.append("")

    if assessment["weak_spots"]:
        lines.append("**薄弱点**:")
        for w in assessment["weak_spots"]:
            lines.append(f"- {w}")
    if assessment["strong_spots"]:
        lines.append("**强项**:")
        for s in assessment["strong_spots"]:
            lines.append(f"- {s}")

    lines.append("\n💡 试试「快速练习」强化薄弱点。")
    return "\n".join(lines)


def handle_path_recommend(context: SessionContext) -> str:
    """推荐下一步"""
    recommendation = learning_path.recommend_next(context.__dict__)

    lines = ["## 🎯 下一步推荐\n"]
    lines.append(f"**类型**: {recommendation['type']}")
    lines.append(f"**概念**: {recommendation['concept']}")
    lines.append(f"**原因**: {recommendation['reason']}")
    lines.append(f"**建议操作**: {recommendation['action']}")

    if recommendation["type"] == "复习":
        lines.append(f"\n试试「复习 {recommendation['concept']}」")
    elif recommendation["type"] == "强化":
        lines.append(f"\n试试「深度练习 {recommendation['concept']}」")
    else:
        lines.append(f"\n试试「什么是 {recommendation['concept']}」")

    return "\n".join(lines)


# ============================================================
# 仪表盘 + 学习流 + 系统命令
# ============================================================

def handle_dashboard(context: SessionContext) -> str:
    """学习仪表盘"""
    return dashboard.overview()


def handle_full_dashboard(context: SessionContext) -> str:
    """完整仪表盘"""
    return dashboard.dashboard()


def handle_discover_flow(context: SessionContext) -> str:
    """发现→学习→练习 闭环"""
    return flow_engine.discover_flow()


def handle_weak_flow(context: SessionContext) -> str:
    """薄弱→强化→验证 闭环"""
    return flow_engine.weak_flow()


def handle_review_flow(context: SessionContext) -> str:
    """复习→巩固→推进 闭环"""
    return flow_engine.review_flow()


def handle_deep_flow(user_input: str, context: SessionContext) -> str:
    """疑问→研究→理解 闭环"""
    # 提取概念名
    concept = ""
    parts = user_input.split()
    for i, p in enumerate(parts):
        if "深入" in p or "研究" in p:
            if i + 1 < len(parts):
                concept = parts[i + 1]
            break
    if not concept and context.current_concept:
        concept = context.current_concept.split(" (")[0]
    return flow_engine.deep_flow(concept)


def handle_stats(context: SessionContext) -> str:
    """学习统计"""
    return system_commands.stats()


def handle_export(context: SessionContext) -> str:
    """导出数据"""
    return system_commands.export()


def handle_reset(user_input: str, context: SessionContext) -> str:
    """重置进度"""
    if "确认" in user_input.lower() or "confirm" in user_input.lower():
        return system_commands.reset(dry_run=False)
    return system_commands.reset(dry_run=True)


def handle_onboarding(context: SessionContext) -> str:
    """新用户引导"""
    return ux.onboarding()


def handle_milestone(context: SessionContext) -> str:
    """里程碑"""
    result = ux.celebrate_milestone()
    if result:
        return result
    return "暂无里程碑。继续学习，达成更多成就！"


# ============================================================
# 编排器主函数
# ============================================================

def process_input(user_input: str, context: SessionContext) -> dict:
    """
    处理用户输入，返回响应

    返回: {
        "response": str,
        "intent": str,
        "concepts": [str],
        "mastery_delta": {str: float},
    }
    """
    # 1. 检测是否有活跃的练习（用户可能在作答）
    if practice_session.is_active:
        # 简短回答（对/错/是/否）视为练习作答
        is_practice_answer = user_input.strip().lower() in (
            "对", "错", "正确", "错误", "true", "false", "t", "f",
            "yes", "no", "y", "n", "是", "否", "记住了", "不理解",
        )
        if is_practice_answer:
            response = handle_practice_answer(user_input, context)
            return {
                "response": response,
                "intent": "practice_answer",
                "concepts": [],
                "mastery_delta": {},
            }

    # 2. 检测是否有活跃的测验（用户可能在作答）
    active_session = quiz_manager.active_sessions.get("default")
    if active_session and active_session.is_active:
        # 检查用户输入是否看起来像在答题（而不是新命令）
        # 简短回答（对/错/A/B/C、数字、简短文字）视为答题
        # 但如果输入包含命令关键词，则视为新请求
        is_answer = not any(
            kw in user_input.lower()
            for intent_group in ["help", "quiz_start", "quiz_status", "quiz_history",
                                "status_check", "persona_switch", "note_taking",
                                "note_search", "note_list", "note_export",
                                "book_read", "book_list", "book_progress",
                                "knowledge_search", "knowledge_browse",
                                "deep_dive", "visualize", "practice",
                                "practice_quick", "practice_review",
                                "practice_deep", "practice_report",
                                "mastery_view", "mastery_heatmap",
                                "research", "source_analysis",
                                "visualize_architecture", "visualize_callchain",
                                "visualize_learningpath", "visualize_knowledgegraph",
                                "visualize_dataflow", "visualize_classdiagram",
                                "visualize_studyprogress",
                                "memory_summary", "memory_recommend",
                                "memory_recurrence", "daily_log", "profile",
                                "session_save", "session_recover",
                                "persona_list", "persona_current", "persona_stack",
                                "persona_recommend", "persona_info",
                                "path_view", "path_assess", "path_recommend",
                                "dashboard", "discover_flow", "weak_flow",
                                "review_flow", "deep_flow",
                                "stats", "export_data", "reset_progress",
                                "onboarding", "milestone"]
            for kw in INTENT_PATTERNS.get(intent_group, [])
        )
        # 也要检查是否包含概念名（新请求）
        if is_answer and kg._loaded:
            sorted_names = sorted(kg.concepts.keys(), key=len, reverse=True)
            for name in sorted_names:
                cn_name = name.split("（")[0].strip()
                if cn_name.lower() in user_input.lower() and len(user_input) > 15:
                    is_answer = False
                    break

        if is_answer:
            # 处理答题
            response = handle_quiz_answer(user_input, context)
            return {
                "response": response,
                "intent": "quiz_answer",
                "concepts": [],
                "mastery_delta": {},
            }

    # 3. 意图识别
    intent = detect_intent(user_input, context)
    concepts = extract_concepts(user_input)
    mastery_delta = {}

    # 4. 处理
    response = ""

    if intent == "help":
        response = handle_help()

    elif intent == "misconception":
        result = handle_misconception_detection_and_correction(user_input, context)
        if result:
            response = result
        else:
            response = handle_concept_question(concepts[0], context) if concepts else handle_help()

    elif intent == "deep_dive":
        if concepts:
            concept = kg.get_concept(concepts[0])
            if concept:
                context.set_concept(concept.name)
                lines = [
                    f"## 🔬 深入 {concept.name}",
                    "",
                    f"**核心定义**：{concept.definition}",
                    "",
                ]
                if concept.code_ref:
                    lines.append(f"**源码位置**：`{concept.code_ref}`")
                    lines.append("")
                    lines.append("让我们从源码层面深入分析。")
                    lines.append("")
                    lines.append("### 架构视角")
                    lines.append(f"{concept.name} 在 Docker 整体架构中的位置：")
                    lines.append("")
                    related = kg.get_related_concepts(concept.name)
                    prereqs = kg.get_prerequisites(concept.name)
                    if prereqs:
                        lines.append("上游依赖：")
                        for p in prereqs:
                            lines.append(f"- {p.name}")
                    if related:
                        lines.append("下游组件：")
                        for r in related:
                            lines.append(f"- {r.name}")
                    lines.append("")
                    lines.append("### 关键源码路径")
                    lines.append(f"```")
                    lines.append(f"# 核心入口")
                    lines.append(f"{concept.code_ref}")
                    lines.append(f"```")
                    lines.append("")
                    lines.append("想深入哪个具体方面？我可以：")
                    lines.append("1. 分析关键函数")
                    lines.append("2. 讲解设计模式")
                    lines.append("3. 对比其他实现")
                else:
                    lines.append("目前没有关联的源码路径。")
                    lines.append("")
                    lines.append("想从哪个角度深入理解？")
                response = "\n".join(lines)
            else:
                response = f"没找到「{concepts[0]}」的概念定义。"
        else:
            response = "你想深入哪个概念？试试「深入容器运行时」。"
            if concepts:
                daily_log.log_learning(concepts[0], 5, 0.0)

    elif intent == "concept_question":
        if concepts:
            response = handle_concept_question(concepts[0], context)
        else:
            response = "你想了解哪个概念？试试「什么是容器」或「讲讲镜像构建」。"

    elif intent == "quiz_start":
        response = handle_quiz_start(context)

    elif intent == "quiz_status":
        response = handle_quiz_status(context)

    elif intent == "quiz_history":
        response = handle_quiz_history(context)

    elif intent == "practice":
        # 快速练习作为默认
        response = handle_practice_quick(context)

    elif intent == "practice_quick":
        response = handle_practice_quick(context)

    elif intent == "practice_review":
        response = handle_practice_review(context)

    elif intent == "practice_deep":
        # 如果指定了概念，用它
        if concepts:
            practice_session.start_deep(concepts[0])
        response = handle_practice_deep(context)

    elif intent == "practice_report":
        response = handle_practice_report(context)

    elif intent == "mastery_view":
        response = handle_mastery_view(context)

    elif intent == "mastery_heatmap":
        response = handle_mastery_heatmap(context)

    elif intent == "research":
        if concepts:
            response = research.generate_report(concepts[0])
        elif context.current_concept:
            response = research.generate_report(context.current_concept)
        else:
            response = "你想研究哪个概念？试试「研究 容器运行时」。"

    elif intent == "source_analysis":
        if concepts:
            response = research.generate_source_analysis(concepts[0])
        elif context.current_concept:
            response = research.generate_source_analysis(context.current_concept)
        else:
            response = "你想分析哪个概念的源码？试试「源码分析 容器」。"

    elif intent == "visualize":
        # 列出所有图表类型
        types = viz.list_diagram_types()
        lines = ["## 📊 可视化图表类型\n"]
        for t in types:
            lines.append(f"- **{t['name']}**: {t['desc']}")
        lines.append("")
        lines.append("试试：")
        lines.append("- 「架构图 容器」 — 生成架构图")
        lines.append("- 「调用链 容器创建」 — 生成时序图")
        lines.append("- 「学习路径」 — 学习路线图")
        lines.append("- 「知识图谱」 — 图谱总览")
        lines.append("- 「数据流 镜像」 — 数据流图")
        lines.append("- 「类图 容器」 — 结构体图")
        lines.append("- 「进度图」 — 学习进度甘特图")
        response = "\n".join(lines)

    elif intent == "visualize_architecture":
        concept = concepts[0] if concepts else ""
        response = viz.generate_architecture(concept)

    elif intent == "visualize_callchain":
        concept = concepts[0] if concepts else "容器创建流程"
        response = viz.generate_call_chain(concept)

    elif intent == "visualize_learningpath":
        concept = concepts[0] if concepts else ""
        response = viz.generate_learning_path(concept)

    elif intent == "visualize_knowledgegraph":
        response = viz.generate_knowledge_graph()

    elif intent == "visualize_dataflow":
        concept = concepts[0] if concepts else ""
        response = viz.generate_data_flow(concept)

    elif intent == "visualize_classdiagram":
        concept = concepts[0] if concepts else ""
        response = viz.generate_class_diagram(concept)

    elif intent == "visualize_studyprogress":
        response = viz.generate_study_progress()

    elif intent == "memory_summary":
        response = handle_memory_summary(context)

    elif intent == "memory_recommend":
        response = handle_memory_recommend(context)

    elif intent == "memory_recurrence":
        response = handle_memory_recurrence(context)

    elif intent == "daily_log":
        response = handle_daily_log(context)

    elif intent == "profile":
        response = handle_profile(context)

    elif intent == "session_save":
        response = handle_session_save(context)

    elif intent == "session_recover":
        response = handle_session_recover(context)

    elif intent == "persona_list":
        response = handle_persona_list(context)

    elif intent == "persona_current":
        response = handle_persona_current(context)

    elif intent == "persona_stack":
        response = handle_persona_stack(context)

    elif intent == "persona_recommend":
        response = handle_persona_recommend(context)

    elif intent == "persona_info":
        response = handle_persona_info(user_input, context)

    elif intent == "path_view":
        response = handle_path_view(context)

    elif intent == "path_assess":
        response = handle_path_assess(context)

    elif intent == "path_recommend":
        response = handle_path_recommend(context)

    elif intent == "dashboard":
        # "仪表盘" → 完整仪表盘, "总览" → 简要总览
        if "仪表盘" in user_input:
            response = handle_full_dashboard(context)
        else:
            response = handle_dashboard(context)

    elif intent == "discover_flow":
        response = handle_discover_flow(context)

    elif intent == "weak_flow":
        response = handle_weak_flow(context)

    elif intent == "review_flow":
        response = handle_review_flow(context)

    elif intent == "deep_flow":
        response = handle_deep_flow(user_input, context)

    elif intent == "stats":
        response = handle_stats(context)

    elif intent == "export_data":
        response = handle_export(context)

    elif intent == "reset_progress":
        response = handle_reset(user_input, context)

    elif intent == "onboarding":
        response = handle_onboarding(context)

    elif intent == "milestone":
        response = handle_milestone(context)

    elif intent == "status_check":
        response = handle_status(context)

    elif intent == "persona_switch":
        response = handle_persona_switch(user_input, context)

    elif intent == "knowledge_browse":
        response = kb.get_overview()

    elif intent == "knowledge_search":
        query = user_input.replace("搜索知识库", "").replace("查知识库", "").replace("search knowledge", "").strip()
        if query:
            results = kb.search(query)
            if results:
                lines = [f"## 🔍 知识库搜索结果：{query}\n"]
                for r in results[:10]:
                    lines.append(f"- **{r['title']}** ({r['category']})")
                    lines.append(f"  {r['snippet']}")
                response = "\n".join(lines)
            else:
                response = f"没有找到包含「{query}」的知识文档。"
        else:
            response = "你想搜索什么？试试「搜索知识库 overlay2」。"

    elif intent == "book_list":
        books = bm.list_books()
        if not books:
            response = "目前没有可用的书籍。"
        else:
            lines = ["## 📚 书架\n"]
            for b in books:
                ch_count = len(b.get("chapters", []))
                lines.append(f"### {b['title']}")
                lines.append(f"*{b.get('author', '未知')}*  |  {b.get('description', '')}")
                lines.append(f"共 {ch_count} 章  |  难度：{b.get('difficulty', '未知')}")
                lines.append("")
            response = "\n".join(lines)

    elif intent == "book_read":
        parts = user_input.split()
        book_id = "docker-shenjiu"
        chapter_id = "01"

        if len(parts) >= 2:
            for p in parts[1:]:
                if re.match(r'^\d{1,2}$', p):
                    chapter_id = p.zfill(2)
                    break

        meta = bm.get_book(book_id)
        if not meta:
            response = f"没找到书籍 {book_id}。"
        else:
            if chapter_id == "00" or chapter_id == "overview":
                response = bm.get_book_overview(book_id)
            else:
                content = bm.read_chapter(book_id, chapter_id)
                if content:
                    context.set_concept(f"书籍: {meta['title']} 第{chapter_id}章")
                    bm.save_progress(book_id, chapter_id)
                    response = content
                    next_ch = int(chapter_id) + 1
                    response += f"\n\n---\n*阅读进度已保存。输入「看书 {next_ch:02d}」继续下一章*"
                else:
                    response = f"没找到第 {chapter_id} 章。试试「书籍」查看所有章节。"

    elif intent == "book_progress":
        book_id = "docker-shenjiu"
        progress = bm.get_book_progress(book_id)
        meta = bm.get_book(book_id)
        if meta:
            total = len(meta.get("chapters", []))
            completed = len(progress.get("completed_chapters", []))
            lines = [
                f"## 📖 阅读进度：{meta['title']}",
                f"",
                f"已完成：{completed}/{total} 章",
                f"当前章节：{progress.get('current_chapter', '无')}",
            ]
            if progress.get("last_read"):
                lines.append(f"上次阅读：{progress['last_read'][:16]}")
            lines.append("")
            lines.append("### 章节状态")
            for ch in meta.get("chapters", []):
                status = "✅" if ch["id"] in progress.get("completed_chapters", []) else "⬜"
                lines.append(f"{status} **{ch['id']}**. {ch['title']}")
            response = "\n".join(lines)
        else:
            response = "没有阅读记录。"

    elif intent == "note_taking":
        note = user_input
        for prefix in ["记笔记", "记住", "记录", "保存", "note", "remember", "save"]:
            note = note.replace(prefix, "").strip()
        if note:
            new_note = nm.add_note(
                content=note,
                concept=context.current_concept,
                book="docker-shenjiu" if context.current_concept and "书籍" in context.current_concept else "",
            )
            daily_log.append(f"\n### 笔记\n{note}\n（关联概念：{context.current_concept or '无'}）\n")
            response = f"✅ 已记录笔记。\n\n> {note}\n\n关联概念：{context.current_concept or '无'}"
        else:
            response = "要记什么？例如「记笔记 Docker 的分层架构很巧妙」。"

    elif intent == "note_search":
        query = user_input
        for prefix in ["找笔记", "搜索笔记", "查笔记", "search notes", "find notes"]:
            query = query.replace(prefix, "").strip()
        if query:
            notes = nm.search_notes(query)
            if notes:
                lines = [f"## 🔍 笔记搜索：{query}\n"]
                for n in notes[:10]:
                    lines.append(f"- **{n['created_at'][:16]}** | {n['content'][:80]}")
                    if n.get("concept"):
                        lines.append(f"  *概念：{n['concept']}*")
                response = "\n".join(lines)
            else:
                response = f"没有找到包含「{query}」的笔记。"
        else:
            response = "你想搜索什么笔记？试试「找笔记 overlay2」。"

    elif intent == "note_list":
        notes = nm.list_notes()
        if notes:
            lines = ["## 📝 我的笔记\n"]
            for n in notes[:20]:
                lines.append(f"- **{n['created_at'][:16]}** {n['content'][:80]}")
                if n.get("concept"):
                    lines.append(f"  *概念：{n['concept']}*")
            response = "\n".join(lines)
        else:
            response = "你还没有记录过笔记。试试「记笔记 <内容>」。"

    elif intent == "note_export":
        export = nm.export_notes()
        export_file = NOTES_DIR / "my-notes.md"
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        export_file.write_text(export, encoding="utf-8")
        response = f"✅ 笔记已导出到 `{export_file}`"

    elif intent == "general":
        # 通用回复：尝试检测误解、概念、或建议
        mc_result = handle_misconception_detection_and_correction(user_input, context)
        if mc_result:
            response = mc_result
        elif concepts:
            response = handle_concept_question(concepts[0], context)
        else:
            response = "想学什么？试试「帮助」查看所有功能。"

    # 4. 更新上下文
    context.add_dialogue(user_input, response)
    if concepts:
        context.set_concept(concepts[0])

    # 5. 记录日志
    daily_log.append(f"\n### 对话\n**用户**：{user_input}\n**系统**：{response[:100]}...\n")

    return {
        "response": response,
        "intent": intent,
        "concepts": concepts,
        "mastery_delta": mastery_delta,
    }


# ============================================================
# 主入口
# ============================================================

def main():
    """交互式学习会话"""
    print("=" * 52)
    print("  🐳 Docker 源码学习系统 v0.3")
    print("  🔬 6 大引擎 | 30+ 命令 | 8 种人格")
    print("=" * 52)

    initialize()
    quiz_manager.bank.load()
    mastery_v2.load()
    long_term_memory.load()
    user_profile.load()

    context = create_context()

    # 尝试恢复会话
    recovery = session_manager.get_recovery_prompt()
    if recovery:
        print(f"\n{recovery}")
    elif user_profile.profile["session_count"] == 0:
        # 新用户引导
        print(f"\n{ux.onboarding()}")

    # 更新用户画像
    user_profile.profile["session_count"] += 1
    user_profile.save()

    # 每日问候
    print(f"\n{ux.good_morning()}")

    print("\n输入「帮助」查看所有命令，输入「退出」结束会话。\n")

    while True:
        try:
            user_input = input("\n🧑‍💻 > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("退出", "exit", "quit"):
                session_manager.save_session(context.__dict__)
                print("\n👋 下次见！继续加油！")
                break

            result = process_input(user_input, context)
            response = result['response']

            # 检测里程碑
            milestone = ux.celebrate_milestone()
            if milestone:
                response += f"\n\n{milestone}"

            print(f"\n🤖 {response}")

        except KeyboardInterrupt:
            print("\n\n👋 下次见！")
            break
        except Exception as e:
            print(f"\n❌ 出错了：{e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()