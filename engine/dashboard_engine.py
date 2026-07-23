# Docker 源码学习系统 — 学习仪表盘引擎

"""
统一学习仪表盘和流程引擎，集成所有已有功能。
"""

from pathlib import Path
from datetime import datetime, timedelta

from .knowledge_graph import kg, MEMORY_DIR
from .mastery_engine import mastery_v2, practice_report, get_retention_rate
from .memory_engine import long_term_memory, user_profile, daily_summary
from .persona_engine import learning_path, persona_engine
from .quiz_engine import quiz_manager
from .knowledge_base import nm

# ============================================================
# 仪表盘引擎
# ============================================================

class DashboardEngine:
    """学习仪表盘引擎"""

    def overview(self) -> str:
        """学习总览"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        mastered = [r for r in practiced if r.level >= 0.7]
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0
        today = datetime.now().strftime("%Y-%m-%d")
        due = [r for r in records if r.next_review and r.next_review <= today]

        # 人格信息
        current_persona = user_profile.profile.get("preferred_persona", "socratic")
        persona_info = persona_engine.get_persona(current_persona)

        # 画像
        user_profile.update_strengths_weaknesses()
        p = user_profile.profile

        # 记忆摘要
        mem = long_term_memory.summarize()

        lines = [
            "## 📊 Docker 源码学习系统 — 总览",
            "",
            f"**学习阶段**: {_stage_name(avg_level)}",
            f"**总概念**: {len(all_concepts)} 个 | **已学**: {len(practiced)} 个 | **精通**: {len(mastered)} 个",
            f"**平均掌握度**: {avg_level:.0%}",
            f"**到期复习**: {len(due)} 个",
            f"**学习天数**: {mem['total_days']} 天 | **总会话**: {mem['total_sessions']} 次",
            "",
            "### 当前人格",
            f"**{persona_info['display_name'] if persona_info else current_persona}** — {persona_info['style'] if persona_info else ''}",
            "",
            "### 强项",
            *([f"- {s}" for s in p.get("strengths", [])[:3]] or ["- 暂无"]),
            "",
            "### 薄弱点",
            *([f"- {w}" for w in p.get("weaknesses", [])[:3]] or ["- 暂无"]),
            "",
            "### 快速操作",
            "- 看「学习路径」查看完整路径",
            "- 看「水平评估」详细了解",
            "- 看「快速练习」开始练习",
            "- 看「下一步」获取推荐",
        ]
        return "\n".join(lines)

    def dashboard(self) -> str:
        """完整仪表盘"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        mastered = [r for r in practiced if r.level >= 0.7]
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0
        today = datetime.now().strftime("%Y-%m-%d")
        due = [r for r in records if r.next_review and r.next_review <= today]

        mem = long_term_memory.summarize()

        # 掌握度分布
        def level_bar(level):
            filled = int(level * 10)
            return "█" * filled + "░" * (10 - filled)

        lines = [
            "## 📊 学习仪表盘",
            "",
            "### 🎯 总览",
            f"**阶段**: {_stage_name(avg_level)} | **概念**: {len(practiced)}/{len(all_concepts)} 已学 | **精通**: {mastered}",
            f"**平均掌握度**: {avg_level:.0%} | **到期复习**: {len(due)} 个",
            f"**学习天数**: {mem['total_days']} | **总会话**: {mem['total_sessions']}",
            "",
            "### 📈 掌握度分布",
        ]

        # 按掌握度排序
        sorted_records = sorted(records, key=lambda r: r.level, reverse=True)
        for r in sorted_records[:10]:
            status = "✅" if r.level >= 0.7 else "🔄" if r.attempts > 0 else "⬜"
            due_mark = " ⚠️" if r.next_review and r.next_review <= today else ""
            lines.append(f"{status} **{r.concept[:20]}**: {level_bar(r.level)} {r.level:.0%}{due_mark}")

        if len(sorted_records) > 10:
            lines.append(f"... 还有 {len(sorted_records) - 10} 个概念")

        # 到期复习
        lines.append("")
        lines.append("### 📌 到期复习")
        due_records = sorted([r for r in due], key=lambda x: x.level)
        if due_records:
            for r in due_records[:5]:
                lines.append(f"- {r.concept}（掌握度: {r.level:.0%}）")
        else:
            lines.append("- 今日无到期复习 🎉")

        # 推荐
        lines.append("")
        lines.append("### 🎯 推荐操作")
        next_rec = learning_path.recommend_next({})
        lines.append(f"- {next_rec['type']}: {next_rec['concept']}")
        lines.append("")
        lines.append("💡 试试「总览」查看简要总览，或「帮助」查看所有命令。")

        return "\n".join(lines)


