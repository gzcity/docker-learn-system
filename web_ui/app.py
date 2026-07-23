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
import plotly.express as px
import plotly.graph_objects as go
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
from engine.go_ast_parser import source_analyzer, DOCKER_SOURCE_FILES
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
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("思考中..."):
        result = process_input(user_input, st.session_state.context)
        response = result["response"]
    st.session_state.messages.append({"role": "assistant", "content": response})
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


def render_mermaid_diagram(diagram_code: str, render_mode: str = "image"):
    """渲染 Mermaid 图表"""
    if render_mode == "code":
        st.code(diagram_code, language="markdown")
    else:
        # 使用 mermaid.ink API
        import base64
        diagram_bytes = diagram_code.strip().encode("utf-8")
        base64_string = base64.urlsafe_b64encode(diagram_bytes).decode("ascii")
        mermaid_url = f"https://mermaid.ink/img/{base64_string}?type=png"
        st.image(mermaid_url, use_container_width=True)


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
        "charts": "📈 图表",
        "quiz": "📝 测验",
        "mastery": "🎯 掌握度",
        "research": "🔬 深度研究",
        "source": "🔍 源码分析",
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
        st.success(f"已切换到「{get_persona_display_name(selected)}」")
        st.rerun()

    st.markdown("---")

    # 学习统计
    st.markdown("### 📊 学习统计")
    mastery_data = get_mastery_data()
    avg = sum(d["level"] for d in mastery_data) / len(mastery_data) if mastery_data else 0
    st.metric("平均掌握度", f"{avg:.0%}")
    st.metric("已学概念", sum(1 for d in mastery_data if d["attempts"] > 0))
    st.metric("精通概念", sum(1 for d in mastery_data if d["level"] >= 0.7))


# ============================================================
# 路由
# ============================================================
page = st.session_state.page

