# Docker 容器基础

> 理解 Docker 的核心抽象：容器、镜像、层。

## 容器 (Container)

### 是什么
容器是一个轻量级、可移植的运行环境，包含应用及其所有依赖。它不是虚拟机，而是宿主机上的一个进程，通过 Linux 内核的 namespaces 和 cgroups 实现隔离和资源限制。

### 核心原理
```
容器 = 进程 + 隔离(namespaces) + 资源限制(cgroups) + 文件系统(overlay2)
```

- **namespaces**: 隔离进程视图（PID、网络、挂载点、用户等）
- **cgroups**: 限制资源使用（CPU、内存、IO）
- **联合文件系统**: 提供容器层叠的文件系统视图

### 源码位置
- `container/container.go` — 容器结构体定义
- `daemon/` — 容器生命周期管理
- `libcontainerd/` — 与 containerd 的交互

### 关键概念
- 容器是**进程级**隔离，不是**硬件级**隔离
- 所有容器共享宿主机内核
- 容器镜像提供文件系统，但容器运行时可写层是独立的

### 与虚拟机对比
| 维度 | 容器 | 虚拟机 |
|------|------|--------|
| 隔离级别 | 进程级(namespaces) | 硬件级(Hypervisor) |
| 内核 | 共享宿主机 | 独立内核 |
| 启动时间 | 毫秒级 | 秒级 |
| 资源占用 | MB 级 | GB 级 |
| 隔离性 | 较弱（共享内核） | 强（完全隔离） |

---

## 镜像 (Image)

### 是什么
镜像是容器的只读模板，包含运行应用所需的文件系统、库和配置。镜像由多层（Layer）组成，采用联合文件系统（UnionFS）技术。

### 镜像结构
```
镜像 = 基础层(base) + 修改层(修改/添加文件) + 配置层(CMD/ENTRYPOINT等)
```

### 源码位置
- `image/` — 镜像存储和管理
- `layer/` — 层管理
- `distribution/` — 镜像拉取和推送

### 关键概念
- 镜像是**只读**的，容器启动时在镜像层上添加可写层
- 镜像层是**共享**的，多个镜像可以共用基础层
- `docker pull` 按层下载，已有层跳过

---

## 层 (Layer)

### 是什么
层是 Docker 镜像的基本构建单元。每一层代表一组文件系统变更（添加、修改、删除文件）。层通过联合文件系统（overlay2/aufs）叠加，形成容器的完整文件系统视图。

### 层的工作原理
```
[容器可写层]  ← 容器运行时写入
[镜像层 n]    ← Dockerfile RUN/COPY/ADD
[镜像层 2]    ← Dockerfile 指令
[镜像层 1]    ← 基础镜像
```

### 源码位置
- `layer/` — 层管理（创建、挂载、提交）
- `daemon/graphdriver/` — 存储驱动（overlay2、aufs 等）

### 关键误解
- **删除文件不会减小镜像大小**：删除操作只是在当前层创建一个"白障文件"（whiteout），标记该文件被删除，但底层文件仍然存在。要真正减小大小，需要重建镜像。
- **Dockerfile 每行都产生层**：不一定。`RUN`、`COPY`、`ADD` 产生层，但 `ENV`、`LABEL`、`EXPOSE` 等元数据指令不产生新层，只修改镜像配置。

---

## 容器创建流程

### 完整流程
```
docker run → dockerd → containerd → containerd-shim → runc → 容器进程
```

### 步骤分解
1. **dockerd** 接收 API 请求，解析镜像和配置
2. **dockerd** 调用 containerd 创建容器
3. **containerd** 准备容器运行时环境（镜像挂载、网络配置）
4. **containerd** 启动 shim 进程
5. **shim** 调用 runc 创建和启动容器
6. **runc** 配置 namespaces、cgroups，执行容器进程

### 源码路径
- `daemon/create.go` → `containerd/` → `runtime/` → `runc/libcontainer/`

---

## 容器状态机

### 状态定义
```
created → running → paused
  ↓         ↓
stopped ← exited
```

### 关键状态
- **created**: 容器已创建但未启动
- **running**: 容器正在运行
- **paused**: 容器进程暂停（freezer cgroup）
- **exited**: 容器主进程退出
- **dead**: 容器异常状态

### 源码位置
- `container/state.go` — 状态机定义
- `daemon/start.go` — 启动流程
- `daemon/stop.go` — 停止流程
- `daemon/pause.go` — 暂停/恢复