# ============================================================
# 学习流引擎
# ============================================================

class FlowEngine:
    """学习流程引擎"""

    def discover_flow(self) -> str:
        """发现 → 学习 → 练习 闭环"""
        all_concepts = kg.get_all_concepts()
        untouched = [c for c in all_concepts if mastery_v2.get(c.name).attempts == 0]

        if not untouched:
            return "🎉 你已经学完所有概念！试试「复习」巩固。"

        next_concept = untouched[0]

        lines = [
            "## 🔍 发现 → 学习 → 练习",
            "",
            f"### 发现新概念：{next_concept.name}",
            f"*{next_concept.definition[:80]}...*" if next_concept.definition else "",
            "",
            "### 推荐流程",
            f"1️⃣ 学习：试试「什么是 {next_concept.name.split(' (')[0]}」",
            f"2️⃣ 深入：试试「研究 {next_concept.name.split(' (')[0]}」",
            f"3️⃣ 练习：试试「深度练习 {next_concept.name.split(' (')[0]}」",
            "",
            "### 关联概念",
        ]

        # 关联概念
        if next_concept.prerequisites:
            lines.append("**先修知识**:")
            for p in next_concept.prerequisites:
                lines.append(f"- {p}")
        if next_concept.related:
            lines.append("**关联概念**:")
            for r in next_concept.related:
                lines.append(f"- {r}")
        if not next_concept.prerequisites and not next_concept.related:
            lines.append("（无关联概念）")

        return "\n".join(lines)

    def weak_flow(self) -> str:
        """薄弱点 → 强化 → 验证 闭环"""
        weak = mastery_v2.get_weakest_concepts(3)
        if not weak:
            return "🎉 没有发现薄弱点！"

        lines = [
            "## 🎯 薄弱点 → 强化 → 验证",
            "",
            "### 薄弱概念",
        ]

        for r in weak:
            retention = get_retention_rate(r)
            lines.append(f"**{r.concept}** — 掌握度: {r.level:.0%}, 保持率: {retention:.0%}")
            lines.append(f"  → 强化: 试试「深度练习 {r.concept.split(' (')[0]}」")
            lines.append(f"  → 验证: 试试「开始测验 {r.concept.split(' (')[0]}」")
            lines.append("")

        lines.append("### 系统建议")
        lines.append("1. 先复习概念定义")
        lines.append("2. 再练习相关题目")
        lines.append("3. 最后验证掌握度变化")

        return "\n".join(lines)

    def review_flow(self) -> str:
        """复习 → 巩固 → 推进 闭环"""
        today = datetime.now().strftime("%Y-%m-%d")
        all_concepts = kg.get_all_concepts()
        due = [c for c in all_concepts
               if mastery_v2.get(c.name).next_review
               and mastery_v2.get(c.name).next_review <= today
               and mastery_v2.get(c.name).attempts > 0]

        if not due:
            return "🎉 今日无到期复习！试试「发现新概念」学习新内容。"

        lines = [
            "## 📚 复习 → 巩固 → 推进",
            "",
            f"### 今日到期复习 ({len(due)} 个)",
        ]

        for c in sorted(due, key=lambda x: mastery_v2.get(x.name).level):
            rec = mastery_v2.get(c.name)
            lines.append(f"- **{c.name}**（掌握度: {rec.level:.0%}, 距上次: {rec.interval} 天）")

        lines.append("")
        lines.append("### 推荐流程")
        lines.append("1️⃣ 复习：试试「复习」开始到期复习")
        lines.append("2️⃣ 巩固：查看相关笔记和题目")
        lines.append("3️⃣ 推进：掌握度提升后学习下一概念")

        return "\n".join(lines)

    def deep_flow(self, concept_name: str = "") -> str:
        """疑问 → 研究 → 理解 闭环"""
        if not concept_name:
            return "想深入哪个概念？试试「研究 容器」"

        lines = [
            f"## 🔬 疑问 → 研究 → 理解 — {concept_name}",
            "",
            "### 推荐流程",
            f"1️⃣ 研究：试试「研究 {concept_name}」",
            f"2️⃣ 可视化：试试「架构图 {concept_name}」",
            f"3️⃣ 源码分析：试试「源码分析 {concept_name}」",
            f"4️⃣ 练习：试试「深度练习 {concept_name}」",
            "5️⃣ 笔记：试试「记笔记 <你的理解>」",
            "",
            "### 学习目标",
            "- 理解概念的核心定义",
            "- 掌握源码位置和关键函数",
            "- 能解释设计模式和架构决策",
            "- 能识别和纠正常见误解",
        ]

        return "\n".join(lines)


