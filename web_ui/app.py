#!/usr/bin/env python3
"""
Docker 源码学习系统 — Streamlit Web UI
========================================
启动方式：streamlit run web_ui/app.py
"""

import sys
import os
from pathlib import Path

# 将项目根目录加入路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from datetime import datetime

# ---- 初始化引擎 ----
from engine.knowledge_graph import kg, create_context, initialize, SessionContext
from engine.knowledge_base import kb, bm, nm, NOTES_DIR
from engine.quiz_engine import quiz_manager, Question, QuizSession, Scorer
from engine.mastery_engine import mastery_v2, practice_planner, get_retention_rate
from engine.visualization_engine import viz
from engine.research_engine import research
from engine.memory_engine import long_term_memory, user_profile, daily_summary
from engine.persona_engine import persona_engine, learning_path
from engine.dashboard_engine import dashboard, flow_engine, system_commands, ux
from engine.orchestrator import process_input, INTENT_PATTERNS

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Docker 源码学习系统",
    page_icon="🐳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 初始化会话状态
# ============================================================
def init_session_state():
    """初始化 Streamlit 会话状态"""
    if "initialized" not in st.session_state:
        with st.spinner("正在初始化学习系统..."):
            initialize()
            quiz_manager.bank.load()
            mastery_v2.load()
            long_term_memory.load()
            user_profile.load()
            learning_path.load()

        st.session_state.initialized = True
        st.session_state.context = create_context()
        st.session_state.messages = []
        st.session_state.quiz_active = False
        st.session_state.quiz_session = None
        st.session_state.quiz_index = 0
        st.session_state.quiz_answers = []
        st.session_state.quiz_feedback = []
        st.session_state.page = "chat"
        st.session_state.current_persona = persona_engine.current or "socratic"
        st.session_state.search_query = ""

        # 添加欢迎消息
        welcome = ux.greet() if hasattr(ux, 'greet') else "欢迎来到 Docker 源码学习系统！"
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"🐳 {welcome}\n\n输入「引导」查看新手教程，或直接开始学习！"
        })


init_session_state()

# ============================================================
# 辅助函数
# ============================================================

def handle_chat_input(user_input: str):
    """处理用户输入并生成回复"""
    if not user_input.strip():
        return

    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 处理输入
    with st.spinner("思考中..."):
        result = process_input(user_input, st.session_state.context)
        response = result["response"]

    # 添加助手回复
    st.session_state.messages.append({"role": "assistant", "content": response})

    # 更新当前人格
    st.session_state.current_persona = persona_engine.current or "socratic"


def get_mastery_data():
    """获取掌握度数据"""
    all_concepts = kg.get_all_concepts()
    data = []
    for c in all_concepts:
        rec = mastery_v2.get(c.name)
        data.append({
            "name": c.name,
            "level": rec.level,
            "attempts": rec.attempts,
            "correct": rec.correct,
            "accuracy": rec.accuracy,
            "next_review": rec.next_review,
        })
    return sorted(data, key=lambda x: x["level"])


def get_persona_display_name(p: str) -> str:
    """获取人格的中文显示名"""
    names = {
        "socratic": "苏格拉底",
        "professor": "教授",
        "practitioner": "实践者",
        "storyteller": "说书人",
        "coach": "教练",
        "debugger": "调试者",
        "minimalist": "极简者",
        "devils_advocate": "唱反调",
    }
    return names.get(p, p)


