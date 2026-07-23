# Docker 源码知识图谱 — 核心概念定义

> 这是知识图谱的种子数据。每个概念节点包含定义、关联概念、代码引用和初始难度设定。

---

## 基础概念层

### 容器 (Container)

- **English**: Container
- **定义**：一个轻量级、可移植的运行环境，包含应用及其依赖。Docker 的核心抽象。
- **关联概念**：`镜像` → `容器运行时` → `操作系统虚拟化`
- **前置知识**：`Linux 进程` → `文件系统`
- **代码引用**：`container/container.go`
- **初始难度**：1/5
- **English definition**: A lightweight, portable runtime environment that packages an application with its dependencies. Docker's core abstraction.
- **关键源码**：
  ```go
  // container/container.go
  type Container struct {
      ID              string
      Name            string
      Config          *container.Config
      State           *container.State
      ImageID         image.ID
  }
  ```
- **常见误解 (Misconceptions)**：
  - **"容器就是轻量级虚拟机" / "Container is a lightweight VM"** ❌  
    纠正：容器共享宿主机内核（通过 namespaces 隔离视图，cgroups 限制资源），虚拟机通过 Hypervisor 虚拟化硬件，每个 VM 有独立内核。区别是本质性的，不是"程度的差异"。
    Correction: Containers share the host kernel (namespace isolation, cgroup resource limits), while VMs virtualize hardware via Hypervisor with independent kernels. The difference is fundamental.
  - **"容器内能看到宿主机所有进程" / "Container can see all host processes"** ❌  
    纠正：通过 PID namespace 隔离，容器内只能看到自己的进程树。
    Correction: PID namespace isolation ensures containers only see their own process tree.
  - **"容器必须有操作系统" / "Container needs its own OS"** ❌  
    纠正：容器共享宿主机内核，不需要自己的 OS。`FROM ubuntu` 提供的只是用户空间工具。
    Correction: Containers share the host kernel. `FROM ubuntu` only provides userspace tools.

### 镜像 (Image)

- **English**: Image
- **定义**：一个只读模板，包含创建容器的指令。基于 UnionFS 的分层结构。
- **English definition**: A read-only template with instructions for creating containers. Layered structure based on UnionFS.
- **关联概念**：`容器` → `层` → `Dockerfile`
- **前置知识**：`文件系统` → `UnionFS`
- **代码引用**：`image/image.go`
- **初始难度**：1/5
- **关键源码**：
  ```go
  // image/image.go
  type Image struct {
      ID              ID
      Descriptor      ocispec.Descriptor
      Created         time.Time
      OS              string
      ...
  }
  ```
- **常见误解 (Misconceptions)**：
  - **"镜像就是一个完整的操作系统" / "Image is a complete OS"** ❌  
    纠正：镜像只包含用户空间的文件和工具，不包含内核。容器运行时共享宿主机内核。
    Correction: Images only contain userspace files and tools, not the kernel.
  - **"Dockerfile 的每一行命令都产生一个层" / "Every Dockerfile command creates a layer"** ❌  
    纠正：`RUN`、`COPY`、`ADD` 会创建新层。`CMD`、`EXPOSE`、`ENV` 等不创建层。
    Correction: Only `RUN`, `COPY`, `ADD` create layers. Metadata instructions don't.
  - **"镜像越大，容器启动越慢" / "Larger image = slower startup"** ❌  
    纠正：启动速度取决于需要拉取的新层数量，而非镜像总大小。
    Correction: Startup speed depends on new layers to pull, not total image size.

### 层 (Layer)

