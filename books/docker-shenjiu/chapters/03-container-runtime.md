# 第 3 章：容器运行时深度剖析

> 从 runc 到 containerd，理解容器是如何真正被创建和运行的。

## 3.1 OCI runtime 规范

Open Container Initiative (OCI) 定义了三个核心规范：

| 规范 | 作用 | 关键文件 |
|------|------|---------|
| **runtime-spec** | 定义容器的生命周期和配置 | `config.json` |
| **image-spec** | 定义镜像格式 | OCI Image Format |
| **distribution-spec** | 定义镜像分发协议 | Registry API |

`config.json` 是容器运行的核心配置：

```json
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": true,
    "user": {"uid": 0, "gid": 0},
    "args": ["sh"],
    "env": ["PATH=/usr/local/bin"],
    "cwd": "/"
  },
  "root": {
    "path": "rootfs",
    "readonly": true
  },
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "network"},
      {"type": "mount"},
      {"type": "ipc"},
      {"type": "uts"}
    ],
    "resources": {
      "memory": {"limit": 536870912},
      "cpu": {"shares": 1024}
    }
  }
}
```

## 3.2 runc 的容器创建流程

runc 创建容器的核心流程：

```
1. 读取 config.json
        ↓
2. clone() 创建新进程（指定 namespaces）
        ↓
3. 设置 cgroups（CPU/内存/IO 限制）
        ↓
4. pivot_root 切换根文件系统
        ↓
5. exec() 启动容器入口程序
        ↓
6. runc 进程退出
```

关键系统调用：

```go
// 创建新 namespace 的进程
syscall.Syscall(syscall.SYS_CLONE, uintptr(flags), 0, 0)

// flags 包含:
// CLONE_NEWPID   — 新 PID namespace
// CLONE_NEWNET   — 新 network namespace
// CLONE_NEWNS    — 新 mount namespace
// CLONE_NEWIPC   — 新 IPC namespace
// CLONE_NEWUTS   — 新 UTS namespace
```

## 3.3 containerd 的架构

containerd 的插件化架构：

```
┌─────────────────────────────────────────────┐
│              containerd gRPC API             │
├─────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Content │ │  Snapshot│ │  Runtime │    │
│  │  Store   │ │  Plugin  │ │  Plugin  │    │
│  └──────────┘ └──────────┘ └──────────┘    │
├─────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Image   │ │ Container│ │  Task    │    │
│  │  Service │ │  Service │ │  Service │    │
│  └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
```

**核心概念：**

- **Content Store**: 存储不可变内容（镜像层、配置），通过内容寻址（SHA256）
- **Snapshotter**: 管理文件系统层，支持 overlayfs、btrfs、devicemapper 等
- **Task**: 运行中的容器进程，关联 runtime shim

## 3.4 shim 进程的生命周期

containerd-shim 是 containerd 和 runc 之间的关键桥梁：

```
containerd                    shim                     runc
    │                          │                        │
    │── Create container ─────→│                        │
    │                          │── runc create ────────→│
    │                          │                        │── fork + exec
    │                          │←── container PID ─────│
    │←── Container created ───│                        │ (runc 退出)
    │                          │                        │
    │── Start container ──────→│                        │
    │                          │── runc start ─────────→│
    │                          │                        │
    │                          │←── Container exited ──│
    │←── Exit code ───────────│                        │
    │                          │ (shim 继续运行)         │
```

**为什么需要 shim？**

1. **IO 接管**: runc 启动容器后就退出，shim 接管 stdin/stdout/stderr
2. **状态上报**: shim 等待容器进程退出，将 exit code 报告给 containerd
3. **热升级**: containerd 重启时，shim 保持容器运行不受影响
4. **资源清理**: 容器退出后，shim 负责清理相关资源

## 3.5 容器创建的完整链路

从 `docker run` 到容器进程启动：

```
docker run -it ubuntu bash
    │
    ▼
docker CLI → REST API → dockerd
    │
    ▼
dockerd: containerCreate()
    ├── 验证参数（image、config、hostConfig）
    ├── 拉取镜像（如果不存在）
    ├── 创建容器对象（分配 ID、设置配置）
    ├── 配置网络（创建 endpoint、加入 network sandbox）
    ├── 配置存储（挂载 volume、设置 rootfs）
    └── 调用 containerd Create()
            │
            ▼
containerd: Create Container
    ├── 创建 snapshot（基于镜像层）
    ├── 生成 config.json
    ├── 启动 shim 进程
    └── shim 调用 runc create
            │
            ▼
runc create
    ├── 读取 config.json
    ├── clone() 进入新 namespaces
    ├── 应用 cgroups 限制
    ├── pivot_root 切换 rootfs
    └── exec() 启动 bash
```

## 3.6 关键源码路径

| 组件 | 路径 | 核心文件 |
|------|------|---------|
| dockerd | `docker/daemon/` | `daemon.go`, `container.go` |
| containerd | `docker/containerd/` | `client.go`, `adapter.go` |
| runc | 外部依赖 | `github.com/opencontainers/runc` |
| libnetwork | `docker/libnetwork/` | `network.go`, `sandbox.go` |
| volume | `docker/volume/` | `store.go`, `drivers.go` |

---

> 📝 **下一步**: 第 4 章将深入 namespace 和 cgroups 的底层实现，包括 Linux 内核如何提供隔离机制。