# ============================================================
# 侧边栏导航
# ============================================================
with st.sidebar:
    st.markdown("# 🐳 Docker 学习系统")
    st.markdown("---")

    # 导航
    st.markdown("### 📍 导航")
    pages = {
        "chat": "💬 对话",
        "dashboard": "📊 仪表盘",
        "knowledge": "📚 知识图谱",
        "quiz": "📝 测验",
        "mastery": "🎯 掌握度",
        "research": "🔬 深度研究",
        "books": "📖 书籍",
        "notes": "📓 笔记",
        "settings": "⚙️ 设置",
    }

    for page_id, page_label in pages.items():
        if st.button(page_label, use_container_width=True, key=f"nav_{page_id}"):
            st.session_state.page = page_id
            st.rerun()

    st.markdown("---")

    # 人格选择器
    st.markdown("### 🎭 人格")
    current = st.session_state.current_persona
    persona_names = {p: get_persona_display_name(p) for p in persona_engine.personas.keys()}
    selected = st.selectbox(
        "教学风格",
        options=list(persona_names.keys()),
        format_func=lambda x: f"{persona_names[x]} ({x})",
        index=list(persona_names.keys()).index(current) if current in persona_names else 0,
        label_visibility="collapsed",
    )
    if selected != current:
        persona_engine.switch(selected)
        st.session_state.current_persona = selected
        st.success(f"已切换到「{get_persona_display_name(selected)}」风格")
        st.rerun()

    # 快速统计
    st.markdown("---")
    st.markdown("### 📈 学习统计")
    all_data = get_mastery_data()
    if all_data:
        avg = sum(d["level"] for d in all_data) / len(all_data)
        practiced = sum(1 for d in all_data if d["attempts"] > 0)
        mastered = sum(1 for d in all_data if d["level"] >= 0.7)
        st.markdown(f"- **平均掌握度**: {avg:.0%}")
        st.markdown(f"- **已练习**: {practiced}/{len(all_data)} 概念")
        st.markdown(f"- **已掌握**: {mastered} 个概念")

    # 版本信息
    st.markdown("---")
    st.caption("v1.0 | 6 大引擎 | 8 种人格")


# ============================================================
# 页面路由
# ============================================================
page = st.session_state.page

# ============================================================
# 页面: 对话
# ============================================================
if page == "chat":
    st.title("💬 对话式学习")

    # 显示聊天历史
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 输入框
    user_input = st.chat_input("输入你想学的内容...")
    if user_input:
        handle_chat_input(user_input)
        st.rerun()

# ============================================================
# 页面: 仪表盘
# ============================================================
elif page == "dashboard":
    st.title("📊 学习仪表盘")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎯 学习总览")
        overview = dashboard.overview()
        st.markdown(overview)

    with col2:
        st.markdown("### 📈 掌握度分布")
        all_data = get_mastery_data()
        if all_data:
            levels = [d["level"] for d in all_data]
            names = [d["name"] for d in all_data]
            st.bar_chart(
                data={"掌握度": levels},
                use_container_width=True,
            )
            # 显示掌握度列表
            for d in reversed(all_data):
                emoji = "🟢" if d["level"] >= 0.7 else "🟡" if d["level"] >= 0.4 else "🔴"
                st.markdown(f"{emoji} **{d['name']}**: {d['level']:.0%}")

    with col3:
        st.markdown("### 🔄 学习闭环")
        flow_type = st.radio(
            "选择学习模式",
            ["发现新概念", "强化薄弱点", "到期复习", "深入探究"],
            index=0,
            label_visibility="collapsed",
        )
        flow_map = {
            "发现新概念": "discover",
            "强化薄弱点": "weak",
            "到期复习": "review",
            "深入探究": "deep",
        }
        if st.button("开始学习", use_container_width=True, type="primary"):
            flow_id = flow_map[flow_type]
            result = flow_engine.start_flow(flow_id, st.session_state.context)
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.session_state.page = "chat"
            st.rerun()

    # 下方：系统命令
    st.markdown("---")
    cmd_col1, cmd_col2, cmd_col3 = st.columns(3)
    with cmd_col1:
        if st.button("📊 学习统计", use_container_width=True):
            stats = system_commands.stats()
            st.info(stats)
    with cmd_col2:
        if st.button("💾 导出数据", use_container_width=True):
            result = system_commands.export()
            st.success(result)
    with cmd_col3:
        if st.button("🏆 里程碑", use_container_width=True):
            ms = ux.milestone() if hasattr(ux, 'milestone') else "里程碑功能已就绪"
            st.info(ms)