- **English**: Layer
- **定义**：镜像的增量修改单元。每个层是只读的，多个层叠加形成完整文件系统。
- **English definition**: Incremental modification unit of an image. Each layer is read-only; multiple layers stack to form the complete filesystem.
- **关联概念**：`镜像` → `存储驱动`
- **前置知识**：`UnionFS` → `写时复制`
- **代码引用**：`layer/layer.go`
- **初始难度**：2/5
- **常见误解 (Misconceptions)**：
  - **"删除一个文件会减小镜像大小" / "Deleting a file reduces image size"** ❌  
    纠正：`RUN rm file.txt` 只是在上层创建一个"该文件已被删除"的标记（whiteout 文件），被删除的文件仍然存在于下层。镜像大小不会减小，反而可能增加。
    Correction: `RUN rm file.txt` creates a whiteout marker. The deleted file still exists in lower layers.
  - **"层的顺序不重要" / "Layer order doesn't matter"** ❌  
    纠正：层是有序叠加的，上层文件覆盖下层同名文件。顺序颠倒会导致不同的文件系统状态。
    Correction: Layers are stacked in order. Upper layers override lower layers with the same filename.

### 容器运行时 (Container Runtime)

- **English**: Container Runtime
- **定义**：负责管理容器生命周期的软件组件。Docker 使用 containerd + runc 的架构。
- **English definition**: Software component responsible for managing container lifecycle. Docker uses the containerd + runc architecture.
- **关联概念**：`容器` → `containerd` → `runc` → `shim`
- **前置知识**：`Linux 进程` → `cgroups` → `namespaces`
- **代码引用**：`daemon/`、`containerd`、`runc`
- **初始难度**：3/5
- **常见误解 (Misconceptions)**：
  - **"Docker 就是容器运行时"** ❌  
    纠正：Docker 是一个完整的容器平台（CLI + API + 管理面）。容器运行时是 containerd/runc 这样的底层组件。Docker 使用 containerd 作为运行时，但 containerd 也可以被 Kubernetes 直接使用，不需要 Docker。
  - **"runc 直接创建容器进程"** ❌  
    纠正：runc 创建容器后立即退出，容器进程由 shim 接管。runc 的职责是"配置和启动"，不是"持续管理"。
  - **"容器运行时只负责启动和停止容器"** ❌  
    纠正：容器运行时还负责镜像挂载、网络配置、资源限制、日志管理、进程监控等完整生命周期管理。

---

## 核心架构层

### dockerd (Docker 守护进程)

- **English**: dockerd (Docker Daemon)
- **定义**：Docker 的后台服务进程，处理 API 请求，管理容器生命周期。
- **English definition**: Docker's background service process that handles API requests and manages container lifecycle.
- **关联概念**：`Docker API` → `containerd` → `容器管理`
- **前置知识**：`HTTP API` → `进程管理`
- **代码引用**：`cmd/dockerd/dockerd.go`
- **初始难度**：3/5
- **关键源码**：
  ```go
  // cmd/dockerd/dockerd.go
  func main() {
      // 初始化守护进程配置
      // 启动 API 服务器
      // 连接到 containerd
  }
  ```
- **常见误解 (Misconceptions)**：
  - **"dockerd 直接管理容器" / "dockerd manages containers directly"** ❌  
    纠正：dockerd 通过 containerd 间接管理容器。dockerd 是管理面，containerd 是运行时面，runc 是执行面。dockerd 崩溃不影响正在运行的容器。
    Correction: dockerd manages containers indirectly through containerd. A dockerd crash doesn't affect running containers.
  - **"dockerd 重启会杀死所有容器" / "Restarting dockerd kills all containers"** ❌  
    纠正：dockerd 重启时会执行 restore 流程，重新连接到已有容器的 shim 进程。
    Correction: dockerd restores connections to existing shim processes on restart.

### containerd

- **English**: containerd
- **定义**：行业标准的容器运行时，管理容器的完整生命周期。
- **English definition**: Industry-standard container runtime managing the full container lifecycle.
- **关联概念**：`dockerd` → `runc` → `CRI`
- **前置知识**：`gRPC` → `容器运行时`
- **代码引用**：独立项目 `containerd/containerd`
- **初始难度**：4/5
- **常见误解 (Misconceptions)**：
  - **"containerd 是 Docker 专属的" / "containerd is Docker-only"** ❌  
    纠正：containerd 是 CNCF 毕业项目，被 Kubernetes、Docker、Podman 等多个平台使用。
    Correction: containerd is a CNCF graduated project used by Kubernetes, Docker, Podman, and more.
  - **"containerd 和 dockerd 是竞争关系" / "containerd and dockerd compete"** ❌  
    纠正：containerd 是运行时层，dockerd 是管理面层，属于不同抽象层次。
    Correction: They operate at different abstraction layers — runtime vs management plane.

