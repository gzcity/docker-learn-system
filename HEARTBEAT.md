# Docker 学习系统心跳

## 日常检查清单
- [ ] 检查 `memory/mastery.json` 是否正常
- [ ] 检查今日学习日志 `memory/YYYY-MM-DD.md`
- [ ] 检查是否有到期的复习项
- [ ] 检查用户是否连续多日未学习（需提醒）

## 文件结构
```
docker-learn-system/
├── learn.py              ← 主入口
├── engine/
│   ├── knowledge_graph.py  ← 知识图谱 + 掌握度 + 上下文
│   └── orchestrator.py     ← 编排器 + 意图识别 + 所有处理器
├── agents/                ← Agent 定义文档
├── docker-knowledge/      ← 知识图谱种子数据
├── questions/             ← 题库
├── personas/              ← 人格预设
├── memory/                ← 长期记忆 + 掌握度 + 日志
├── deploy/                ← Docker 部署方案
├── MEMORY.md              ← 长期记忆
├── README.md              ← 设计哲学
├── ARCHITECTURE.md        ← 技术架构
└── ROADMAP.md             ← 实现路线图
```

## 注
- 系统已通过所有 P0 测试 ✅
- 下一个里程碑：P1 — 深度研究 + 知识库管理