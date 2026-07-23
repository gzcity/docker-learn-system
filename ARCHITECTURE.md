# Docker 源码学习系统 — 详细架构设计

> 本文档深入描述系统的技术架构、数据流、状态管理和工具集成。

---

## 1. 核心数据流架构

### 1.1 三层数据流模型

```
输入层                        处理层                             输出层
┌────────┐    ┌─────────────────────────────────────────┐    ┌────────┐
│ 用户   │    │  Orchestrator                            │    │ 文字   │
│ 输入   │───►│  ┌─────────┐  ┌──────────────────────┐  │───►│ 回答   │
└────────┘    │  │ 意图分类 │  │ 上下文组装器          │  │    └────────┘
              │  │         │  │ - 注入掌握度           │  │    ┌────────┐
              │  │ - 概念  │  │ - 注入记忆             │  │    │ 测验   │
              │  │ - 操作  │  │ - 注入人格             │  │───►│ 题目   │
              │  │ - 模式  │  │ - 注入知识库片段       │  │    └────────┘
              │  └────┬────┘  └───────────┬──────────┘  │    ┌────────┐
              │       │                   │              │    │ 可视   │
              │       ▼                   ▼              │───►│ 化图表 │
              │  ┌────────────────────────────────────┐  │    └────────┘
              │  │  Agent 路由                        │  │    ┌────────┐
              │  │  ┌──────┐ ┌──────┐ ┌──────┐       │  │    │ 研究   │
              │  │  │Tutor │ │Quiz  │ │Viz   │...     │  │───►│ 报告   │
              │  │  └──┬───┘ └──┬───┘ └──┬───┘       │  │    └────────┘
              │  └─────┼────────┼────────┼───────────┘  │    ┌────────┐
              │        │        │        │              │    │ 练习   │
              │        ▼        ▼        ▼              │───►│ 计划   │
              │  ┌────────────────────────────────────┐  │    └────────┘
              │  │  工具调用层                         │  │
              │  │  Browser  │  Code Read  │  Search  │  │
              │  └────────────────────────────────────┘  │
              └─────────────────────────────────────────┘
```

### 1.2 知识图谱查询模式

```
┌──────────────────────────────────────────────────────────────────┐
│                      图谱查询模式                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query 1: 概念展开                                              │
│  MATCH (c:Concept {name: "容器运行时"})                          │
│  OPTIONAL MATCH (c)-[:BELONGS_TO]->(f:SourceFile)                │
│  OPTIONAL MATCH (c)-[:PREREQUISITE]->(p:Concept)                 │
│  OPTIONAL MATCH (c)<-[:PREREQUISITE]-(n:Concept)                 │
│  RETURN c, collect(f), collect(p), collect(n)                    │
│                                                                  │
│  Query 2: 薄弱点发现                                             │
│  MATCH (u:User {id: $user_id})-[r:MASTERY_LEVEL]->(c:Concept)   │
│  WHERE r.level < 0.5                                             │
│  RETURN c, r.level ORDER BY r.level ASC                          │
│                                                                  │
│  Query 3: 学习路径推荐                                           │
│  MATCH path = (c1:Concept)-[:PREREQUISITE*]->(c2:Concept)        │
│  WHERE c1.name = $current_concept                                │
│  AND NOT EXISTS (                                                │
│    MATCH (u:User)-[:MASTERY_LEVEL]->(c2) WHERE u.id = $user_id  │
│  )                                                               │
│  RETURN path ORDER BY length(path) ASC                           │
│                                                                  │
│  Query 4: 关联内容检索                                           │
│  MATCH (c:Concept {name: $concept})                              │
│  OPTIONAL MATCH (c)-[:HAS_QUESTION]->(q:Question)                │
│  OPTIONAL MATCH (c)-[:HAS_NOTE]->(n:Note)                        │
│  OPTIONAL MATCH (book:Book)-[:COVERS]->(c)                       │
│  RETURN q, n, book                                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. 状态管理

### 2.1 状态图谱

```
┌──────────────────────────────────────────────────────────────────┐
│                      系统状态树                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SystemState                                                      │
│  ├── activeSession: SessionState                                  │
│  │   ├── userId, sessionId, startTime                             │
│  │   ├── context: ContextObject (当前上下文)                       │
│  │   ├── dialogueHistory: Message[] (最近N轮)                     │
│  │   └── pendingActions: Action[] (待处理动作队列)                 │
│  │                                                                 │
│  ├── knowledgeGraph: GraphState                                    │
│  │   ├── loaded: boolean                                          │
│  │   ├── lastSync: timestamp                                      │
│  │   └── cache: Map<conceptId, ConceptNode>                       │
│  │                                                                 │
│  ├── userMemory: MemoryState                                       │
│  │   ├── loaded: boolean                                          │
│  │   ├── userProfile: UserProfile                                  │
│  │   └── masteryRecords: Map<conceptId, MasteryRecord>             │
│  │                                                                 │
│  ├── activePersona: PersonaState                                   │
│  │   ├── current: string ("socratic")                              │
│  │   ├── override: boolean (是否临时覆盖)                          │
│  │   └── stack: string[] (人格切换栈，支持回溯)                    │
│  │                                                                 │
│  └── toolStates: Map<toolId, ToolState>                            │
│      ├── browser: { running, currentUrl, tabs }                    │
│      ├── codeReader: { currentFile, lines }                        │
│      └── search: { lastQuery, results }                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 状态流转