# ============================================================
# 页面: 知识图谱
# ============================================================
elif page == "knowledge":
    st.title("📚 知识图谱")

    # 搜索
    search = st.text_input("搜索概念", placeholder="输入概念名称...")
    all_concepts = kg.get_all_concepts()

    if search:
        results = kg.search_concepts(search)
        concepts_to_show = results if results else []
    else:
        concepts_to_show = all_concepts

    # 概念列表
    for c in concepts_to_show:
        rec = mastery_v2.get(c.name)
        # Display name with English
        display_name = c.name
        if c.english_name and c.english_name not in c.name:
            display_name = f"{c.name} ({c.english_name})"
        with st.expander(f"{display_name}  (Mastery: {rec.level:.0%})"):
            st.markdown(f"**Definition**: {c.definition}")
            if c.english_definition:
                st.markdown(f"**English**: {c.english_definition}")
            if c.code_ref:
                st.markdown(f"**Source**: `{c.code_ref}`")
            if c.prerequisites:
                st.markdown(f"**前置知识**: {', '.join(c.prerequisites)}")
            if c.related:
                st.markdown(f"**关联概念**: {', '.join(c.related)}")
            if c.misconceptions:
                st.markdown("**常见误解**:")
                for mc in c.misconceptions:
                    severity = "🔴" if mc.get("severity") == "critical" else "🟡"
                    st.markdown(f"- {severity} {mc.get('pattern', '')}")
                    st.markdown(f"  *纠正: {mc.get('correction', '')}*")

            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"💬 学习 {c.name}", key=f"learn_{c.name}"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"讲讲 {c.name}"
                    })
                    handle_chat_input(f"讲讲 {c.name}")
                    st.session_state.page = "chat"
                    st.rerun()
            with col2:
                if st.button(f"📝 出题 {c.name}", key=f"quiz_{c.name}"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"考考我 {c.name}"
                    })
                    handle_chat_input(f"考考我 {c.name}")
                    st.session_state.page = "chat"
                    st.rerun()
            with col3:
                if st.button(f"🔬 研究 {c.name}", key=f"research_{c.name}"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"深入 {c.name}"
                    })
                    handle_chat_input(f"深入 {c.name}")
                    st.session_state.page = "chat"
                    st.rerun()

    # 可视化
    st.markdown("---")
    st.markdown("### 🎨 知识图谱可视化")
    viz_types = {
        "知识图谱总览": "knowledgegraph",
        "架构层次": "architecture",
        "学习路径": "learningpath",
    }
    viz_choice = st.selectbox("选择图表类型", list(viz_types.keys()), label_visibility="collapsed")
    if st.button("生成图表", use_container_width=True):
        vtype = viz_types[viz_choice]
        if vtype == "knowledgegraph":
            diagram = viz.knowledge_graph()
        elif vtype == "architecture":
            diagram = viz.architecture_diagram()
        elif vtype == "learningpath":
            diagram = viz.learning_path()
        else:
            diagram = "暂不支持"
        st.markdown(diagram)