# ============================================================
# 系统命令
# ============================================================

class SystemCommands:
    """系统管理命令"""

    @staticmethod
    def stats() -> str:
        """学习统计"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        mastered = [r for r in practiced if r.level >= 0.7]
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0
        today = datetime.now().strftime("%Y-%m-%d")
        due = [r for r in records if r.next_review and r.next_review <= today]
        total_attempts = sum(r.attempts for r in records)
        total_correct = sum(r.correct for r in records)

        # 笔记统计
        notes = nm.list_notes()
        note_count = len(notes)

        # 测验统计
        quiz_history = quiz_manager.get_history()
        quiz_count = len(quiz_history)
        avg_score = 0
        if quiz_history:
            scores = [q.get("score", 0) for q in quiz_history if q.get("score")]
            avg_score = sum(scores) / len(scores) if scores else 0

        # 记忆统计
        mem = long_term_memory.summarize()

        lines = [
            "## 📊 学习统计",
            "",
            "### 概念进度",
            f"总概念: {len(all_concepts)}",
            f"已学: {len(practiced)} ({len(practiced)/len(all_concepts)*100:.0f}%)",
            f"精通: {len(mastered)} ({len(mastered)/len(all_concepts)*100:.0f}%)",
            f"平均掌握度: {avg_level:.0%}",
            "",
            "### 练习统计",
            f"总答题: {total_attempts} 次",
            f"正确率: {total_correct/total_attempts*100:.0f}%" if total_attempts else "正确率: -",
            f"到期复习: {len(due)} 个",
            "",
            "### 测验统计",
            f"完成测验: {quiz_count} 次",
            f"平均得分: {avg_score:.0f}%" if quiz_count else "平均得分: -",
            "",
            "### 内容统计",
            f"笔记: {note_count} 条",
            f"学习天数: {mem['total_days']} 天",
            f"学习会话: {mem['total_sessions']} 次",
            "",
            "💡 试试「仪表盘」查看完整总览。",
        ]
        return "\n".join(lines)

    @staticmethod
    def export() -> str:
        """导出学习数据"""
        today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        export_dir = Path(__file__).parent.parent / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        files_exported = []

        # 1. 掌握度报告
        mastery_file = export_dir / f"mastery_{today}.md"
        all_concepts = kg.get_all_concepts()
        names = [c.name for c in all_concepts]
        content = practice_report.generate_text(names, mastery_v2)
        mastery_file.write_text(content, encoding="utf-8")
        files_exported.append(mastery_file)

        # 2. 学习路径
        path_file = export_dir / f"learning_path_{today}.md"
        path = learning_path.adapt_path({})
        path_lines = ["# 学习路径导出\n"]
        for item in path:
            path_lines.append(f"- {item['concept']} [{item['status']}] {item.get('group', '')}")
        path_file.write_text("\n".join(path_lines), encoding="utf-8")
        files_exported.append(path_file)

        # 3. 笔记导出
        notes_file = export_dir / f"notes_{today}.md"
        notes = nm.export_notes()
        notes_file.write_text(notes, encoding="utf-8")
        files_exported.append(notes_file)

        # 4. 记忆摘要
        mem_file = export_dir / f"memory_{today}.json"
        import json
        mem_file.write_text(
            json.dumps(long_term_memory.summarize(), ensure_ascii=False, indent=2),
            encoding="utf-8")
        files_exported.append(mem_file)

        lines = ["## 📦 学习数据导出\n"]
        for f in files_exported:
            lines.append(f"- ✅ 导出: `{f}`")
        lines.append("\n共导出 4 个文件。")

        return "\n".join(lines)

    @staticmethod
    def reset(dry_run: bool = True) -> str:
        """重置学习进度"""
        if dry_run:
            all_concepts = kg.get_all_concepts()
            records = [mastery_v2.get(c.name) for c in all_concepts]
            practiced = [r for r in records if r.attempts > 0]
            return (
                "## ⚠️ 重置进度预览\n"
                f"\n将重置 {len(practiced)} 个已学概念的掌握度记录。"
                "\n笔记、测验历史、记忆将保留。"
                "\n\n确定要重置吗？输入「确认重置」执行。"
            )

        # 执行重置
        all_concepts = kg.get_all_concepts()
        for c in all_concepts:
            rec = mastery_v2.get(c.name)
            rec.attempts = 0
            rec.correct = 0
            rec.level = 0.0
            rec.ef = 2.5
            rec.interval = 0
            rec.next_review = ""
            mastery_v2.records[rec.concept] = rec
        mastery_v2.save()
        return "✅ 已重置所有掌握度记录。重新开始学习吧！"


# ============================================================
# 用户体验增强
# ============================================================

class UXEngine:
    """用户体验增强"""

    @staticmethod
    def onboarding() -> str:
        """新用户引导"""
        return (
            "## 🐳 欢迎来到 Docker 源码学习系统！\n"
            "\n"
            "### 快速开始\n"
            "\n"
            "1️⃣ **了解系统**：输入「总览」查看学习总览\n"
            "2️⃣ **选择人格**：输入「人格列表」选择教学风格\n"
            "3️⃣ **开始学习**：输入「什么是容器」开始\n"
            "4️⃣ **练习巩固**：输入「快速练习」做练习\n"
            "5️⃣ **记录笔记**：输入「记笔记 <内容>」\n"
            "\n"
            "### 推荐学习路径\n"
            "\n"
            "**基础篇**：容器 → 镜像 → Docker 架构\n"
            "**核心篇**：容器运行时 → 存储驱动 → 网络模型\n"
            "**进阶篇**：镜像构建 → 安全 → 编排\n"
            "**深入篇**：源码分析 → 设计模式\n"
            "\n"
            "💡 输入「帮助」查看所有命令。"
        )

    @staticmethod
    def celebrate_milestone() -> str:
        """里程碑庆祝"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]
        practiced = [r for r in records if r.attempts > 0]
        mastered = [r for r in practiced if r.level >= 0.7]
        avg_level = sum(r.level for r in practiced) / len(practiced) if practiced else 0

        milestones = []
        if len(practiced) == len(all_concepts):
            milestones.append("🏆 **全部概念已学完！** 真正的 Docker 大师！")
        if len(mastered) >= len(all_concepts) * 0.5:
            milestones.append(f"🌟 **精通过半！** {len(mastered)}/{len(all_concepts)} 概念已精通！")
        if len(practiced) >= len(all_concepts) * 0.25:
            milestones.append(f"📚 **四分之一里程碑！** 已学 {len(practiced)}/{len(all_concepts)} 概念")
        if len(practiced) == 1:
            milestones.append("🎉 **第一个概念！** 好的开始是成功的一半！")
        if avg_level >= 0.8:
            milestones.append("🔥 **平均掌握度 80%+！** 你已经接近专家水平！")

        if milestones:
            return "\n".join(["## 🎉 里程碑！"] + milestones)
        return ""

    @staticmethod
    def good_morning() -> str:
        """每日问候"""
        today = datetime.now()
        weekday = today.weekday()
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_name = day_names[weekday]

        all_concepts = kg.get_all_concepts()
        due = [c for c in all_concepts
               if mastery_v2.get(c.name).next_review
               and mastery_v2.get(c.name).next_review <= today.strftime("%Y-%m-%d")
               and mastery_v2.get(c.name).attempts > 0]

        messages = [
            f"早安！今天是 {day_name}，又是学习 Docker 的好日子！",
            f"下午好！{day_name} 的学习时间到了！",
            f"晚上好！{day_name} 的 Docker 学习时间！",
        ]

        # 根据时间选择问候
        hour = today.hour
        if hour < 12:
            msg = messages[0]
        elif hour < 18:
            msg = messages[1]
        else:
            msg = messages[2]

        if due:
            msg += f"\n📌 今天有 {len(due)} 个概念到期复习。"

        # 里程碑
        milestone = UXEngine.celebrate_milestone()
        if milestone:
            msg += f"\n{milestone}"

        # 推荐
        next_rec = learning_path.recommend_next({})
        msg += f"\n💡 推荐: {next_rec['type']} {next_rec['concept']}"

        return msg


# ============================================================
# 全局实例
# ============================================================

dashboard = DashboardEngine()
flow_engine = FlowEngine()
system_commands = SystemCommands()
ux = UXEngine()


def _stage_name(avg_level: float) -> str:
    if avg_level < 0.3:
        return "🐣 初学者"
    elif avg_level < 0.6:
        return "🌱 进阶者"
    elif avg_level < 0.8:
        return "🌳 熟练者"
    else:
        return "🏆 专家"