# Docker 源码学习系统 — 可视化引擎

"""
Mermaid 图生成引擎。
从知识图谱和概念数据自动生成 8 种可视化图表。
"""

from datetime import datetime
from .knowledge_graph import kg, Concept
from .mastery_engine import mastery_v2, get_retention_rate


class MermaidGenerator:
    """Mermaid 图生成器基类"""

    @staticmethod
    def wrap(title: str, diagram_type: str, body: str) -> str:
        return (
            f"```mermaid\n"
            f"%%{{init: {{'theme': 'base', 'themeVariables': {{'primaryBorderColor': '#333'}}}}}}%%\n"
            f"{diagram_type}\n"
            f"    title {title}\n"
            f"{body}\n"
            f"```\n"
        )


# ============================================================
# 1. 架构图 — 组件层次关系
# ============================================================

class ArchitectureGenerator(MermaidGenerator):
    """生成 Docker 架构图（flowchart）"""

    @staticmethod
    def generate(concept_name: str = "") -> str:
        if concept_name:
            c = kg.get_concept(concept_name)
            if not c:
                matches = kg.search_concepts(concept_name)
                if matches:
                    c = matches[0]
            if c:
                return ArchitectureGenerator._generate_single(c)
        return ArchitectureGenerator._generate_overview()

    @staticmethod
    def _generate_overview() -> str:
        """生成 Docker 整体架构图"""
        lines = [
            "graph TB",
            "    subgraph 用户层",
            "        CLI[Docker CLI]",
            "        API[REST API]",
            "    end",
            "    subgraph 管理面",
            "        D[dockerd]",
            "        B[Builder]",
            "        N[Network]",
            "        V[Volume]",
            "    end",
            "    subgraph 运行时层",
            "        CD[containerd]",
            "        SH[shim]",
            "        RC[runc]",
            "    end",
            "    subgraph 内核层",
            "        CG[cgroups]",
            "        NS[namespaces]",
            "        UF[UnionFS]",
            "    end",
            "    CLI --> API",
            "    API --> D",
            "    D --> B",
            "    D --> N",
            "    D --> V",
            "    D --> CD",
            "    CD --> SH",
            "    SH --> RC",
            "    RC --> CG",
            "    RC --> NS",
            "    RC --> UF",
        ]
        return MermaidGenerator.wrap("Docker 整体架构", "graph TB", "\n".join(lines))

    @staticmethod
    def _generate_single(concept: Concept) -> str:
        """生成单个概念的架构图"""
        name = concept.name
        lines = ["graph LR"]

        # 前置知识
        prereqs = kg.get_prerequisites(name)
        for p in prereqs:
            lines.append(f"    {p.name.replace(' ', '_')}[{p.name}] --> {name.replace(' ', '_')}[{name}]")

        # 关联概念
        related = kg.get_related_concepts(name)
        for r in related:
            lines.append(f"    {name.replace(' ', '_')}[{name}] --> {r.name.replace(' ', '_')}[{r.name}]")

        # 掌握度标注
        record = mastery_v2.get(name)
        lines.append(f"    style {name.replace(' ', '_')} fill:#e1f5fe,stroke:#0288d1")
        for p in prereqs:
            pr = mastery_v2.get(p.name)
            if pr.level >= 0.5:
                lines.append(f"    style {p.name.replace(' ', '_')} fill:#e8f5e9,stroke:#388e3c")
            elif pr.attempts > 0:
                lines.append(f"    style {p.name.replace(' ', '_')} fill:#fff3e0,stroke:#f57c00")

        return MermaidGenerator.wrap(f"{name} 架构关系", "graph LR", "\n".join(lines))


# ============================================================
# 2. 调用链 / 概念流程图
# ============================================================