# ============================================================
# 页面: 测验
# ============================================================
elif page == "quiz":
    st.title("📝 测验")

    # 测验配置
    if not st.session_state.quiz_active:
        st.markdown("### 开始新测验")

        all_concepts = kg.get_all_concepts()
        concept_names = [c.name for c in all_concepts]

        col1, col2 = st.columns(2)
        with col1:
            target_concept = st.selectbox("选择概念范围", ["全部"] + concept_names)
            difficulty = st.select_slider("难度", options=["简单", "中等", "困难", "综合"], value="综合")
        with col2:
            question_count = st.slider("题目数量", 1, 10, 5)
            types = ["multiple_choice", "true_false", "fill_blank", "code_analysis"]
            qtype = st.selectbox("题型", ["混合"] + types)

        if st.button("开始答题", type="primary", use_container_width=True):
            # 获取题目
            if target_concept == "全部":
                questions = quiz_manager.bank.questions
            else:
                questions = [q for q in quiz_manager.bank.questions if target_concept in q.concepts]

            if not questions:
                st.warning("该范围暂无题目，请先学习相关概念。")
            else:
                # 随机选择
                selected = random.sample(questions, min(question_count, len(questions)))
                st.session_state.quiz_session = selected
                st.session_state.quiz_index = 0
                st.session_state.quiz_answers = []
                st.session_state.quiz_feedback = []
                st.session_state.quiz_active = True
                st.rerun()

    # 答题界面
    else:
        questions = st.session_state.quiz_session
        idx = st.session_state.quiz_index

        if idx < len(questions):
            q = questions[idx]
            progress_text = f"第 {idx + 1}/{len(questions)} 题"
            st.progress((idx) / len(questions), text=progress_text)

            # 题目信息
            st.markdown(f"### 题目 {idx + 1}")
            st.markdown(f"**难度**: {'⭐' * int(q.difficulty * 5 + 1)}")
            st.markdown(f"**题型**: {q.type}")
            st.markdown(f"**概念**: {', '.join(q.concepts)}")
            st.markdown("---")
            st.markdown(q.body)

            # 根据题型显示输入
            answer = None
            if q.type == "multiple_choice" and q.options:
                answer = st.radio("选择答案", q.options, key=f"q_{idx}_radio")
            elif q.type == "true_false":
                answer = st.radio("选择", ["正确", "错误"], key=f"q_{idx}_tf")
            elif q.type in ("fill_blank", "code_analysis"):
                answer = st.text_area("输入你的答案", key=f"q_{idx}_text", height=100)
            else:
                answer = st.text_input("输入答案", key=f"q_{idx}_input")

            # 提交按钮
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("提交答案", type="primary", use_container_width=True):
                    if not answer:
                        st.warning("请先输入答案")
                    else:
                        # 评分
                        scorer = Scorer(q.type)
                        is_correct, score = scorer.score(q, answer)

                        # 记录
                        st.session_state.quiz_answers.append(answer)
                        st.session_state.quiz_feedback.append({
                            "correct": is_correct,
                            "score": score,
                            "correct_answer": q.answer,
                            "explanation": q.explanation,
                        })

                        # 显示反馈
                        if is_correct:
                            st.success(f"✅ 正确！得分: {score:.0%}")
                        else:
                            st.error(f"❌ 不正确。得分: {score:.0%}")
                            st.info(f"正确答案: {q.answer}")

                        if q.explanation:
                            st.markdown(f"**解析**: {q.explanation}")

                        # 下一题按钮
                        if st.button("下一题 →", use_container_width=True):
                            st.session_state.quiz_index += 1
                            st.rerun()

        else:
            # 测验完成
            st.balloons()
            st.markdown("## 🎉 测验完成！")

            # 统计
            feedbacks = st.session_state.quiz_feedback
            correct_count = sum(1 for f in feedbacks if f["correct"])
            total = len(feedbacks)
            accuracy = correct_count / total if total > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("正确", f"{correct_count}/{total}")
            with col2:
                st.metric("正确率", f"{accuracy:.0%}")
            with col3:
                st.metric("平均得分", f"{sum(f['score'] for f in feedbacks) / total:.0%}" if total > 0 else "0%")

            # 详情
            st.markdown("### 答题详情")
            for i, (q, fb) in enumerate(zip(questions, feedbacks)):
                emoji = "✅" if fb["correct"] else "❌"
                with st.expander(f"{emoji} 第 {i+1} 题: {q.body[:50]}..."):
                    st.markdown(f"**你的答案**: {st.session_state.quiz_answers[i]}")
                    st.markdown(f"**正确答案**: {fb['correct_answer']}")
                    st.markdown(f"**解析**: {fb['explanation']}")

            # 更新掌握度
            if st.button("更新掌握度并返回", type="primary", use_container_width=True):
                for q, fb in zip(questions, feedbacks):
                    for concept in q.concepts:
                        rec = mastery_v2.get(concept)
                        old_level = rec.level
                        delta = 0.1 if fb["correct"] else -0.05
                        rec.level = max(0.0, min(1.0, rec.level + delta))
                        rec.attempts += 1
                        if fb["correct"]:
                            rec.correct += 1
                        rec.last_practiced = datetime.now().strftime("%Y-%m-%d %H:%M")
                        mastery_v2.set(concept, rec)
                mastery_v2.save()
                st.success("✅ 掌握度已更新！")

                # 重置
                st.session_state.quiz_active = False
                st.session_state.quiz_session = None
                st.rerun()

