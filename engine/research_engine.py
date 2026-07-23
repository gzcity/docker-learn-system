# Docker 源码学习系统 — 深度研究引擎

"""
自动生成 Docker 源码概念的结构化研究报告。
基于知识图谱和代码引用，无需实际 Go 源码即可生成深度分析。
支持扩展为真实 Go AST 解析。
"""

from datetime import datetime
from typing import Optional

from .knowledge_graph import kg, Concept
from .mastery_engine import mastery_v2, get_retention_rate


# ============================================================
# 研究报告生成器
# ============================================================

class ResearchEngine:
    """深度研究引擎"""

    @staticmethod
    def generate_report(concept_name: str) -> str:
        """生成概念的研究报告"""
        c = kg.get_concept(concept_name)
        if not c:
            matches = kg.search_concepts(concept_name)
            if matches:
                c = matches[0]
            else:
                return f"没有找到概念「{concept_name}」"

        record = mastery_v2.get(c.name)
        retention = get_retention_rate(record)

        lines = [
            f"# 🔬 深度研究报告: {c.name}",
            f"",
            f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            f"",
            f"---",
            f"",
            f"## 1. 概念概述",
            f"",
            f"**定义**: {c.definition}",
            f"",
        ]

        if c.code_ref:
            lines.append(f"**核心源码**: `{c.code_ref}`")
            lines.append("")

        lines.append(f"**难度等级**: {'⭐' * int(c.difficulty * 5)} ({c.difficulty:.1f})")
        lines.append(f"")
        lines.append(f"**你的掌握度**: {record.level:.0%}")
        lines.append(f"**记忆保留率**: {retention:.0%}")
        lines.append("")

        # 2. 架构位置
        lines.append("## 2. 架构位置")
        lines.append("")
        prereqs = kg.get_prerequisites(c.name)
        related = kg.get_related_concepts(c.name)

        lines.append("```")
        lines.append("上游依赖 (前置知识):")
        if prereqs:
            for p in prereqs:
                pr = mastery_v2.get(p.name)
                lines.append(f"  {p.name} (掌握度: {pr.level:.0%})")
        else:
            lines.append("  (无)")
        lines.append("")
        lines.append("下游关联:")
        if related:
            for r in related:
                rr = mastery_v2.get(r.name)
                lines.append(f"  {r.name} (掌握度: {rr.level:.0%})")
        else:
            lines.append("  (无)")
        lines.append("```")
        lines.append("")

        # 3. 源码分析
        lines.append("## 3. 源码分析")
        lines.append("")
        if c.code_ref:
            code_path = c.code_ref
            lines.append(f"### 3.1 关键源码路径")
            lines.append("")
            lines.append(f"**入口**: `{code_path}`")
            lines.append("")

            # 生成源码位置分析
            path_parts = code_path.split("/")
            if len(path_parts) >= 2:
                pkg = path_parts[0]
                lines.append(f"**包**: `{pkg}`")
                lines.append("")
                lines.append(f"在 Docker 源码中，{pkg}/ 目录主要负责：")
                lines.append("")
                if pkg == "container":
                    lines.append("- 容器对象的定义和管理")
                    lines.append("- 容器生命周期状态机")
                    lines.append("- 容器元数据持久化")
                elif pkg == "daemon":
                    lines.append("- 守护进程核心逻辑")
                    lines.append("- 容器创建/启动/停止的协调")
                    lines.append("- 网络、存储、镜像的集成")
                elif "runtime" in pkg:
                    lines.append("- 容器运行时接口定义")
                    lines.append("- 与 containerd/runc 的交互")
                else:
                    lines.append(f"- {c.name} 的核心实现")
                    lines.append("- 相关功能的协调和调度")
                lines.append("")

        # 4. 设计模式
        lines.append("## 4. 设计模式与分析")
        lines.append("")
        design_insights = ResearchEngine._get_design_insights(c.name)
        lines.append(design_insights)
        lines.append("")

        # 5. 常见误解
        if c.misconceptions:
            lines.append("## 5. 常见误解")
            lines.append("")
            for i, mc in enumerate(c.misconceptions, 1):
                lines.append(f"### 5.{i} 误解: {mc['pattern']}")
                lines.append("")
                lines.append(f"**纠正**: {mc['correction']}")
                lines.append("")
                # 检查用户是否曾经犯过这个错误
                for mc_record in record.misconceptions_corrected:
                    if mc_record["pattern"] == mc["pattern"]:
                        lines.append(f"*⚠️ 你曾犯过这个误解 ({mc_record['corrected_at']})，已纠正*")
                        lines.append("")
                lines.append("---")
                lines.append("")

        # 6. 学习建议
        lines.append("## 6. 学习建议")
        lines.append("")
        lines.append(ResearchEngine._get_learning_advice(c, record, retention))
        lines.append("")

        # 7. 关联知识
        lines.append("## 7. 关联知识")
        lines.append("")
        lines.append("### 前置概念 (应先掌握)")
        lines.append("")
        if prereqs:
            for p in prereqs:
                pr = mastery_v2.get(p.name)
                status = "✅" if pr.level >= 0.5 else "⚠️" if pr.attempts > 0 else "⬜"
                lines.append(f"- {status} **{p.name}** — {p.definition[:60]}...")
        else:
            lines.append("- (无)")
        lines.append("")
        lines.append("### 后续概念 (可深入)")
        if related:
            for r in related:
                status = "✅" if mastery_v2.get(r.name).level >= 0.5 else "⬜"
                lines.append(f"- {status} **{r.name}** — {r.definition[:60]}...")
        else:
            lines.append("- (无)")

        return "\n".join(lines)

    @staticmethod
    def _get_design_insights(concept_name: str) -> str:
        """获取设计模式分析"""
        insights = {
            "容器": (
                "Docker 容器的设计体现了「组合优于继承」的原则。\n\n"
                "**关键设计决策**:\n"
                "- 容器 = cgroups + namespaces + rootfs 的组合\n"
                "- 不创建完整虚拟机，而是复用宿主机内核\n"
                "- 通过 `clone()` 系统调用创建隔离进程\n\n"
                "**为什么这样设计?**\n"
                "- 性能: 避免硬件虚拟化开销，接近原生性能\n"
                "- 密度: 一台机器可运行数百个容器\n"
                "- 启动速度: 秒级启动 (vs 分钟级 VM)"
            ),
            "镜像": (
                "Docker 镜像采用「分层 + 写时复制」设计。\n\n"
                "**关键设计决策**:\n"
                "- 每一层是只读的，容器运行时在顶层加可写层\n"
                "- 层间通过 UnionFS 合并为一个文件系统视图\n"
                "- 层可被多个镜像共享，节省存储\n\n"
                "**为什么这样设计?**\n"
                "- 构建缓存: 未变化层可复用\n"
                "- 镜像推送/拉取: 只传输差分层\n"
                "- 存储效率: 100 个基于 ubuntu 的镜像只存一份 ubuntu 层"
            ),
            "容器运行时": (
                "Docker 运行时采用「分层抽象」设计模式。\n\n"
                "**架构层次**:\n"
                "- 高层: dockerd (管理面, API, 用户体验)\n"
                "- 中层: containerd (标准容器运行时接口, CNCF 项目)\n"
                "- 底层: runc (OCI 运行时规范实现)\n\n"
                "**为什么这样设计?**\n"
                "- 关注点分离: 每层只做一件事\n"
                "- 标准接口: OCI 规范使 runc 可被替换\n"
                "- 生态系统: Kubernetes 可直接对接 containerd"
            ),
            "容器创建流程": (
                "容器创建采用「链式调用 + 资源回滚」模式。\n\n"
                "**关键流程**:\n"
                "1. 参数验证 → 2. 容器对象创建 → 3. 网络设置 → 4. 挂载设置\n"
                "5. 调用 containerd → 6. shim 启动 → 7. runc 创建进程\n\n"
                "**设计要点**:\n"
                "- 创建和启动分离: containerCreate 只创建, start 才运行\n"
                "- 资源回滚: 如果第 4 步失败, 需回滚第 3 步的网络设置\n"
                "- 异步状态管理: 通过 shim 持续监控容器状态"
            ),
        }

        for key, text in insights.items():
            if key in concept_name:
                return text

        # 默认分析
        return (
            f"「{concept_name}」在 Docker 架构中扮演着重要角色。\n\n"
            f"**设计分析**:\n"
            f"- 遵循 Unix 哲学「做一件事并做好」\n"
            f"- 通过接口抽象实现组件解耦\n"
            f"- 支持配置化扩展 (插件机制)\n\n"
            f"**建议**: 深入学习相关源码，理解其设计意图。"
        )

    @staticmethod
    def _get_learning_advice(concept: Concept, record, retention: float) -> str:
        """获取学习建议"""
        advice = []

        if record.attempts == 0:
            advice.append("🔴 **尚未开始学习**")
            advice.append("- 建议先阅读概念定义，理解核心作用")
            advice.append("- 查看关联前置知识，确保基础扎实")
            advice.append("- 可以试试「出题」来检验初步理解")
        elif retention < 0.3:
            advice.append("🔴 **记忆率较低，需紧急复习**")
            advice.append(f"- 上次练习: {record.last_practiced}")
            advice.append(f"- 建议立即复习，试试「复习 {concept.name}」")
            advice.append(f"- 或「出题」来检验理解")
        elif record.level < 0.5:
            advice.append("🟡 **需要更多练习**")
            advice.append(f"- 当前掌握度: {record.level:.0%}")
            advice.append(f"- 建议「深度练习 {concept.name}」")
            advice.append(f"- 查看关联源码 `{concept.code_ref}`" if concept.code_ref else "")
        elif record.level < 0.8:
            advice.append("🟢 **基础扎实，可以深入**")
            advice.append(f"- 当前掌握度: {record.level:.0%}")
            advice.append(f"- 建议阅读源码深入理解")
            advice.append(f"- 或探索关联概念拓展知识面")
        else:
            advice.append("🌟 **掌握良好！**")
            advice.append(f"- 当前掌握度: {record.level:.0%}")
            advice.append(f"- 建议教导他人，巩固理解")
            advice.append(f"- 或深入研究实现细节和源码")

        return "\n".join(advice)

    @staticmethod
    def generate_source_analysis(concept_name: str) -> str:
        """生成源码分析报告"""
        c = kg.get_concept(concept_name)
        if not c:
            matches = kg.search_concepts(concept_name)
            if matches:
                c = matches[0]
            else:
                return f"没有找到概念「{concept_name}」"

        if not c.code_ref:
            return f"「{c.name}」没有关联的源码路径。"

        lines = [
            f"## 📂 源码分析: {c.code_ref}",
            f"",
            f"**概念**: {c.name}",
            f"**定义**: {c.definition}",
            f"",
            f"### 文件路径分析",
            f"",
            f"```",
            f"docker/",
        ]

        path_parts = c.code_ref.split("/")
        current = "docker/"
        for part in path_parts:
            current += part
            lines.append(f"├── {part}")
            current += "/"

        lines.append("```")
        lines.append("")

        # 关键函数分析
        lines.append("### 关键函数/结构体")
        lines.append("")
        if "container" in c.code_ref:
            lines.append("| 函数/结构体 | 作用 |")
            lines.append("|------------|------|")
            lines.append("| `Container` | 容器对象，包含 ID、Config、State 等字段 |")
            lines.append("| `NewContainer` | 创建新容器对象，分配 ID |")
            lines.append("| `containerCreate` | 完整容器创建流程（参数验证→对象创建→网络→挂载） |")
            lines.append("| `State` | 容器状态机（Running/Paused/Restarting/ExitCode） |")
        elif "daemon" in c.code_ref:
            lines.append("| 函数/结构体 | 作用 |")
            lines.append("|------------|------|")
            lines.append("| `Daemon` | 守护进程核心对象，管理所有容器 |")
            lines.append("| `start()` | 初始化流程：恢复容器→网络→监控→API |")
            lines.append("| `containerCreate` | 容器创建入口 |")
        elif "runtime" in c.code_ref:
            lines.append("| 函数/结构体 | 作用 |")
            lines.append("|------------|------|")
            lines.append("| `Runtime` | 运行时接口定义 |")
            lines.append("| `Create` | 创建容器运行时实例 |")
            lines.append("| `Start` | 启动容器进程 |")
        else:
            lines.append(f"| `{c.name.split(' (')[0]}` | 核心实现 |")

        lines.append("")
        lines.append("### 设计要点")
        lines.append("")
        lines.append("1. **接口抽象**: 通过接口定义行为，实现可替换")
        lines.append("2. **错误处理**: Go 的多返回值模式，错误检查")
        lines.append("3. **异步监控**: 通过 goroutine 和 channel 实现")
        lines.append("4. **资源管理**: defer 确保资源释放")

        return "\n".join(lines)


# ============================================================
# 全局实例
# ============================================================

research = ResearchEngine()