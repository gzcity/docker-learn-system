# Docker 源码架构

> 理解 Docker 各核心组件的源码架构和协作关系。

## 架构总览

```
┌─────────────────────────────────────────────────┐
│          Docker CLI / API Clients                │
├─────────────────────────────────────────────────┤
│                    dockerd                        │
│    (Docker 守护进程，API 网关 + 编排 + 管理)        │
├──────────┬──────────┬──────────┬─────────────────┤
│          │          │          │                  │
│  containerd       │  Network  │  Volume          │
│  (容器生命周期)    │  (libnetwork) │  (存储卷)       │
│          │          │          │                  │
│  ┌───────┴────┐    │          │                  │
│  │ containerd-│    │          │                  │
│  │ shim       │    │          │                  │
│  └───────┬────┘    │          │                  │
│          │         │          │                  │
│     ┌────┴──┐     │          │                  │
│     │ runc  │     │          │                  │
│     └───┬───┘     │          │                  │
│         │         │          │                  │
│    ┌────┴────┐    │          │                  │
│    │ 容器进程  │    │          │                  │
│    └─────────┘    │          │                  │
└───────────────────┴──────────┴──────────────────┘
```

---

## dockerd (Docker 守护进程)

### 是什么
dockerd 是 Docker 的核心守护进程，负责接收 API 请求、管理容器生命周期、镜像管理、网络和存储。

### 职责
- **API 网关**: 接收 Docker CLI 和 REST API 请求
- **容器编排**: 创建、启动、停止、删除容器
- **镜像管理**: 拉取、构建、推送镜像
- **网络管理**: 通过 libnetwork 管理容器网络
- **存储管理**: 管理卷和数据持久化
- **插件管理**: 加载和管理插件

### 源码位置
- `cmd/dockerd/` — 入口
- `daemon/` — 核心逻辑
- `api/server/` — API 服务
- `cli/` — CLI 命令

### 关键源码路径
- `daemon/daemon.go` — 守护进程初始化
- `daemon/create.go` — 容器创建
- `daemon/start.go` — 容器启动
- `daemon/stop.go` — 容器停止
- `daemon/wait.go` — 等待容器退出

---

## containerd

### 是什么
containerd 是一个工业级容器运行时，管理容器的完整生命周期（创建、启动、停止、删除）。它被 Docker 捐赠给 CNCF，是 Docker 的底层容器管理组件。

### 架构
```
containerd
├── API (gRPC)
├── Services
│   ├── Namespaces Service
│   ├── Containers Service
│   ├── Tasks Service
│   ├── Images Service
│   └── Snapshots Service
├── Runtime
│   ├── v1 (基于 runc)
│   └── v2 (基于 shim v2)
└── Metadata Store (boltdb)
```

### 源码位置
- `containerd/` — Docker 仓库中的 containerd 集成
- `vendor/github.com/containerd/containerd/` — containerd 源码

### 关键概念
- containerd 不是 Docker 专属，它可以被任何容器平台使用（Kubernetes 通过 CRI 调用）
- containerd 实现了 CRI (Container Runtime Interface)
- 它通过 shim 进程与 runc 交互

---

## runc

### 是什么
runc 是 OCI (Open Container Initiative) 运行时规范的参考实现，是一个轻量级的命令行工具，用于创建和运行容器。它是容器生命周期的最终执行者。

### 职责
- 基于 OCI bundle 创建容器
- 配置 namespaces 和 cgroups
- 执行容器进程
- 管理容器状态

### 源码位置
- `vendor/github.com/opencontainers/runc/` — runc 源码
- `libcontainer/` — 核心库

### 关键源码路径
- `libcontainer/container_linux.go` — 容器创建
- `libcontainer/process_linux.go` — 进程管理
- `libcontainer/cgroups/` — cgroups 配置
- `libcontainer/nsenter/` — 命名空间进入

### 关键误解
- **runc 一直运行着管理容器** ❌：runc 创建容器后即退出，由 shim 进程接管
- **runc 是 Docker 独有的** ❌：runc 是 OCI 规范的独立实现，可以在没有 Docker 的情况下使用
- **runc 只做容器运行** ❌：runc 还负责容器的暂停、恢复、执行命令等

---

## shim

### 是什么
shim 是 containerd 和 runc 之间的桥梁进程。它负责在 runc 退出后仍然保持容器的标准输入输出流，并上报容器状态。

### 为什么需要 shim
```
containerd → shim (保持 IO 流) → runc (创建容器后退出)
                                              ↓
                                        容器进程
```

- runc 创建容器后退出 → 需要 shim 保持 IO 连接
- shim 上报容器退出状态给 containerd
- shim 支持容器重启（不重建）

### 源码位置
- `containerd/shim/` — shim 实现
- 关注 `shim/service.go` 和 `shim/shim.go`

### 关键误解
- **shim 只负责 IO 转发** ❌：shim 还负责容器状态上报、退出码收集、支持容器重启等

---

## 调用链总结

| 操作 | 调用链 |
|------|--------|
| docker run | CLI → dockerd → containerd → shim → runc → 容器 |
| docker stop | CLI → dockerd → containerd → shim → runc → 信号 |
| docker exec | CLI → dockerd → containerd → shim → runc → 新进程 |
| docker logs | CLI → dockerd → containerd → shim → IO 读取 |