# ============================================================
# 页面: 掌握度
# ============================================================
elif page == "mastery":
    st.title("🎯 掌握度")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 掌握度热力图")
        all_data = get_mastery_data()
        if all_data:
            # 分组
            mastered = [d for d in all_data if d["level"] >= 0.7]
            learning = [d for d in all_data if 0.4 <= d["level"] < 0.7]
            new = [d for d in all_data if d["level"] < 0.4]

            st.markdown("#### 🟢 已掌握 (>= 70%)")
            for d in mastered:
                st.markdown(f"- **{d['name']}**: {d['level']:.0%} ({d['correct']}/{d['attempts']} 正确)")

            st.markdown("#### 🟡 学习中 (40-70%)")
            for d in learning:
                st.markdown(f"- **{d['name']}**: {d['level']:.0%} ({d['correct']}/{d['attempts']} 正确)")

            st.markdown("#### 🔴 待学习 (< 40%)")
            for d in new:
                st.markdown(f"- **{d['name']}**: {d['level']:.0%} ({d['attempts']} 次练习)")

            # 柱状图
            st.markdown("### 📊 掌握度分布")
            chart_data = {d["name"]: d["level"] for d in all_data}
            st.bar_chart(chart_data, use_container_width=True)

    with col2:
        st.markdown("### 🔄 到期复习")
        now = datetime.now()
        due = []
        for d in all_data:
            if d["next_review"] and d["attempts"] > 0:
                try:
                    review_date = datetime.strptime(d["next_review"], "%Y-%m-%d")
                    if review_date <= now:
                        due.append(d)
                except:
                    pass

        if due:
            for d in sorted(due, key=lambda x: x["level"]):
                st.markdown(f"- ⏰ **{d['name']}**: {d['level']:.0%}")
        else:
            st.info("暂无到期复习内容")

        st.markdown("---")
        st.markdown("### 📈 遗忘曲线")
        # 用 retention rate 展示
        for d in all_data[:5]:
            rate = get_retention_rate(d["name"])
            bar_width = int(rate * 100)
            bar = "█" * (bar_width // 5) + "░" * (20 - bar_width // 5)
            st.markdown(f"**{d['name']}**: {bar} {rate:.0%}")

        # 生成 Mermaid 热力图
        st.markdown("---")
        if st.button("生成 Mermaid 热力图", use_container_width=True):
            diagram = viz.heatmap()
            st.markdown(diagram)

# ============================================================
# 页面: 深度研究
# ============================================================
elif page == "research":
    st.title("🔬 深度研究")

    all_concepts = kg.get_all_concepts()
    concept_names = [c.name for c in all_concepts]

    col1, col2 = st.columns([3, 1])
    with col1:
        target = st.selectbox("选择研究主题", concept_names)
    with col2:
        st.markdown("### &nbsp;")
        if st.button("生成研究报告", type="primary", use_container_width=True):
            with st.spinner(f"正在研究 {target}..."):
                report = research.generate_report(target)
                if report:
                    st.session_state.research_report = report
                    st.session_state.research_topic = target
                else:
                    st.warning("暂无该主题的研究数据")

    # 显示研究报告
    if "research_report" in st.session_state and st.session_state.research_report:
        st.markdown("---")
        st.markdown(st.session_state.research_report)

        # 导出
        if st.button("📥 导出为 Markdown", use_container_width=True):
            export_path = ROOT / "research" / f"{st.session_state.research_topic}-研究报告.md"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(st.session_state.research_report, encoding="utf-8")
            st.success(f"已导出到 {export_path}")

    # 可视化
    st.markdown("---")
    st.markdown("### 🎨 相关可视化")
    if st.button("生成调用链图", use_container_width=True):
        diagram = viz.call_chain(target if 'target' in dir() else "容器运行时")
        st.markdown(diagram)

# ============================================================
# 页面: 书籍
# ============================================================
elif page == "books":
    st.title("📖 交互式书籍")

    # 书籍列表
    books = bm.list_books()
    if not books:
        st.info("暂无书籍，请先添加。")
    else:
        book_names = [b["title"] for b in books]
        selected_book = st.selectbox("选择书籍", book_names)

        if selected_book:
            book = bm.get_book(selected_book)
            if book and "chapters" in book:
                chapters = book["chapters"]
                chapter_names = [ch.get("title", f"第 {i+1} 章") for i, ch in enumerate(chapters)]
                selected_chapter = st.selectbox("选择章节", chapter_names)

                if selected_chapter:
                    ch_idx = chapter_names.index(selected_chapter)
                    chapter = bm.get_chapter(selected_book, ch_idx)

                    if chapter:
                        st.markdown(f"## {selected_chapter}")
                        st.markdown(chapter.get("content", "（暂无内容）"))

                        # 进度追踪
                        progress = bm.get_progress(selected_book)
                        st.markdown(f"**阅读进度**: {progress.get('progress', 0)}%")

                        if st.button("标记为已读", use_container_width=True):
                            bm.update_progress(selected_book, ch_idx)
                            st.success("进度已更新！")

                        # 操作
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📝 记笔记", use_container_width=True):
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": f"记笔记 正在阅读《{selected_book}》- {selected_chapter}"
                                })
                                st.session_state.page = "chat"
                                st.rerun()
                        with col2:
                            if st.button("📝 章节测验", use_container_width=True):
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": f"考考我 {selected_chapter}"
                                })
                                st.session_state.page = "chat"
                                st.rerun()