```
         ┌──────────┐
         │  空闲态   │ ←── 等待用户输入
         └────┬─────┘
              │ 用户输入到达
              ▼
         ┌──────────┐
         │  理解态   │ ←── 意图识别 + 上下文组装
         └────┬─────┘
              │ 意图已识别
              ▼
         ┌──────────┐
         │  处理态   │ ←── Agent 路由 + 工具调用
         └────┬─────┘
              │ 处理完成
              ▼
         ┌──────────┐
         │  输出态   │ ←── 生成回复 + 更新记忆
         └────┬─────┘
              │ 输出完成
              ▼
         ┌──────────┐
         │  空闲态   │ ←── 等待下一次输入
         └──────────┘
```

---

## 3. Docker 源码知识图谱初始化

### 3.1 源码解析策略

```
Docker 源码目录结构（了解析目标）：
docker/
├── cmd/          # CLI 入口
│   ├── docker/   # docker 命令
│   └── dockerd/  # 守护进程
├── daemon/       # 核心守护进程逻辑
├── builder/      # 镜像构建
├── distribution/ # 镜像分发
├── network/      # 网络管理
├── volume/       # 存储卷
├── image/        # 镜像管理
├── container/    # 容器管理
├── layer/        # 层管理
├── plugin/       # 插件系统
├── api/          # API 定义
├── client/       # 客户端 SDK
├── cli/          # CLI 逻辑
├── opts/         # 选项解析
├── pkg/          # 公共包
└── integration/  # 集成测试
```

**解析策略**：
1. **入口优先**：从 `cmd/` 和 `api/` 开始，建立骨架
2. **核心优先**：`daemon/`、`container/`、`image/` 核心模块
3. **按需深入**：用户问到哪个模块，再深入解析
4. **增量构建**：每次学习后，将新解析的代码加入知识图谱

### 3.2 自动概念提取

```
从 Go 源码中自动提取概念的规则：

1. 包 (package) → Concept 节点
   pkg/archive/ → "归档处理"

2. 接口 (interface) → Concept 节点
   type ImageService interface → "镜像服务接口"
   
3. 结构体 (struct) → Concept 节点
   type Container struct → "容器对象"

4. 函数 (func) → 关联到所属概念
   func (s *containerStore) Add → containerStore.Add 方法

5. 接口实现 → IMPLEMENTS 关系
   type containerStore struct → IMPLEMENTS → Store interface

6. 函数调用 → CALLS 关系
   (从 AST 中提取调用关系)

7. 导入路径 → REFERENCES 关系
   import "github.com/docker/docker/container" → REFERENCES
```