class CallChainGenerator(MermaidGenerator):
    """生成概念调用链/流程图"""

    @staticmethod
    def generate(concept_name: str = "") -> str:
        if not concept_name:
            concept_name = "容器创建流程"
        return CallChainGenerator._generate_flow(concept_name)

    @staticmethod
    def _generate_flow(concept_name: str) -> str:
        """生成流程图的序列图"""
        # 容器创建流程
        if "创建" in concept_name or "容器" in concept_name:
            lines = [
                "sequenceDiagram",
                "    participant User as 用户",
                "    participant API as Docker API",
                "    participant D as dockerd",
                "    participant CD as containerd",
                "    participant SH as shim",
                "    participant RC as runc",
                "    participant OS as 内核",
                "",
                "    User->>API: POST /containers/create",
                "    API->>D: 解析请求",
                "    D->>D: verifyContainerSettings",
                "    D->>D: newContainer(分配ID)",
                "    D->>D: setupContainerNetwork",
                "    D->>D: setupContainerMounts",
                "    D->>CD: CreateContainer",
                "    CD->>SH: 启动 shim",
                "    SH->>RC: runc create",
                "    RC->>OS: clone(CLONE_NEWNS|...)",
                "    RC->>OS: cgroup 设置",
                "    RC-->>SH: 容器进程运行中",
                "    SH-->>CD: 状态上报",
                "    CD-->>D: 创建成功",
                "    D-->>API: 返回容器ID",
                "    API-->>User: 201 Created",
            ]
            return MermaidGenerator.wrap(
                "容器创建流程 (时序图)", "sequenceDiagram", "\n".join(lines))

        # 通用概念流程
        c = kg.get_concept(concept_name) or (kg.search_concepts(concept_name) or [None])[0]
        if not c:
            return "没有找到相关概念。"

        prereqs = kg.get_prerequisites(c.name)
        related = kg.get_related_concepts(c.name)

        lines = ["graph LR"]
        for p in prereqs:
            lines.append(f"    {p.name.replace(' ', '_')}[{p.name}] -->|输入| {c.name.replace(' ', '_')}[{c.name}]")
        for r in related:
            lines.append(f"    {c.name.replace(' ', '_')}[{c.name}] -->|输出| {r.name.replace(' ', '_')}[{r.name}]")

        return MermaidGenerator.wrap(f"{c.name} 概念流程", "graph LR", "\n".join(lines))


# ============================================================
# 3. 学习路径图
# ============================================================

class LearningPathGenerator(MermaidGenerator):
    """生成学习路径图"""

    @staticmethod
    def generate(focus: str = "") -> str:
        if focus:
            return LearningPathGenerator._generate_path_for(focus)
        return LearningPathGenerator._generate_full_path()

    @staticmethod
    def _generate_full_path() -> str:
        """生成完整学习路径"""
        # 按难度分组
        all_concepts = kg.get_all_concepts()
        by_difficulty = sorted(all_concepts, key=lambda c: c.difficulty)

        lines = [
            "graph TD",
            "    classDef easy fill:#e8f5e9,stroke:#388e3c",
            "    classDef medium fill:#fff3e0,stroke:#f57c00",
            "    classDef hard fill:#fce4ec,stroke:#d32f2f",
            "",
            "    subgraph 第一阶段: 基础",
        ]

        easy = [c for c in by_difficulty if c.difficulty < 0.4]
        for i, c in enumerate(easy):
            lines.append(f"        E{i}[{c.name}]")
        lines.append("    end")
        lines.append("")
        lines.append("    subgraph 第二阶段: 进阶")

        medium = [c for c in by_difficulty if 0.4 <= c.difficulty < 0.7]
        for i, c in enumerate(medium):
            lines.append(f"        M{i}[{c.name}]")
        lines.append("    end")
        lines.append("")
        lines.append("    subgraph 第三阶段: 深入")

        hard = [c for c in by_difficulty if c.difficulty >= 0.7]
        for i, c in enumerate(hard):
            lines.append(f"        H{i}[{c.name}]")
        lines.append("    end")

        # 连接关系
        if easy:
            lines.append(f"    E0 --> M0")
        if medium:
            lines.append(f"    M0 --> H0")

        # 标注掌握度
        for label, group in [("E", easy), ("M", medium), ("H", hard)]:
            for i, c in enumerate(group):
                rec = mastery_v2.get(c.name)
                if rec.level >= 0.8:
                    lines.append(f"    class {label}{i} easy;")
                elif rec.level >= 0.5:
                    lines.append(f"    class {label}{i} medium;")
                elif rec.attempts > 0:
                    pass  # 默认

        return MermaidGenerator.wrap("Docker 源码学习路径", "graph TD", "\n".join(lines))

    @staticmethod
    def _generate_path_for(focus: str) -> str:
        """生成指定概念的学习路径"""
        c = kg.get_concept(focus)
        if not c:
            matches = kg.search_concepts(focus)
            if matches:
                c = matches[0]
            else:
                return f"没有找到概念「{focus}」"

        lines = ["graph LR"]
        lines.append(f"    classDef current fill:#e1f5fe,stroke:#0288d1")
        lines.append(f"    classDef ready fill:#e8f5e9,stroke:#388e3c")
        lines.append(f"    classDef weak fill:#fce4ec,stroke:#d32f2f")

        prereqs = kg.get_prerequisites(c.name)
        related = kg.get_related_concepts(c.name)

        for p in prereqs:
            rec = mastery_v2.get(p.name)
            label = f"{p.name} ({rec.level:.0%})"
            el_id = p.name.replace(" ", "_")
            lines.append(f"    {el_id}[{label}]")
            lines.append(f"    {el_id} --> {c.name.replace(' ', '_')}[{c.name}]")
            cls = "ready" if rec.level >= 0.5 else "weak"
            lines.append(f"    class {el_id} {cls}")

        for r in related:
            rec = mastery_v2.get(r.name)
            label = f"{r.name} ({rec.level:.0%})"
            el_id = r.name.replace(" ", "_")
            lines.append(f"    {el_id}[{label}]")
            lines.append(f"    {c.name.replace(' ', '_')}[{c.name}] --> {el_id}")

        lines.append(f"    class {c.name.replace(' ', '_')} current")

        return MermaidGenerator.wrap(f"「{c.name}」学习路径", "graph LR", "\n".join(lines))