# ============================================================
# 页面: 笔记
# ============================================================
elif page == "notes":
    st.title("📓 笔记管理")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 新建笔记")
        note_content = st.text_area("笔记内容", placeholder="记录你的学习心得...", height=150)
        note_concept = st.selectbox(
            "关联概念（可选）",
            [""] + [c.name for c in kg.get_all_concepts()],
        )

        if st.button("保存笔记", type="primary", use_container_width=True):
            if note_content:
                nm.add_note(note_content, note_concept if note_concept else None)
                st.success("笔记已保存！")
                st.rerun()
            else:
                st.warning("请输入笔记内容")

    with col2:
        st.markdown("### 搜索笔记")
        search_query = st.text_input("搜索", placeholder="关键词...", label_visibility="collapsed")
        if search_query:
            results = nm.search_notes(search_query)
            if results:
                st.markdown(f"找到 {len(results)} 条结果")
                for r in results[:10]:
                    st.markdown(f"- {r['created_at'][:16]}: {r['content'][:50]}...")
            else:
                st.info("无匹配结果")

    # 笔记列表
    st.markdown("---")
    st.markdown("### 所有笔记")
    all_notes = nm.list_notes()
    if all_notes:
        for n in reversed(all_notes[-20:]):
            with st.expander(f"{n['created_at'][:16]} — {n['content'][:60]}..."):
                st.markdown(n["content"])
                if n.get("concept"):
                    st.markdown(f"*关联概念: {n['concept']}*")
    else:
        st.info("暂无笔记")

    # 导出
    if all_notes and st.button("📥 导出笔记为 Markdown", use_container_width=True):
        export = nm.export_notes()
        export_path = NOTES_DIR / "my-notes.md"
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        export_path.write_text(export, encoding="utf-8")
        st.success(f"已导出到 {export_path}")

# ============================================================
# 页面: 设置
# ============================================================
elif page == "settings":
    st.title("⚙️ 设置")

    st.markdown("### 🎭 人格设置")
    persona_names = {p: get_persona_display_name(p) for p in persona_engine.personas.keys()}

    for pid, pname in persona_names.items():
        with st.expander(f"{pname} ({pid})"):
            info = persona_engine.get_persona_info(pid)
            if info:
                st.markdown(info)
            if st.button(f"切换为 {pname}", key=f"set_{pid}"):
                persona_engine.switch(pid)
                st.session_state.current_persona = pid
                st.success(f"已切换到「{pname}」风格")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🗄️ 数据管理")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 查看统计", use_container_width=True):
            stats = system_commands.stats()
            st.info(stats)
    with col2:
        if st.button("💾 导出所有数据", use_container_width=True):
            result = system_commands.export()
            st.success(result)
    with col3:
        if st.button("🏆 查看里程碑", use_container_width=True):
            ms = ux.milestone() if hasattr(ux, 'milestone') else "学习里程碑"
            st.info(ms)

    st.markdown("---")
    st.markdown("### ℹ️ 系统信息")
    st.markdown(f"- **引擎版本**: v1.0")
    st.markdown(f"- **核心概念**: {len(kg.get_all_concepts())} 个")
    st.markdown(f"- **题库**: {len(quiz_manager.bank.questions)} 道")
    st.markdown(f"- **人格预设**: {len(persona_engine.personas)} 种")
    st.markdown(f"- **当前人格**: {get_persona_display_name(st.session_state.current_persona)}")

    # 危险操作
    st.markdown("---")
    st.markdown("### ⚠️ 危险操作")
    with st.expander("重置学习进度"):
        st.warning("此操作将清除所有掌握度数据和练习记录，不可恢复！")
        confirm = st.text_input("输入 RESET 确认重置")
        if st.button("确认重置", type="secondary", use_container_width=True):
            if confirm == "RESET":
                result = system_commands.reset()
                st.success(result)
                st.rerun()
            else:
                st.error("请输入 RESET 确认")


# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.caption("🐳 Docker 源码学习系统 | 知识图谱驱动 · 多智能体协作 · 间隔重复 · 8 种人格")