---

## 4. 工具集成层

### 4.1 现有 Skills 复用

| Skill | 在此系统中的用途 | 调用时机 |
|-------|----------------|---------|
| **browser_use** | 浏览 Docker 官方文档、GitHub 源码、社区讨论 | 深度研究、查阅资料 |
| **file_reader** | 读取本地 Docker 源码文件 | 源码分析、代码讲解 |
| **pdf** | 生成学习报告 PDF、导出笔记 | 知识输出、学习总结 |
| **docx** | 生成结构化的学习笔记文档 | 知识输出、学习总结 |
| **pptx** | 生成学习成果演示 | 知识输出、分享 |
| **xlsx** | 掌握度统计表、学习计划表 | 进度追踪 |
| **multi_agent_collaboration** | 多 Agent 协作（调用其他 Agent） | 复杂任务拆分 |
| **cron** | 定时复习提醒、每日学习总结 | 间隔重复、习惯养成 |
| **channel_message** | 推送学习提醒、每日总结 | 主动通知 |
| **news** | 获取 Docker 社区最新动态 | 知识更新 |
| **guidance** | 本系统自身的安装与配置指南 | 系统引导 |

### 4.2 MCP 工具扩展

```
需要新增的 MCP 工具：

1. 知识图谱工具 (knowledge_graph)
   - kg_query: 执行 Cypher 查询
   - kg_upsert: 创建/更新节点
   - kg_delete: 删除节点
   - kg_shortest_path: 概念间最短路径

2. 掌握度工具 (mastery)
   - mastery_get: 获取概念掌握度
   - mastery_update: 更新掌握度
   - mastery_recommend: 获取复习推荐
   - mastery_heatmap: 生成掌握度热力图

3. 间隔重复工具 (spaced_repetition)
   - sr_schedule: 计算复习时间
   - sr_due: 获取到期复习项
   - sr_review: 记录复习结果

4. 题库工具 (question_bank)
   - qb_search: 搜索题目
   - qb_generate: 动态生成题目
   - qb_stats: 题目统计
   - qb_export: 导出题目
```

---

## 5. 上下文持久化机制

### 5.1 会话恢复流程

```
用户再次进入系统：
  │
  ├── 1. 读取最近会话记录 sessions/latest.json
  │
  ├── 2. 恢复上下文对象
  │   ├── 上次学习的知识点
  │   ├── 掌握度快照
  │   ├── 未完成的题目
  │   └── 人格偏好
  │
  ├── 3. 读取每日记忆
  │   ├── 昨天学了什么
  │   ├── 遇到的问题
  │   └── 今天的推荐
  │
  └── 4. 生成恢复提示
      "欢迎回来！上次我们学到了容器运行时，
       你对 cgroups 的掌握度是 60%。
       最后有一个关于 runc 的题目没做完，要接着做吗？
       今天推荐学习 overlay2 存储驱动。"
```

### 5.2 跨会话上下文桥接

```
会话 A (今天)                       会话 B (明天)
┌──────────────────┐              ┌──────────────────┐
│ 正在学: cgroups  │              │ 上下文注入        │
│ 掌握度: 0.6      │───持久化───►│ 当前: cgroups     │
│ 未完成: Q-042    │              │ 掌握度: 0.6      │
│ 人格: socratic   │              │ 待办: Q-042      │
└──────────────────┘              │ 人格: socratic   │
                                  └──────────────────┘
```

---

## 6. Docker 源码学习路径设计

### 6.1 推荐学习路径（从入门到精通）

