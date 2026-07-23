# Docker 源码学习系统 — 实现路线图

> 从零到完整系统的分阶段实现计划。每个阶段都是可运行、可交付的增量。

---

## 阶段总览

| 阶段 | 名称 | 周期 | 核心交付物 | 可运行？ |
|------|------|------|-----------|---------|
| P0 | 基础骨架 | 1 天 | 多 Agent 框架 + 知识图谱 + 对话 + 误解框架 | ✅ |
| P1 | 知识库 + 书籍 | 2 天 | 知识库管理 + 交互式书籍阅读 | ✅ |
| P2 | 题库 + 测验 | 2 天 | 动态测验生成 + 自动评分 + 误解检测引擎 | ✅ |
| P3 | 掌握度 + 练习 | 2 天 | 掌握度模型 + 间隔重复练习 | ✅ |
| P4 | 深度研究 + 可视化 | 3 天 | 源码自动分析 + 图表生成 | ✅ |
| P5 | 长期记忆 + 上下文 | 1 天 | 跨会话记忆 + 会话恢复 | ✅ |
| P6 | 人格预设 + 自适应 | 1 天 | 多人格教学 + 自适应路径 | ✅ |
| P7 | 打磨与集成 | 2 天 | 学习闭环整合 + 体验优化 | ✅ |

---

## P0 — 基础骨架（1 天）

### 目标
建立多 Agent 协作框架，初始化 Docker 知识图谱的基础节点，实现基础对话功能。

### 任务清单

```
□ 1.1 创建 Agent 框架
    ├── agents/
    │   ├── orchestrator.md     # Orchestrator 的 AGENTS.md
    │   ├── tutor.md
    │   ├── quizmaster.md
    │   ├── researcher.md
    │   ├── visualizer.md
    │   ├── coach.md
    │   ├── librarian.md
    │   └── scribe.md
    └── 每个文件包含：
        - 角色定义
        - 核心能力列表
        - 上下文处理规则
        - 协作协议

□ 1.2 初始化知识图谱
    ├── docker-knowledge/
    │   ├── concepts/           # 概念节点定义
    │   │   ├── 00-容器基础.md
    │   │   ├── 01-容器运行时.md
    │   │   ├── 02-镜像与层.md
    │   │   ├── 03-网络模型.md
    │   │   ├── 04-存储驱动.md
    │   │   ├── 05-源码架构.md
    │   │   └── 06-扩展主题.md
    │   ├── relationships/      # 关系定义
    │   │   └── graph.json     # 节点间关系
    │   └── build.sh           # 构建图谱脚本
    └── 初始节点：~30 个核心概念

□ 1.3 实现基础对话 Agent
    ├── commands/
    │   ├── learn.md           # "学 Docker" 命令
    │   ├── concept.md         # 概念查询
    │   └── context.md         # 上下文查看
    └── 功能：
        - 接收用户提问
        - 检索知识图谱
        - 生成回答
        - 更新会话上下文

□ 1.4 会话上下文管理
    ├── session/
    │   ├── context.py         # 上下文对象
    │   ├── store.py           # 上下文持久化
    │   └── restore.py         # 上下文恢复
    └── 功能：
        - 上下文对象定义
        - 会话间持久化
        - 自动恢复

□ 1.5 误解框架初始化 [DeepTutor 集成]
    ├── misconception/
    │   ├── schema.py          # 误解数据结构定义
    │   ├── seed.py            # 从 CONCEPTS.md 加载初始误解
    │   └── index.py           # 误解关键词索引
    ├── 在知识图谱中添加：
    │   └── 每个概念节点 → HAS_MISCONCEPTION → Misconception 节点
    └── 初始数据：~15 个常见误解（从 CONCEPTS.md 中提取）
```

### 交付检查
```
✅ 用户可以说"学 Docker 源码"，系统开始响应
✅ 用户问概念，系统从知识图谱检索并回答
✅ 系统能记住当前会话上下文
✅ 基础多 Agent 框架可运行
```

---

## P1 — 知识库 + 书籍（2 天）

### 目标
构建结构化的 Docker 知识库，支持交互式书籍阅读和笔记管理。

### 任务清单