### runc

- **English**: runc
- **定义**：OCI 运行时规范实现，负责实际创建和运行容器进程。
- **English definition**: OCI runtime specification implementation responsible for creating and running container processes.
- **关联概念**：`containerd` → `cgroups` → `namespaces` → `OCI 规范`
- **前置知识**：`cgroups` → `namespaces` → `Linux 系统调用`
- **代码引用**：独立项目 `opencontainers/runc`
- **初始难度**：4/5
- **关键流程**：
  ```
  runc create → 创建 cgroups 和 namespaces
             → 准备 rootfs
             → 启动 init 进程
  runc start → 执行容器内的用户进程
  ```
- **常见误解 (Misconceptions)**：
  - **"runc 是 Docker 开发的" / "runc is developed by Docker"** ❌  
    纠正：runc 是 OCI 的参考实现，由 Docker、Red Hat、Google 等共同维护。
    Correction: runc is the OCI reference implementation, co-maintained by Docker, Red Hat, Google.
  - **"runc 一直运行着管理容器" / "runc keeps running to manage containers"** ❌  
    纠正：runc 完成容器创建和启动后立即退出，由 shim 接管。
    Correction: runc exits after creating/starting the container. The shim takes over.
  - **"runc 用 Go 的 os/exec 启动进程" / "runc uses os/exec to start processes"** ❌  
    纠正：runc 使用 `syscall.Exec`（`execve` 系统调用），直接将当前进程替换为目标进程，确保 PID 1 身份。
    Correction: runc uses `syscall.Exec` (the `execve` syscall), replacing itself with the target process to ensure PID 1 status.

### shim

- **English**: shim
- **定义**：containerd 和 runc 之间的中间层，允许 runc 退出后容器继续运行。
- **English definition**: The intermediary layer between containerd and runc, allowing containers to continue running after runc exits.
- **关联概念**：`containerd` → `runc` → `容器运行时`
- **前置知识**：`进程管理` → `信号处理`
- **代码引用**：`containerd/shim/`
- **初始难度**：3/5
- **常见误解 (Misconceptions)**：
  - **"shim 是多余的，runc 可以直接管理容器" / "shim is redundant"** ❌  
    纠正：shim 的关键作用是让 runc 可以安全退出，防止 runc 崩溃导致容器丢失。
    Correction: The shim allows runc to exit safely, preventing container loss on runc crashes.
  - **"shim 只负责 IO 转发" / "shim only forwards I/O"** ❌  
    纠正：shim 还负责退出码收集、状态报告、信号代理。
    Correction: The shim also handles exit code collection, state reporting, and signal proxying.

---

## 容器管理

### 容器创建流程 (Container Creation Flow)

- **English**: Container Creation Flow
- **定义**：从 API 请求到容器进程启动的完整代码路径。
- **English definition**: The complete code path from API request to container process startup.
- **关联概念**：`Docker API` → `dockerd` → `containerd` → `runc`
- **前置知识**：`容器运行时` → `HTTP API`
- **代码路径**：
  ```
  POST /containers/create
  → api/server/router/container/
  → daemon/create.go
  → daemon/container_operations.go
  → containerd client
  → runc
  ```
- **初始难度**：4/5

### 容器状态机 (Container State Machine)

- **English**: Container State Machine
- **定义**：容器的状态转换模型，包括 Created、Running、Paused、Exited 等。
- **English definition**: The state transition model for containers, including Created, Running, Paused, Exited states.
- **关联概念**：`容器` → `容器生命周期`
- **前置知识**：`状态机` → `容器管理`
- **代码引用**：`container/state.go`
- **初始难度**：3/5
- **关键源码**：
  ```go
  // container/state.go
  type State struct {
      Running    bool
      Paused     bool
      Restarting bool
      ExitCode   *int
      ...
  }
  ```

