# 第 1 章：Docker 架构总览

> 从万米高空俯瞰 Docker 的整体架构，理解各组件如何协作。

## 1.1 Docker 不是什么？

在深入源码之前，我们需要先破除一个常见的误解：**Docker 不是单一的容器运行时**。

Docker 是一个**容器管理平台**，它由多个独立的组件组成：

```
┌─────────────────────────────────────────────────────┐
│                    Docker CLI                        │
├─────────────────────────────────────────────────────┤
│                   dockerd (API)                      │
├──────────┬──────────┬──────────┬────────────────────┤
│          │          │          │                     │
│ containerd        │ network  │  volumes             │
│ (容器管理) │  (libnetwork) │  (存储)     │
│          │          │          │                     │
│ shim     │          │          │                     │
│          │          │          │                     │
│ runc     │          │          │                     │
└──────────┴──────────┴──────────┴─────────────────────┘
```

## 1.2 各组件职责

### dockerd — 大脑
- 负责所有 API 请求
- 管理镜像、网络、卷
- 调用 containerd 管理容器

### containerd — 容器管家
- 管理容器生命周期（创建、启动、停止、删除）
- 管理镜像拉取和存储
- 被 CNCF 托管，可供 K8s 直接使用

### runc — 最后的执行者
- OCI 运行时规范实现
- 创建容器的 namespaces 和 cgroups
- 启动容器进程后退出

### shim — 桥梁
- 在 runc 退出后保持 IO 连接
- 上报容器状态
- 支持容器重启

## 1.3 关键设计思想

### 分层解耦
每个组件专注于自己的职责：
- dockerd 不直接创建容器
- containerd 不直接操作内核
- runc 只关心创建和运行

### 标准接口
- **CRI** (Container Runtime Interface): containerd 与 K8s 的接口
- **OCI** (Open Container Initiative): runc 遵循的规范
- **gRPC**: containerd 与 dockerd/shim 的通信协议

## 1.4 源码入口

要开始阅读 Docker 源码，推荐按以下顺序：

1. `cmd/dockerd/docker.go` — dockerd 入口
2. `daemon/daemon.go` — 守护进程初始化
3. `containerd/` — containerd 集成
4. `vendor/github.com/opencontainers/runc/` — runc 源码

---

**思考题**：为什么 Docker 要把容器管理功能拆分到 containerd 中？这样的设计带来了什么好处？