```
□ 2.1 知识库构建
    ├── docker-knowledge/
    │   ├── structure.json     # 知识库层次结构
    │   ├── basic/             # 基础概念
    │   ├── source/            # 源码架构
    │   ├── design/            # 设计决策
    │   └── practice/          # 实践技巧
    └── 每个知识文档包含：
        - 概念定义
        - 代码引用
        - 关联概念
        - 难度等级
        - 前置知识

□ 2.2 书籍系统
    ├── books/
    │   ├── docker-shenjiu/    # 《Docker 源码深究》
    │   │   ├── book.json      # 书籍元数据
    │   │   ├── chapter-01/    # 第1章
    │   │   ├── chapter-02/    # 第2章
    │   │   └── ...
    │   └── book-template/     # 书籍模板
    ├── commands/
    │   ├── book-open.md       # 打开书籍
    │   ├── book-chapter.md    # 跳转章节
    │   ├── book-note.md       # 添加笔记
    │   └── book-progress.md   # 查看进度
    └── 功能：
        - 按章节阅读
        - 添加笔记（笔记关联到概念节点）
        - 阅读进度追踪
        - 章节内代码链接跳转

□ 2.3 笔记系统
    ├── notes/
    │   ├── link-to-concept.py # 笔记关联概念
    │   ├── search.py          # 笔记搜索
    │   └── export.py          # 笔记导出
    └── 功能：
        - 笔记自动关联当前概念
        - 语义搜索笔记
        - 笔记导出为 Markdown/PDF
```

### 交付检查
```
✅ 知识库可查询、可浏览
✅ 书籍可阅读、可跳转、可标注
✅ 笔记可添加、可搜索、可导出
✅ 笔记自动关联到知识图谱概念
```

---

## P2 — 题库 + 测验（2 天）

### 目标
建立关联知识图谱的题库，支持动态测验生成和自动评分。

### 任务清单

```
✅ 3.1 题库构建
    ├── questions/
    │   ├── question-schema.json  # 题目结构定义
    │   ├── generate/             # 自动生成题目
    │   │   ├── from-concept.py   # 从概念生成
    │   │   ├── from-code.py      # 从源码生成
    │   │   └── from-book.py      # 从书籍生成
    │   ├── manual/               # 手动编写的题目
    │   └── index.json            # 题库索引
    └── 初始题目：14 道（覆盖核心概念，6 种题型）

✅ 3.2 测验生成引擎
    ├── quiz/
    │   ├── generator.py       # 测验生成器
    │   ├── difficulty.py      # 难度适配
    │   ├── scorer.py          # 自动评分
    │   └── feedback.py        # 答题反馈
    └── 功能：
        - 根据概念范围出题
        - 根据掌握度调整难度
        - 多种题型支持
        - 自动评分 + 解析

✅ 3.3 测验命令
    ├── commands/
    │   ├── quiz-start.md      # 开始测验
    │   ├── quiz-answer.md     # 作答
    │   ├── quiz-result.md     # 查看结果
    │   └── quiz-history.md    # 历史记录
    └── 交互流程：
        用户 → 请求测验 → 系统出题 → 用户作答
        → 自动评分 → 显示解析 → 更新掌握度

✅ 3.4 误解检测引擎 [DeepTutor 集成]
    ├── detector/
    │   ├── keyword_match.py   # 关键词匹配检测
    │   ├── semantic_match.py  # 语义相似度检测
    │   ├── negation_detect.py # 否定检测
    │   └── inference.py       # 推理链分析
    ├── corrector/
    │   ├── generate.py        # 纠正回复生成
    │   ├── follow_up.py       # 追问生成
    │   └── verify.py          # 理解验证
    ├── tracker/
    │   ├── record.py          # 记录到用户记忆
    │   ├── recur.py           # 反复出现检测
    │   └── review.py          # 复习建议
    └── 集成：
        - 对话 Agent 回复前插入误解检测步骤
        - 检测到误解 → 触发纠正流程 → 更新掌握度 → 记录到记忆
        - 误解关联的题目在测验中优先出现
```

### 交付检查
```
✅ 题库可查询、可检索（14 题，6 种题型）
✅ 可动态生成测验（指定概念/范围/难度）
✅ 自动评分 + 解析（5 种评分器）
✅ 测验结果更新掌握度
✅ 测验历史记录
✅ 交互式答题流程（出题→答题→反馈→下一题→完成统计）
```

---

## P3 — 掌握度 + 练习（2 天）

### 目标
实现掌握度模型和间隔重复练习系统。

### 任务清单