# ============================================================
# 页面: 对话
# ============================================================
if page == "chat":
    st.title("💬 对话式学习")

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

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
            colors = []
            for d in all_data:
                if d["level"] >= 0.7:
                    colors.append("#22c55e")
                elif d["level"] >= 0.4:
                    colors.append("#eab308")
                else:
                    colors.append("#ef4444")

            fig = go.Figure(go.Bar(
                x=[d["name"] for d in all_data],
                y=[d["level"] for d in all_data],
                marker_color=colors,
                text=[f"{d['level']:.0%}" for d in all_data],
                textposition="auto",
            ))
            fig.update_layout(
                yaxis_title="掌握度",
                yaxis_range=[0, 1],
                height=350,
                margin=dict(l=20, r=20, t=20, b=60),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown("### 🎯 阶段进度")
        avg_level = sum(d["level"] for d in all_data) / len(all_data) if all_data else 0
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_level * 100,
            number={"suffix": "%", "font": {"size": 36}},
            title={"text": "平均掌握度"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#3b82f6"},
                "steps": [
                    {"range": [0, 40], "color": "#fee2e2"},
                    {"range": [40, 70], "color": "#fef9c3"},
                    {"range": [70, 100], "color": "#dcfce7"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 70,
                },
            },
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("#### 选择学习模式")
        flow_type = st.radio(
            "学习模式",
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

    all_concepts = kg.get_all_concepts()
    difficulty_filter = st.select_slider(
        "难度过滤",
        options=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        value=0.0,
    )

    concepts_to_show = [c for c in all_concepts if c.difficulty >= difficulty_filter]
    st.markdown(f"显示 {len(concepts_to_show)}/{len(all_concepts)} 个概念")

    for c in concepts_to_show:
        rec = mastery_v2.get(c.name)
        display_name = c.name
        if c.english_name and c.english_name not in c.name:
            display_name = f"{c.name} ({c.english_name})"
        with st.expander(f"{display_name}  (Mastery: {rec.level:.0%})"):
            st.markdown(f"**Definition**: {c.definition}")
            if c.english_definition:
                st.markdown(f"**English**: {c.english_definition}")
            if c.code_ref:
                st.markdown(f"**Source**: `{c.code_ref}`")
            prereqs = kg.get_prerequisites(c.name)
            if prereqs:
                st.markdown(f"**Prerequisites**: {', '.join(p.name for p in prereqs)}")
            related = kg.get_related_concepts(c.name)
            if related:
                st.markdown(f"**Related**: {', '.join(r.name for r in related)}")
            if c.misconceptions:
                st.markdown("**常见误解**:")
                for mc in c.misconceptions:
                    st.markdown(f"- ❌ {mc['pattern']} → ✅ {mc['correction']}")

# ============================================================
# 页面: 图表可视化
# ============================================================
elif page == "charts":
    st.title("📈 图表可视化")

    diagram_types = viz.list_diagram_types()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎨 图表类型")
        all_concepts = kg.get_all_concepts()
        concept_names = [c.name for c in all_concepts]

        selected_diagram = st.radio(
            "选择图表类型",
            [d["name"] for d in diagram_types],
        )
        target_concept = st.selectbox("焦点概念（可选）", ["(无)"] + concept_names)

        if st.button("生成图表", type="primary", use_container_width=True):
            focus = "" if target_concept == "(无)" else target_concept
            diagram = ""
            if selected_diagram == "architecture":
                diagram = viz.generate_architecture(focus)
            elif selected_diagram == "call_chain":
                diagram = viz.generate_call_chain(focus)
            elif selected_diagram == "learning_path":
                diagram = viz.generate_learning_path(focus)
            elif selected_diagram == "knowledge_graph":
                diagram = viz.generate_knowledge_graph()
            elif selected_diagram == "data_flow":
                diagram = viz.generate_data_flow(focus)
            elif selected_diagram in ("study_progress", "heatmap"):
                diagram = viz.generate_study_progress()
            elif selected_diagram == "class_diagram":
                diagram = viz.generate_class_diagram(focus)

            if diagram:
                st.session_state.current_diagram = diagram
                st.session_state.current_diagram_type = selected_diagram

    with col2:
        st.markdown("### 📊 图表预览")
        if "current_diagram" in st.session_state and st.session_state.current_diagram:
            diagram = st.session_state.current_diagram

            render_mode = st.radio(
                "渲染方式",
                ["Mermaid 代码", "mermaid.ink 图片"],
                horizontal=True,
                key="chart_render_mode",
            )

            render_mermaid_diagram(diagram, render_mode)

            # 下载
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "📥 下载 Mermaid 源码",
                    diagram,
                    file_name=f"{st.session_state.get('current_diagram_type', 'chart')}.mmd",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_dl2:
                import base64
                base64_string = base64.urlsafe_b64encode(diagram.strip().encode("utf-8")).decode("ascii")
                svg_url = f"https://mermaid.ink/img/{base64_string}?type=svg"
                st.markdown(f"[🔗 打开 SVG]({svg_url})")
        else:
            st.info("点击「生成图表」开始")

    # 图表说明
    st.markdown("---")
    st.markdown("### 📖 图表类型说明")
    cols = st.columns(4)
    for i, dt in enumerate(diagram_types):
        with cols[i % 4]:
            st.markdown(f"**{dt['name']}**")
            st.caption(dt['desc'])

# ============================================================
# 页面: 测验
# ============================================================
elif page == "quiz":
    st.title("📝 测验")

    if not st.session_state.quiz_active:
        st.markdown("### 开始测验")
        quiz_scope = st.radio(
            "测验范围",
            ["全部", "特定概念", "薄弱点"],
            horizontal=True,
        )

        target_concept = None
        if quiz_scope == "特定概念":
            all_concepts = kg.get_all_concepts()
            concept_names = [c.name for c in all_concepts]
            target_concept = st.selectbox("选择概念", concept_names)
        elif quiz_scope == "薄弱点":
            all_data = get_mastery_data()
            weak = [d for d in all_data if d["level"] < 0.5]
            if weak:
                st.markdown("薄弱点: " + ", ".join(d["name"] for d in weak[:5]))
            else:
                st.info("暂无薄弱点")

        question_count = st.slider("题目数量", 3, 14, 5)

        if st.button("开始", type="primary", use_container_width=True):
            questions = quiz_manager.bank.questions
            if quiz_scope == "特定概念" and target_concept:
                questions = [q for q in questions if target_concept in q.concepts]
            elif quiz_scope == "薄弱点" and weak:
                weak_names = [d["name"] for d in weak[:5]]
                questions = [q for q in questions if any(w in q.concepts for w in weak_names)]

            if not questions:
                st.warning("该范围暂无题目")
            else:
                import random
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
            st.progress(idx / len(questions), text=f"第 {idx + 1}/{len(questions)} 题")

            st.markdown(f"### 题目 {idx + 1}")
            st.markdown(f"**难度**: {'⭐' * int(q.difficulty * 5 + 1)}")
            st.markdown(f"**题型**: {q.type}")
            st.markdown(f"**概念**: {', '.join(q.concepts)}")
            st.markdown("---")
            st.markdown(q.body)

            answer = None
            if q.type == "multiple_choice" and q.options:
                answer = st.radio("选择答案", q.options, key=f"q_{idx}_radio")
            elif q.type == "true_false":
                answer = st.radio("选择", ["正确", "错误"], key=f"q_{idx}_tf")
            elif q.type in ("fill_blank", "code_analysis"):
                answer = st.text_area("输入你的答案", key=f"q_{idx}_text", height=100)
            else:
                answer = st.text_input("输入答案", key=f"q_{idx}_input")

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("提交答案", type="primary", use_container_width=True):
                    if not answer:
                        st.warning("请先输入答案")
                    else:
                        scorer = Scorer(q.type)
                        is_correct, score = scorer.score(q, answer)
                        st.session_state.quiz_answers.append(answer)
                        st.session_state.quiz_feedback.append({
                            "correct": is_correct,
                            "score": score,
                            "correct_answer": q.answer,
                            "explanation": q.explanation,
                        })
                        if is_correct:
                            st.success(f"✅ 正确！得分: {score:.0%}")
                        else:
                            st.error(f"❌ 不正确。得分: {score:.0%}")
                        st.info(f"正确答案: {q.answer}\n\n解析: {q.explanation}")
                        st.session_state.quiz_index += 1
                        import time
                        time.sleep(1.5)
                        st.rerun()

        else:
            # 测验结束
            st.markdown("## 🎉 测验完成!")
            feedback = st.session_state.quiz_feedback
            correct_count = sum(1 for f in feedback if f["correct"])
            avg_score = sum(f["score"] for f in feedback) / len(feedback) if feedback else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("正确率", f"{correct_count}/{len(feedback)}")
            with col2:
                st.metric("平均得分", f"{avg_score:.0%}")
            with st.columns(3)[2]:
                st.metric("题目数", str(len(feedback)))

            if st.button("再来一次", use_container_width=True):
                st.session_state.quiz_active = False
                st.rerun()

# ============================================================
# 页面: 掌握度
# ============================================================
elif page == "mastery":
    st.title("🎯 掌握度")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📊 掌握度分布")
        all_data = get_mastery_data()
        if all_data:
            colors = []
            for d in all_data:
                if d["level"] >= 0.7:
                    colors.append("#22c55e")
                elif d["level"] >= 0.4:
                    colors.append("#eab308")
                else:
                    colors.append("#ef4444")

            fig = go.Figure(go.Bar(
                x=[d["name"] for d in all_data],
                y=[d["level"] for d in all_data],
                marker_color=colors,
                text=[f"{d['level']:.0%}" for d in all_data],
                textposition="auto",
            ))
            fig.update_layout(
                yaxis_title="掌握度",
                yaxis_range=[0, 1],
                height=300,
                margin=dict(l=20, r=20, t=20, b=80),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 散点图
            st.markdown("### 📈 掌握度 vs 准确率")
            fig_scatter = px.scatter(
                x=[d["attempts"] for d in all_data],
                y=[d["accuracy"] for d in all_data],
                size=[d["level"] * 30 + 5 for d in all_data],
                color=[d["level"] for d in all_data],
                color_continuous_scale="RdYlGn",
                hover_name=[d["name"] for d in all_data],
                labels={"x": "练习次数", "y": "准确率", "color": "掌握度"},
            )
            fig_scatter.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=40))
            st.plotly_chart(fig_scatter, use_container_width=True)

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
                except Exception:
                    pass

        if due:
            for d in sorted(due, key=lambda x: x["level"]):
                st.markdown(f"- ⏰ **{d['name']}**: {d['level']:.0%}")
        else:
            st.info("暂无到期复习内容")

        st.markdown("---")
        st.markdown("### 📈 遗忘曲线预测")
        import math
        days = list(range(0, 31))
        fig_decay = go.Figure()
        for d in all_data[:5]:
            if d["attempts"] > 0:
                retention = get_retention_rate(d["name"])
                stability = max(1, d["attempts"] * d["level"] * 2)
                decay_values = [retention * math.exp(-t / stability) for t in days]
                fig_decay.add_trace(go.Scatter(
                    x=days, y=decay_values,
                    mode="lines", name=d["name"],
                ))
        fig_decay.update_layout(
            xaxis_title="天数",
            yaxis_title="记忆保留率",
            yaxis_range=[0, 1],
            height=250,
            margin=dict(l=20, r=20, t=30, b=30),
            legend=dict(font=dict(size=9)),
        )
        st.plotly_chart(fig_decay, use_container_width=True)

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

    if "research_report" in st.session_state and st.session_state.research_report:
        st.markdown("---")
        st.markdown(st.session_state.research_report)

        if st.button("📥 导出为 Markdown", use_container_width=True):
            export_path = ROOT / "research" / f"{st.session_state.research_topic}-研究报告.md"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(st.session_state.research_report, encoding="utf-8")
            st.success(f"已导出到 {export_path}")

    # 可视化
    st.markdown("---")
    st.markdown("### 🎨 相关可视化")
    viz_col1, viz_col2 = st.columns(2)
    with viz_col1:
        if st.button("生成架构图", use_container_width=True):
            diagram = viz.generate_architecture(target)
            st.session_state.research_diagram = diagram
    with viz_col2:
        if st.button("生成调用链图", use_container_width=True):
            diagram = viz.generate_call_chain(target)
            st.session_state.research_diagram = diagram

    if "research_diagram" in st.session_state:
        render_mode = st.radio(
            "渲染方式",
            ["Mermaid 代码", "mermaid.ink 图片"],
            horizontal=True,
            key="research_render_mode",
        )
        render_mermaid_diagram(st.session_state.research_diagram, render_mode)

# ============================================================
# 页面: 源码分析
# ============================================================
elif page == "source":
    st.title("🔍 Go 源码分析")

    all_concepts = kg.get_all_concepts()
    concept_names = [c.name for c in all_concepts]

    col1, col2 = st.columns([3, 1])
    with col1:
        target = st.selectbox("选择要分析的概念", concept_names, key="source_concept")
    with col2:
        st.markdown("### &nbsp;")
        if st.button("🔬 分析源码", type="primary", use_container_width=True):
            with st.spinner(f"正在分析 {target} 的源码..."):
                report = source_analyzer.generate_source_report(target)
                st.session_state.source_report = report
                st.session_state.source_topic = target

    # 显示分析报告
    if "source_report" in st.session_state and st.session_state.source_report:
        st.markdown("---")
        st.markdown(st.session_state.source_report)

        if st.button("📥 导出为 Markdown", use_container_width=True):
            export_path = ROOT / "source-analysis" / f"{st.session_state.source_topic}-源码分析.md"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(st.session_state.source_report, encoding="utf-8")
            st.success(f"已导出到 {export_path}")

    # 缓存状态
    st.markdown("---")
    st.markdown("### 📦 缓存状态")
    cache_status = source_analyzer.get_cache_status()
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric("缓存文件数", cache_status["cached_files"])
    with col_c2:
        st.metric("缓存大小", f"{cache_status['total_size_kb']} KB")
    with col_c3:
        if st.button("🗑️ 清空缓存", use_container_width=True):
            import shutil
            cache_dir = Path(".cache/docker-source")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                st.success("缓存已清空")
            else:
                st.info("无缓存可清空")

    # 源码分类说明
    st.markdown("---")
    st.markdown("### 📂 源码分类")
    cols = st.columns(3)
    for i, (cat, info) in enumerate(DOCKER_SOURCE_FILES.items()):
        with cols[i % 3]:
            with st.expander(f"{cat}: {info['description']}"):
                for f in info["files"]:
                    st.markdown(f"- `{f['path']}`")

# ============================================================
# 页面: 书籍
# ============================================================
elif page == "books":
    st.title("📖 交互式书籍")

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

                        progress = bm.get_progress(selected_book)
                        st.markdown(f"**阅读进度**: {progress.get('progress', 0)}%")

                        if st.button("标记为已读", use_container_width=True):
                            bm.mark_chapter_read(selected_book, ch_idx)
                            st.success("已标记为已读")
                            st.rerun()

# ============================================================
# 页面: 笔记
# ============================================================
elif page == "notes":
    st.title("📓 笔记")

    st.markdown("### ✏️ 快速记笔记")
    note_text = st.text_area("笔记内容", height=150)
    all_concepts = kg.get_all_concepts()
    note_concept = st.selectbox(
        "关联概念（可选）",
        ["(无)"] + [c.name for c in all_concepts],
    )

    if st.button("保存笔记", type="primary", use_container_width=True):
        if note_text.strip():
            concept = None if note_concept == "(无)" else note_concept
            nm.add_note(note_text, concept)
            st.success("笔记已保存")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 搜索笔记")
    search = st.text_input("搜索关键词")
    if search:
        results = nm.search_notes(search)
        if results:
            st.markdown(f"找到 {len(results)} 条结果")
            for r in results[:10]:
                st.markdown(f"- {r['created_at'][:16]}: {r['content'][:50]}...")
        else:
            st.info("无匹配结果")

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