---

## 镜像管理

### 镜像拉取流程 (Image Pull Flow)

- **English**: Image Pull Flow
- **定义**：从注册中心拉取镜像到本地存储的完整流程。
- **English definition**: The complete flow of pulling an image from a registry to local storage.
- **关联概念**：`镜像` → `层` → `注册中心` → `distribution`
- **前置知识**：`HTTP` → `镜像层`
- **代码路径**：
  ```
  docker pull → distribution/
  → 认证 → 清单获取 → 层下载 → 层验证 → 存储
  ```
- **初始难度**：3/5

### 镜像构建流程 (Image Build Flow)

- **English**: Image Build Flow
- **定义**：从 Dockerfile 构建镜像的流程，包括每一步的层创建。
- **English definition**: The process of building an image from a Dockerfile, including layer creation at each step.
- **关联概念**：`镜像` → `Dockerfile` → `builder`
- **前置知识**：`镜像层` → `缓存机制`
- **代码引用**：`builder/builder.go`
- **初始难度**：3/5

---

## 网络与存储

### 网络模型 (Network Model)

- **English**: Network Model
- **定义**：Docker 的网络抽象，包括 bridge、overlay、host、macvlan 等驱动。
- **English definition**: Docker's network abstraction, including bridge, overlay, host, macvlan drivers.
- **关联概念**：`容器` → `网络命名空间` → `iptables`
- **前置知识**：`Linux 网络` → `网络命名空间` → `iptables`
- **代码引用**：`network/`
- **初始难度**：4/5

### 存储驱动 (Storage Driver)

- **English**: Storage Driver
- **定义**：Docker 使用的存储后端，如 overlay2、aufs、devicemapper 等。
- **English definition**: The storage backend used by Docker, such as overlay2, aufs, devicemapper.
- **关联概念**：`层` → `镜像` → `文件系统`
- **前置知识**：`UnionFS` → `写时复制` → `文件系统`
- **代码引用**：`daemon/graphdriver/`
- **初始难度**：4/5

---

## 高级主题

### 插件系统 (Plugin System)

- **English**: Plugin System
- **定义**：Docker 的插件扩展机制，支持网络、存储、认证等插件。
- **English definition**: Docker's plugin extension mechanism supporting network, storage, and authentication plugins.
- **关联概念**：`网络` → `存储` → `认证`
- **前置知识**：`Go plugin` → `RPC`
- **代码引用**：`plugin/`
- **初始难度**：5/5

### Swarm 集群 (Swarm Cluster)

- **English**: Swarm Cluster
- **定义**：Docker 的原生集群管理方案，服务编排和集群管理。
- **English definition**: Docker's native cluster management solution for service orchestration.
- **关联概念**：`容器` → `服务发现` → `负载均衡`
- **前置知识**：`分布式系统` → `Raft` → `服务发现`
- **代码引用**：`swarm/`
- **初始难度**：5/5

---

## 概念关系图

```
镜像层模型 ───→ 存储驱动 ───→ overlay2
    │
    ├──→ 镜像 ───→ Dockerfile
    │
    ├──→ 镜像拉取 ──→ 注册中心 ──→ distribution
    │
    └──→ 镜像构建 ──→ builder

容器 ───→ 容器运行时 ───→ containerd ───→ runc ───→ shim
    │            │
    │            └──→ OCI 规范 ──→ OCI 镜像规范
    │
    ├──→ 容器状态机 ───→ 容器生命周期
    │
    ├──→ 容器创建流程 ──→ dockerd
    │
    ├──→ 网络模型 ───→ bridge ──→ overlay ──→ host
    │
    └──→ 存储卷 ───→ volume ──→ mount

dockerd ───→ Docker API ───→ HTTP API
    │
    └──→ daemon ───→ 容器管理 ──→ 镜像管理 ──→ 网络管理
```