```
✅ 4.1 掌握度模型
    ├── mastery/
    │   ├── model.py           # 掌握度模型定义
    │   ├── update.py          # 更新规则
    │   ├── decay.py           # 遗忘曲线
    │   ├── propagate.py       # 关联传播
    │   └── predict.py         # 预测下次复习时间
    └── 算法：
        - 基于 SM-2 的间隔重复
        - 关联概念传递
        - 遗忘曲线模拟

✅ 4.2 练习系统
    ├── practice/
    │   ├── planner.py         # 练习计划生成
    │   ├── session.py         # 练习会话管理
    │   ├── quick.py           # 快速练习模式
    │   ├── deep.py            # 深度练习模式
    │   ├── review.py          # 错题重练
    │   └── report.py          # 练习报告
    └── 功能：
        - 多种练习模式（快速/深度/复习）
        - 自适应难度
        - 间隔重复提醒
        - 练习报告生成

✅ 4.3 掌握度命令
    ├── commands/
    │   ├── mastery-view.md    # 查看掌握度
    │   ├── mastery-heatmap.md # 掌握度热力图
    │   ├── practice-start.md  # 开始练习
    │   └── practice-report.md # 练习报告
    └── 可视化：
        - 文字表格
        - Mermaid 热力图
        - 进度条
```

### 交付检查
```
✅ 每个概念有独立掌握度评分（SM-2 算法）
✅ 练习后掌握度自动更新（含关联传播）
✅ 间隔重复推送复习提醒（到期检测）
✅ 掌握度可视化（热力图/表格/进度条）
✅ 三种练习模式（快速/深度/复习）
```

---

## P4 — 深度研究 + 可视化（3 天）

### 目标
实现 Docker 源码的自动分析和结构化可视化。

### 任务清单

```
✅ 5.1 源码分析引擎
    ├── research/
    │   ├── code-loader.py     # 源码加载器
    │   ├── parser.py          # Go AST 解析
    │   ├── extractor.py       # 概念提取
    │   ├── relationship.py    # 关系发现
    │   ├── report.py          # 研究报告生成
    │   └── template.md        # 报告模板
    └── 功能：
        - 自动分析 Docker 源码概念
        - 提取函数、结构体、接口
        - 发现函数调用关系
        - 生成结构化报告（7 章节）

✅ 5.2 可视化引擎
    ├── visualize/
    │   ├── mermaid.py         # Mermaid 图生成
    │   ├── architecture.py    # 架构图
    │   ├── callchain.py       # 调用链
    │   ├── classdiagram.py    # 类图
    │   ├── datalflow.py       # 数据流图
    │   ├── learningpath.py    # 学习路径图
    │   └── heatmap.py         # 掌握度热力图
    └── 功能：
        - 8 种图表类型
        - 从知识图谱自动生成
        - 图表可交互式深入

✅ 5.3 研究命令
    ├── commands/
    │   ├── research-start.md  # 开始研究
    │   ├── research-depth.md  # 深入方向
    │   ├── research-export.md # 导出报告
    │   └── visualize.md       # 生成可视化
    └── 交互流程：
        用户 → 指定主题 → 系统分析源码
        → 生成报告 → 生成图表 → 入库
```

### 交付检查
```
✅ 可自动分析 Docker 源码概念（知识图谱驱动）
✅ 可生成 8 种图表（架构图、调用链、学习路径、知识图谱、数据流、类图、进度图、热力图）
✅ 研究结果自动生成（7 章节深度研究报告）
✅ 图表可交互式深入（Mermaid 格式支持渲染）
```

---

## P5 — 长期记忆 + 上下文（1 天）

### 目标
实现跨会话的长期记忆和上下文恢复。

### 任务清单

```
✅ 6.1 长期记忆系统
    ├── memory/
    │   ├── schema.py          # 记忆结构定义
    │   ├── store.py           # 记忆存储
    │   ├── retrieve.py        # 记忆检索
    │   ├── summarize.py       # 记忆总结
    │   └── forget.py          # 记忆衰减/清理
    └── 功能：
        - 用户画像维护
        - 学习历史记录
        - 薄弱点/强项追踪
        - 误解纠正记录 ← 新增：记录用户曾有的误解和纠正状态
        - 误解复发检测 ← 新增：检查用户是否反复出现相同误解

✅ 6.2 每日学习记录
    ├── daily/
    │   ├── log.py             # 每日日志生成
    │   ├── summary.py         # 学习总结
    │   ├── recommend.py       # 明日推荐
    │   └── template.md        # 日志模板
    └── 功能：
        - 自动记录每日学习内容
        - 掌握度变化追踪
        - 明日学习推荐

✅ 6.3 会话恢复
    ├── session/
    │   ├── save.py            # 会话保存
    │   ├── load.py            # 会话加载
    │   └── bridge.py          # 会话桥接
    └── 功能：
        - 会话结束时自动保存
        - 新会话自动恢复上下文
        - 生成恢复提示
```

### 交付检查
```
✅ 系统能记住用户是谁、学到哪了
✅ 每日学习记录自动生成
✅ 跨会话上下文自动恢复
✅ 记忆可查询、可更新
```

---

## P6 — 人格预设 + 自适应（1 天）

