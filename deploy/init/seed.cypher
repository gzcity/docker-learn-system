// ============================================================
// 知识图谱初始化脚本
// 首次启动时自动执行，创建概念节点和关系
// ============================================================

// 清空已有数据（仅首次初始化）
// MATCH (n) DETACH DELETE n;

// ============================================================
// 基础概念层
// ============================================================

// 容器
CREATE (c:Concept:LearningNode {
    id: "container",
    name: "容器",
    definition: "一个轻量级、可移植的运行环境，包含应用及其依赖。Docker 的核心抽象。",
    difficulty: 0.2,
    code_ref: "container/container.go",
    created_at: datetime()
})

// 镜像
CREATE (i:Concept:LearningNode {
    id: "image",
    name: "镜像",
    definition: "一个只读模板，包含创建容器的指令。基于 UnionFS 的分层结构。",
    difficulty: 0.2,
    code_ref: "image/image.go",
    created_at: datetime()
})

// 层
CREATE (l:Concept:LearningNode {
    id: "layer",
    name: "层",
    definition: "镜像的增量修改单元。每个层是只读的，多个层叠加形成完整文件系统。",
    difficulty: 0.3,
    code_ref: "layer/layer.go",
    created_at: datetime()
})

// 容器运行时
CREATE (r:Concept:LearningNode {
    id: "container-runtime",
    name: "容器运行时",
    definition: "负责管理容器生命周期的软件组件。Docker 使用 containerd + runc 的架构。",
    difficulty: 0.5,
    code_ref: "daemon/, containerd, runc",
    created_at: datetime()
})

// 关系：容器 → 镜像
CREATE (c)-[:RELATES_TO {weight: 0.9}]->(i)
// 关系：容器 → 容器运行时
CREATE (c)-[:RELATES_TO {weight: 0.8}]->(r)
// 关系：镜像 → 层
CREATE (i)-[:COMPOSED_OF]->(l)

// ============================================================
// 核心架构层
// ============================================================

CREATE (d:Concept:LearningNode {
    id: "dockerd",
    name: "dockerd",
    definition: "Docker 的后台服务进程，处理 API 请求，管理容器生命周期。",
    difficulty: 0.5,
    code_ref: "cmd/dockerd/dockerd.go",
    created_at: datetime()
})

CREATE (ct:Concept:LearningNode {
    id: "containerd",
    name: "containerd",
    definition: "行业标准的容器运行时，管理容器的完整生命周期。",
    difficulty: 0.6,
    code_ref: "containerd/containerd",
    created_at: datetime()
})

CREATE (rc:Concept:LearningNode {
    id: "runc",
    name: "runc",
    definition: "OCI 运行时规范实现，负责实际创建和运行容器进程。",
    difficulty: 0.7,
    code_ref: "opencontainers/runc",
    created_at: datetime()
})

CREATE (sh:Concept:LearningNode {
    id: "shim",
    name: "shim",
    definition: "containerd 和 runc 之间的中间层，允许 runc 退出后容器继续运行。",
    difficulty: 0.5,
    code_ref: "containerd/shim/",
    created_at: datetime()
})

// 架构关系
CREATE (d)-[:CALLS]->(ct)
CREATE (ct)-[:CALLS]->(sh)
CREATE (sh)-[:CALLS]->(rc)
CREATE (r)-[:RELATES_TO]->(ct)
CREATE (r)-[:RELATES_TO]->(rc)
CREATE (r)-[:RELATES_TO]->(sh)

// ============================================================
// 误解节点
// ============================================================

CREATE (m1:Misconception {
    id: "mc-container-vm",
    pattern: "容器是轻量级虚拟机",
    severity: "critical",
    correction: "容器共享宿主机内核（通过 namespaces 隔离，cgroups 限制资源），虚拟机通过 Hypervisor 虚拟化硬件，每个 VM 有独立内核。",
    keywords: ["轻量级虚拟机", "VM", "虚拟化", "阉割版"]
})
CREATE (c)-[:HAS_MISCONCEPTION]->(m1)

CREATE (m2:Misconception {
    id: "mc-docker-runtime",
    pattern: "Docker 就是容器运行时",
    severity: "major",
    correction: "Docker 是一个完整的容器平台（CLI + API + 管理面）。容器运行时是 containerd/runc 这样的底层组件。",
    keywords: ["Docker 就是", "Docker 等于", "Docker 只是"]
})
CREATE (r)-[:HAS_MISCONCEPTION]->(m2)

CREATE (m3:Misconception {
    id: "mc-runc-manager",
    pattern: "runc 一直运行着管理容器",
    severity: "major",
    correction: "runc 完成容器创建和启动后立即退出。容器的持续运行由 shim 接管，runc 是启动器不是管理器。",
    keywords: ["一直运行", "持续管理", "常驻"]
})
CREATE (rc)-[:HAS_MISCONCEPTION]->(m3)

// ============================================================
// 前置知识关系
// ============================================================

// 容器的前置知识
CREATE (p1:Concept:LearningNode {
    id: "linux-process",
    name: "Linux 进程",
    difficulty: 0.1
})
CREATE (p2:Concept:LearningNode {
    id: "filesystem",
    name: "文件系统",
    difficulty: 0.1
})
CREATE (p1)-[:PREREQUISITE]->(c)
CREATE (p2)-[:PREREQUISITE]->(c)

// 容器运行时的前置知识
CREATE (p3:Concept:LearningNode {
    id: "cgroups",
    name: "cgroups",
    difficulty: 0.4
})
CREATE (p4:Concept:LearningNode {
    id: "namespaces",
    name: "namespaces",
    difficulty: 0.4
})
CREATE (p3)-[:PREREQUISITE]->(r)
CREATE (p4)-[:PREREQUISITE]->(r)

// ============================================================
// 索引
// ============================================================

CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)
CREATE INDEX concept_id IF NOT EXISTS FOR (c:Concept) ON (c.id)

RETURN "知识图谱初始化完成" AS result