# ============================================================
# 4. 知识图谱总览
# ============================================================

class KnowledgeGraphGenerator(MermaidGenerator):
    """生成知识图谱总览图"""

    @staticmethod
    def generate() -> str:
        lines = [
            "graph TD",
            "    classDef core fill:#e1f5fe,stroke:#0288d1,stroke-width:2px",
            "    classDef runtime fill:#e8f5e9,stroke:#388e3c",
            "    classDef storage fill:#fff3e0,stroke:#f57c00",
            "    classDef network fill:#f3e5f5,stroke:#7b1fa2",
            "    classDef build fill:#fce4ec,stroke:#c62828",
            "",
        ]

        all_concepts = kg.get_all_concepts()
        # 核心概念
        core = [c for c in all_concepts if c.difficulty < 0.4]
        runtime = [c for c in all_concepts if "运行" in c.name or "runc" in c.name.lower() or "containerd" in c.name.lower() or "shim" in c.name.lower() or "dockerd" in c.name.lower()]
        storage = [c for c in all_concepts if "存储" in c.name or "overlay" in c.name.lower() or "aufs" in c.name.lower()]
        network = [c for c in all_concepts if "网络" in c.name]
        build = [c for c in all_concepts if "构建" in c.name or "builder" in c.name.lower() or "镜像" in c.name or "层" in c.name]

        groups = {
            "核心概念": (core, "core"),
            "运行时": (runtime, "runtime"),
            "存储": (storage, "storage"),
            "网络": (network, "network"),
            "构建": (build, "build"),
        }

        node_ids = {}
        for group_name, (group_list, css_class) in groups.items():
            if group_list:
                lines.append(f"    subgraph {group_name}")
                for c in group_list:
                    nid = c.name.replace(" ", "_").replace("(", "").replace(")", "")
                    node_ids[c.name] = nid
                    lines.append(f"        {nid}[{c.name.split(' (')[0]}]")
                    lines.append(f"        class {nid} {css_class}")
                lines.append("    end")
                lines.append("")

        # 添加关系
        for c in all_concepts:
            src = node_ids.get(c.name)
            if not src:
                continue
            for r_name in c.related:
                dst = node_ids.get(r_name)
                if dst:
                    lines.append(f"    {src} --> {dst}")

        return MermaidGenerator.wrap("Docker 知识图谱总览", "graph TD", "\n".join(lines))


# ============================================================
# 5. 数据流图
# ============================================================