```
第一阶段：理解 Docker 架构（1-2 天）
  ├── Docker 整体架构图
  ├── client-server 模式
  ├── CLI → API → Daemon 调用链
  └── 关键组件：dockerd, containerd, runc, shim

第二阶段：容器生命周期（3-5 天）
  ├── 容器创建流程
  ├── 容器启动流程
  ├── 容器停止与删除
  └── 源码路径：cmd/dockerd → daemon/ → container/

第三阶段：镜像管理（2-3 天）
  ├── 镜像拉取流程
  ├── 镜像构建流程
  ├── 镜像层管理
  └── 源码路径：distribution/ → image/ → layer/

第四阶段：网络与存储（3-4 天）
  ├── 网络模型 (bridge, overlay, host)
  ├── 存储驱动 (overlay2, aufs)
  ├── 数据卷管理
  └── 源码路径：network/ → volume/

第五阶段：高级主题（5-7 天）
  ├── 插件系统
  ├── 安全机制
  ├── 集群管理 (Swarm)
  └── 源码路径：plugin/ → swarm/

第六阶段：贡献与扩展（持续）
  ├── 代码规范与贡献流程
  ├── 调试技巧
  ├── 性能优化
  └── 自定义扩展开发
```

### 6.2 自适应路径调整

```
用户基础 -> 学习路径调整：

有 Go 基础：
  → 跳过 Go 语法讲解
  → 直接进入源码分析
  → 更多代码填空和代码分析题

无容器基础：
  → 先补充容器基础概念
  → 更多类比和故事化讲解
  → 更多基础选择题

有 Docker 使用经验：
  → 跳过基础使用讲解
  → 聚焦实现原理
  → 更多架构设计题
```

---

## 7. 性能与扩展性

### 7.1 缓存策略

```
┌──────────────────────────────────────────────────────────────────┐
│                        缓存层级                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L1: 会话缓存 (内存)                                              │
│  缓存：当前会话的知识图谱查询结果                                   │
│  过期：会话结束                                                   │
│  大小：~10MB                                                      │
│                                                                  │
│  L2: 知识图谱缓存 (内存 + Redis)                                   │
│  缓存：高频查询的概念节点和关系                                     │
│  过期：LRU，最大 1000 条                                           │
│  大小：~100MB                                                     │
│                                                                  │
│  L3: 源码缓存 (磁盘)                                              │
│  缓存：已解析的 Docker 源码 AST                                    │
│  过期：Docker 版本更新时失效                                       │
│  大小：~500MB                                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 扩展性设计

```
1. 多语言支持：知识图谱节点支持多语言 label
   (Concept)-[:HAS_LABEL]->(Label {lang: "zh", text: "容器运行时"})
   (Concept)-[:HAS_LABEL]->(Label {lang: "en", text: "Container Runtime"})

2. 多源码库支持：知识图谱不限于 Docker
   (Codebase {name: "docker"})
   (Codebase {name: "containerd"})
   (Codebase {name: "runc"})
   
3. 用户社区：知识库和题库可共享
   (User {id: "A"})-[:CONTRIBUTED]->(Question)
   (User {id: "B"})-[:USED]->(Question)
```

---

## 8. 安全与隐私

### 8.1 数据隔离

```
用户数据严格隔离：
├── 用户知识图谱：每个用户独立的命名空间
│   MATCH (u:User {id: $user_id})  // 始终带用户 ID 过滤
│
├── 用户记忆：文件按用户隔离
│   memory/${user_id}/YYYY-MM-DD.md
│
└── 共享知识库：只读，不可修改
    知识库中的 Docker 源码分析是共享的
```

### 8.2 敏感信息处理

```
- 用户密码/Token：不存储，不记录
- 用户代码：属于用户，不共享
- 学习数据：仅用户自己可见
- 知识图谱中的源码引用：仅引用行号，不复制完整代码
```

---

## 9. Expectation-Misconception 检测引擎

### 9.1 架构位置

```
用户输入
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Orchestrator 处理流程                                           │
│                                                                  │
│  1. 意图识别 ───────────────────────────────────────────────    │
│  2. 上下文组装 ─────────────────────────────────────────────    │
│  3. ► 误解检测 ← 新增步骤，在进入 Agent 路由之前               │
│  4. Agent 路由 ─────────────────────────────────────────────    │
│  5. 工具调用 ───────────────────────────────────────────────    │
│  6. 输出生成 ───────────────────────────────────────────────    │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 检测引擎模块