### 目标
实现多人格教学和自适应学习路径。

### 任务清单

```
✅ 7.1 人格预设系统
    ├── personas/
    │   ├── socratic.yaml      # 苏格拉底
    │   ├── professor.yaml     # 教授
    │   ├── practitioner.yaml  # 实践者
    │   ├── storyteller.yaml   # 说书人
    │   ├── coach.yaml         # 教练
    │   ├── debugger.yaml      # 调试者
    │   ├── minimalist.yaml    # 极简者
    │   └── devils_advocate.yaml # 唱反调
    ├── engine/
    │   ├── loader.py          # 人格加载
    │   ├── switcher.py        # 人格切换
    │   ├── stack.py           # 人格栈（支持回溯）
    │   └── template.py        # 提示词模板引擎
    └── 功能：
        - 8 种人格预设
        - 临时切换/永久切换
        - 人格叠加（教授+代码示例）
        - 人格记录到用户记忆

✅ 7.2 自适应学习路径
    ├── path/
    │   ├── assess.py          # 基础评估
    │   ├── planner.py         # 路径规划
    │   ├── adapter.py         # 路径调整
    │   └── recommend.py       # 内容推荐
    └── 功能：
        - 根据用户基础调整路径
        - 根据掌握度调整节奏
        - 根据学习偏好调整方式
        - 动态推荐下一学习内容

✅ 7.3 人格命令
    ├── commands/
    │   ├── persona-set.md     # 设置人格
    │   ├── persona-list.md    # 查看可选人格
    │   ├── persona-current.md # 查看当前人格
    │   └── path-view.md       # 查看学习路径
```

### 交付检查
```
✅ 可切换人格（临时/永久）
✅ 不同人格输出风格不同
✅ 学习路径自适应调整
✅ 人格偏好记录到记忆
```

---

## P7 — 打磨与集成（2 天）

### 目标
将所有功能整合为流畅的学习闭环，优化用户体验。

### 任务清单

```
✅ 8.1 学习闭环整合
    ├── flow/
    │   ├── discover-loop.md   # 发现 → 学习 → 练习
    │   ├── weak-loop.md       # 薄弱点 → 强化 → 验证
    │   ├── review-loop.md     # 复习 → 巩固 → 推进
    │   └── deep-loop.md       # 疑问 → 研究 → 理解
    └── 每个闭环定义：
        - 触发条件
        - 参与 Agent
        - 数据流
        - 状态更新

✅ 8.2 学习仪表盘
    ├── dashboard/
    │   ├── overview.md        # 总览
    │   ├── progress.md        # 进度
    │   ├── weak-spots.md      # 薄弱点
    │   ├── recent.md          # 最近学习
    │   └── recommendations.md # 推荐
    └── 输出格式：Markdown + Mermaid

✅ 8.3 系统命令
    ├── commands/
    │   ├── status.md          # 系统状态
    │   ├── stats.md           # 学习统计
    │   ├── export.md          # 导出学习数据
    │   ├── reset.md           # 重置进度
    │   └── help.md            # 学习系统帮助
    └── 统一命令前缀：/learn

✅ 8.4 体验优化
    ├── UX/
    │   ├── onboarding.md      # 引导流程
    │   ├── feedback.md        # 反馈机制
    │   ├── continuous.md      # 持续学习提示
    │   └── celebrate.md       # 里程碑庆祝
    └── 功能：
        - 新用户引导
        - 学习反馈收集
        - 定时学习提醒
        - 里程碑达成庆祝
```

### 交付检查
```
✅ 完整学习闭环可运行
✅ 学习仪表盘可用
✅ 所有命令统一可用
✅ 用户体验流畅
```

---

## 附录：快速启动

### 最小可行系统（1 小时可上手）

```
1. 创建 agents/ 目录和基础 Agent 定义
2. 创建 docker-knowledge/concepts/ 核心概念
3. 实现基础对话（上下文注入 + 知识检索）
4. 实现基础掌握度（简单评分 + 记录）

这就是 MVP。其他功能在此基础上逐步叠加。
```

### 关键设计决策

```
1. 知识图谱优先于向量数据库
   - 先关系，后语义
   - 关系查询比语义搜索更适合学习路径推理

2. Agent 协作优先于 Monolithic
   - 每个 Agent 职责单一
   - 通过 Orchestrator 协调
   - 可独立测试和迭代

3. 文件系统优先于数据库
   - 初期用文件存储，后期再迁移
   - Markdown 是人类可读的
   - 不依赖外部基础设施

4. 增量构建优先于完美设计
   - 每个阶段都是可运行的
   - 先有，再好
   - 用户反馈驱动迭代
```