class DataFlowGenerator(MermaidGenerator):
    """生成数据流图"""

    @staticmethod
    def generate(concept_name: str = "") -> str:
        if concept_name:
            c = kg.get_concept(concept_name)
            if not c:
                matches = kg.search_concepts(concept_name)
                if matches:
                    c = matches[0]
            if c:
                return DataFlowGenerator._generate_for_concept(c)

        # 默认：镜像构建数据流
        return DataFlowGenerator._generate_build_flow()

    @staticmethod
    def _generate_build_flow() -> str:
        lines = [
            "graph LR",
            "    DF[Dockerfile] -->|读取| Builder[Builder]",
            "    Builder -->|解析| Stages[构建阶段]",
            "    Stages -->|1. FROM| Base[基础镜像层]",
            "    Stages -->|2. COPY| Src[源码层]",
            "    Stages -->|3. RUN| Deps[依赖层]",
            "    Stages -->|4. COPY| App[应用层]",
            "    Stages -->|5. CMD| Cmd[启动命令层]",
            "    Base -->|缓存命中| Cache[层缓存]",
            "    Src -->|缓存失效| Rebuild[重新构建]",
            "    Cache -->|复用| Image[最终镜像]",
            "    Rebuild --> Image",
            "",
            "    style DF fill:#e8f5e9,stroke:#388e3c",
            "    style Image fill:#e1f5fe,stroke:#0288d1",
            "    style Cache fill:#fff3e0,stroke:#f57c00",
        ]
        return MermaidGenerator.wrap("镜像构建数据流", "graph LR", "\n".join(lines))

    @staticmethod
    def _generate_for_concept(concept: Concept) -> str:
        name = concept.name
        prereqs = kg.get_prerequisites(name)
        related = kg.get_related_concepts(name)

        lines = ["flowchart LR"]
        lines.append(f"    {name.replace(' ', '_')}[{name}]")

        for p in prereqs:
            pid = p.name.replace(" ", "_")
            lines.append(f"    {pid}[{p.name}] -->|输入| {name.replace(' ', '_')}")
        for r in related:
            rid = r.name.replace(" ", "_")
            lines.append(f"    {name.replace(' ', '_')} -->|输出| {rid}[{r.name}]")

        return MermaidGenerator.wrap(f"{name} 数据流", "flowchart LR", "\n".join(lines))


# ============================================================
# 6. 学习进度可视化
# ============================================================

class StudyProgressGenerator(MermaidGenerator):
    """生成学习进度可视化"""

    @staticmethod
    def generate() -> str:
        """生成甘特图显示学习进度"""
        all_concepts = kg.get_all_concepts()
        records = [mastery_v2.get(c.name) for c in all_concepts]

        lines = [
            "gantt",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat  %m/%d",
            "",
            "    section 精通 (≥80%)",
        ]

        mastered = []
        in_progress = []
        weak = []
        untouched = []

        for c, r in zip(all_concepts, records):
            if r.level >= 0.8:
                mastered.append((c, r))
            elif r.level >= 0.5:
                in_progress.append((c, r))
            elif r.attempts > 0:
                weak.append((c, r))
            else:
                untouched.append((c, r))

        for c, r in mastered:
            days = max(1, r.interval or 1)
            start = r.last_practiced or datetime.now().strftime("%Y-%m-%d")
            lines.append(f"    {c.name.split(' (')[0]} :{start}, {days}d")

        if not mastered:
            lines.append("    (暂无) :{}, 1d".format(datetime.now().strftime("%Y-%m-%d")))

        lines.append("")
        lines.append("    section 进行中 (50-79%)")
        for c, r in in_progress:
            days = max(1, r.interval or 1)
            start = r.last_practiced or datetime.now().strftime("%Y-%m-%d")
            lines.append(f"    {c.name.split(' (')[0]} :{start}, {days}d")

        if not in_progress:
            lines.append("    (暂无) :{}, 1d".format(datetime.now().strftime("%Y-%m-%d")))

        lines.append("")
        lines.append("    section 需加强 (<50%)")
        for c, r in weak:
            days = max(1, (r.interval or 1))
            start = r.last_practiced or datetime.now().strftime("%Y-%m-%d")
            lines.append(f"    {c.name.split(' (')[0]} :{start}, {days}d")

        for c, r in untouched:
            lines.append(f"    {c.name.split(' (')[0]} (未学) :{datetime.now().strftime('%Y-%m-%d')}, 1d")

        return MermaidGenerator.wrap("学习进度甘特图", "gantt", "\n".join(lines))


# ============================================================
# 7. 类图 / 结构体图
# ============================================================