```
misconception_engine/
├── detector.py          # 主检测器
│   ├── keyword_match()      # 关键词匹配
│   ├── semantic_match()     # 语义相似度匹配
│   ├── negation_detect()    # 否定检测
│   └── inference_analyze()  # 推理链分析
│
├── index.py             # 误解索引
│   ├── build_index()        # 从知识图谱构建误解索引
│   ├── search()             # 搜索匹配的误解
│   └── rank()               # 按匹配度排序
│
├── corrector.py         # 纠正生成器
│   ├── generate_correction()  # 生成纠正回复
│   ├── follow_up()            # 生成追问
│   └── verify_understanding() # 验证用户是否理解
│
└── tracker.py           # 误解追踪器
    ├── record()              # 记录到用户记忆
    ├── check_recurrence()    # 检查是否反复出现
    └── suggest_review()      # 建议复习时机
```

### 9.3 检测算法

```
def detect_misconception(user_input, current_concept, user_memory):
    """
    三步检测法：
    1. 精确匹配：直接命中已知误解关键词
    2. 语义匹配：嵌入向量相似度 > 阈值
    3. 推理分析：从用户的多轮对话中推断
    """
    # 第一步：关键词匹配 (O(1) 哈希查找)
    for mc in current_concept.misconceptions:
        if any(keyword in user_input for keyword in mc.keywords):
            return mc, "keyword_match"
    
    # 第二步：语义匹配 (向量相似度)
    input_embedding = embed(user_input)
    for mc in current_concept.misconceptions:
        similarity = cosine_similarity(input_embedding, mc.embedding)
        if similarity > THRESHOLD_SEMANTIC:
            return mc, "semantic_match"
    
    # 第三步：检查用户历史误解 (避免重复纠正)
    for history_mc in user_memory.misconceptions:
        if history_mc.status == "corrected":
            continue  # 已纠正的误解不再触发
        if semantic_similarity(user_input, history_mc.pattern) > THRESHOLD_RECURRENCE:
            return history_mc, "recurrence"
    
    return None, None
```

### 9.4 图谱集成

在知识图谱中，误解以独立节点类型存在，通过 `:HAS_MISCONCEPTION` 关系关联到概念：

```
(Concept:容器运行时)
    │
    ├──[:HAS_MISCONCEPTION]→ (Misconception)
    │   ├── pattern: "容器是轻量级虚拟机"
    │   ├── severity: "critical"
    │   ├── keywords: ["轻量级虚拟机", "VM", "虚拟化", "阉割版"]
    │   └── correction: "容器共享宿主机内核..."
    │
    ├──[:HAS_MISCONCEPTION]→ (Misconception)
    │   ├── pattern: "Docker 就是容器运行时"
    │   ├── severity: "major"
    │   └── ...
    │
    └──[:HAS_MISCONCEPTION]→ (Misconception)
        ├── pattern: "runc 一直运行着管理容器"
        └── ...

查询示例：
MATCH (c:Concept {name: "容器运行时"})-[:HAS_MISCONCEPTION]->(m:Misconception)
WHERE m.severity = "critical"
RETURN m.pattern, m.correction
```

### 9.5 与现有系统的集成点

| 组件 | 集成方式 | 触发条件 |
|------|---------|---------|
| **对话 Agent** | 回复前插入误解检测步骤 | 每次用户输入 |
| **知识库 Agent** | 将误解写入概念节点 | 知识库更新时 |
| **题库 Agent** | 针对误解生成针对性题目 | 用户被纠正后 |
| **掌握度模型** | 误解导致掌握度扣减 0.1-0.2 | 检测到误解时 |
| **记忆系统** | 记录误解及纠正历史 | 纠正完成后 |
| **可视化** | 生成"误解地图" | 用户请求时 |