class ClassDiagramGenerator(MermaidGenerator):
    """生成类图/结构体关系图"""

    @staticmethod
    def generate(concept_name: str = "") -> str:
        if concept_name:
            c = kg.get_concept(concept_name)
            if not c:
                matches = kg.search_concepts(concept_name)
                if matches:
                    c = matches[0]
            if c:
                return ClassDiagramGenerator._generate_for_concept(c)
        return ClassDiagramGenerator._generate_core_classes()

    @staticmethod
    def _generate_core_classes() -> str:
        lines = [
            "classDiagram",
            "    class Container {",
            "        +string ID",
            "        +string Name",
            "        +Config Config",
            "        +State State",
            "        +ImageID ImageID",
            "        +Monitor Monitor",
            "        +HostConfig HostConfig",
            "        +Store Store",
            "        +create()",
            "        +start()",
            "        +stop()",
            "    }",
            "    class State {",
            "        +bool Running",
            "        +bool Paused",
            "        +bool Restarting",
            "        +int* ExitCode",
            "        +time StartedAt",
            "        +time FinishedAt",
            "    }",
            "    class Daemon {",
            "        +containers containerStore",
            "        +imageService ImageService",
            "        +netController NetworkController",
            "        +volService VolumeService",
            "        +start() error",
            "        +containerCreate()",
            "    }",
            "    class Config {",
            "        +string Hostname",
            "        +string Domainname",
            "        +string User",
            "        +Env Env",
            "        +Cmd Cmd",
            "        +Entrypoint Entrypoint",
            "    }",
            "    Container --> State : 状态管理",
            "    Container --> Config : 配置",
            "    Container --> Daemon : 管理",
            "    Daemon --> Container : 创建/管理",
        ]
        return MermaidGenerator.wrap("核心结构体关系", "classDiagram", "\n".join(lines))

    @staticmethod
    def _generate_for_concept(concept: Concept) -> str:
        lines = ["classDiagram"]
        name = concept.name.split(" (")[0]
        lines.append(f"    class {name.replace(' ', '_')} {{")

        if concept.definition:
            lines.append(f"        +string 定义")
        prereqs = kg.get_prerequisites(concept.name)
        related = kg.get_related_concepts(concept.name)
        for p in prereqs:
            lines.append(f"        +{p.name.split(' (')[0].replace(' ', '_')} 前置")
        for r in related:
            lines.append(f"        +{r.name.split(' (')[0].replace(' ', '_')} 关联")
        if concept.code_ref:
            lines.append(f"        +string 源码路径")
        lines.append("    }")

        for p in prereqs:
            pn = p.name.split(" (")[0].replace(" ", "_")
            lines.append(f"    {pn} --> {name.replace(' ', '_')}")
        for r in related:
            rn = r.name.split(" (")[0].replace(" ", "_")
            lines.append(f"    {name.replace(' ', '_')} --> {rn}")

        return MermaidGenerator.wrap(f"{name} 结构", "classDiagram", "\n".join(lines))


# ============================================================
# 可视化引擎入口
# ============================================================

class VisualizationEngine:
    """可视化引擎总入口"""

    @staticmethod
    def generate_architecture(concept: str = "") -> str:
        return ArchitectureGenerator.generate(concept)

    @staticmethod
    def generate_call_chain(concept: str = "") -> str:
        return CallChainGenerator.generate(concept)

    @staticmethod
    def generate_learning_path(concept: str = "") -> str:
        return LearningPathGenerator.generate(concept)

    @staticmethod
    def generate_knowledge_graph() -> str:
        return KnowledgeGraphGenerator.generate()

    @staticmethod
    def generate_data_flow(concept: str = "") -> str:
        return DataFlowGenerator.generate(concept)

    @staticmethod
    def generate_study_progress() -> str:
        return StudyProgressGenerator.generate()

    @staticmethod
    def generate_class_diagram(concept: str = "") -> str:
        return ClassDiagramGenerator.generate(concept)

    @staticmethod
    def list_diagram_types() -> list[dict]:
        return [
            {"name": "architecture", "desc": "Docker 架构层次图", "aliases": ["架构", "架构图"]},
            {"name": "call_chain", "desc": "概念调用链/时序图", "aliases": ["调用链", "时序图", "流程"]},
            {"name": "learning_path", "desc": "学习路径推荐图", "aliases": ["学习路径", "学习路线"]},
            {"name": "knowledge_graph", "desc": "知识图谱总览图", "aliases": ["知识图谱", "图谱总览"]},
            {"name": "data_flow", "desc": "数据流图", "aliases": ["数据流", "数据流向"]},
            {"name": "study_progress", "desc": "学习进度甘特图", "aliases": ["进度图", "学习进度"]},
            {"name": "class_diagram", "desc": "结构体/类关系图", "aliases": ["类图", "结构体图"]},
            {"name": "heatmap", "desc": "掌握度热力图", "aliases": ["热力图", "掌握度图"]},
        ]


viz = VisualizationEngine()