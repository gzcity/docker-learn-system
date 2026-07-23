# Docker 源码学习 — 题库示例

> 前 14 道核心题目的示例。完整题库会动态扩展。

---

## 基础概念题

### Q001: 容器 vs 虚拟机

**类型**：选择题（单选）
**概念**：`容器` → `操作系统虚拟化`
**难度**：0.2
**前置知识**：无

**题目**：
Docker 容器与虚拟机的主要区别是什么？

A. 容器共享宿主机内核，虚拟机有独立内核
B. 容器比虚拟机更安全
C. 容器只能运行 Linux 应用
D. 容器不需要文件系统

**正确答案**：A
**解析**：容器与宿主机共享内核，通过 cgroups 和 namespaces 实现隔离；虚拟机通过 Hypervisor 虚拟化硬件，每个 VM 有独立内核。这是两者最根本的区别。

---

### Q002: 镜像分层

**类型**：选择题（单选）
**概念**：`镜像` → `层`
**难度**：0.3
**前置知识**：`镜像`

**题目**：
Docker 镜像采用分层结构的主要目的是什么？

A. 提高安全性
B. 提高构建速度，节省存储空间
C. 支持多架构
D. 兼容不同操作系统

**正确答案**：B
**解析**：分层结构允许层复用。当多个镜像基于同一基础层时，该层只需存储一次。构建时，未变化的层可复用缓存，大幅提升构建速度。

---

### Q003: 容器运行时组件

**类型**：选择题（多选）
**概念**：`容器运行时`
**难度**：0.4
**前置知识**：`容器`

**题目**：
以下哪些组件属于 Docker 的容器运行时栈？（多选）

A. containerd
B. runc
C. dockerd
D. shim
E. kubelet

**正确答案**：A, B, D
**解析**：Docker 运行时栈为：dockerd → containerd → shim → runc。其中 containerd、runc、shim 属于容器运行时范畴。kubelet 是 Kubernetes 的组件。

---

## 源码分析题

### Q004: Container 结构体

**类型**：代码填空题
**概念**：`容器` → `container/container.go`
**难度**：0.5
**前置知识**：`Go 结构体` → `容器`

**题目**：
补全以下 Docker 源码中 Container 结构体的字段：

```go
// container/container.go
type Container struct {
    ID              string
    Name            string
    Config          *container.Config
    State           *container.State
    ImageID         image.ID
    // 请补全下面缺失的字段
    _____________  *daemon.Monitor
    _____________  map[string]string
    _____________  container.Store
}
```

**正确答案**：Monitor, HostConfig, Store
**解析**：Container 结构体还包含 Monitor（监控进程）、HostConfig（主机配置）、Store（容器存储）等关键字段，共同管理容器的完整生命周期。

---

### Q005: 容器创建流程

**类型**：排序题
**概念**：`容器创建流程`
**难度**：0.6
**前置知识**：`容器运行时`

**题目**：
将以下容器创建事件按正确顺序排列：

1. runc 创建容器进程
2. containerd 接收创建请求
3. dockerd 解析 API 请求
4. shim 监控容器状态
5. 用户发送 POST /containers/create

**正确答案**：5 → 3 → 2 → 1 → 4
**解析**：用户通过 API 发起请求，dockerd 解析后调用 containerd，containerd 通过 shim 调用 runc 创建进程，shim 持续监控容器状态。

---

### Q006: State 结构体

**类型**：代码分析题
**概念**：`容器状态机` → `container/state.go`
**难度**：0.5
**前置知识**：`Go 结构体`

**题目**：
阅读以下代码，分析 `State` 结构体中各字段的作用：

```go
type State struct {
    Running    bool
    Paused     bool
    Restarting bool
    ExitCode   *int
    StartedAt  time.Time
    FinishedAt time.Time
}
```

问题：为什么 `ExitCode` 使用指针类型 `*int` 而不是 `int`？

**正确答案**：指针类型 `*int` 可以表示"未退出"状态（nil），而 `int` 的零值 0 会被误认为是正常退出码。当容器还在运行时，ExitCode 为 nil，表示尚未退出。

---

### Q007: Daemon 初始化

**类型**：代码分析题
**概念**：`dockerd` → `daemon`
**难度**：0.7
**前置知识**：`Go 并发` → `容器运行时`

**题目**：
以下代码来自 Docker 守护进程的初始化流程：

```go
func (daemon *Daemon) start() error {
    // 1. 恢复容器状态
    // 2. 初始化网络
    // 3. 启动容器监控
    // 4. 注册监控指标
    // 5. 启动 API 服务器
}
```

问题：为什么需要先"恢复容器状态"（restore）？这个过程中如果某个容器之前是 running 状态，dockerd 会如何处理？

**正确答案**：dockerd 重启时，需要恢复之前管理的容器状态。"恢复"过程会遍历本地存储的容器元数据，对于之前状态为 running 的容器，dockerd 会尝试重新连接到其 shim 进程（如果容器仍在运行），或将其状态更新为 exited。这保证了 dockerd 重启不影响正在运行的容器。

---

## 概念辨析题

### Q008: cgroups 与 namespaces

**类型**：概念辨析题
**概念**：`cgroups` → `namespaces`
**难度**：0.6
**前置知识**：`Linux 内核`

**题目**：
cgroups 和 namespaces 都是 Linux 内核提供的容器隔离机制，它们的作用分别是什么？请用一句话概括各自的职责，并说明为什么两者缺一不可。

**参考答案**：namespaces 负责"隔离视野"——让进程只能看到自己的资源视图（PID、网络、挂载点等）；cgroups 负责"限制用量"——控制进程能使用的资源上限（CPU、内存、磁盘 IO 等）。两者缺一不可，只有 namespaces 没有 cgroups，一个容器可以耗尽宿主机所有资源；只有 cgroups 没有 namespaces，进程之间没有隔离，可以互相看到和干扰。

---

### Q009: overlay2 vs aufs

**类型**：概念辨析题
**概念**：`存储驱动` → `overlay2` → `aufs`
**难度**：0.7
**前置知识**：`层` → `UnionFS`

**题目**：
Docker 支持多种存储驱动，其中 overlay2 是目前推荐的默认驱动，而 aufs 是早期版本常用的驱动。请从以下角度对比两者：

1. 内核支持要求
2. 性能特点
3. inode 使用
4. Docker 官方推荐度

**参考答案**：
1. 内核支持：overlay2 需要 Linux 4.0+（推荐 4.9+），aufs 需要内核打了 aufs 补丁（非主线）
2. 性能：overlay2 在页面缓存方面有优势，aufs 在层数较多时可能更高效
3. inode 使用：overlay2 在大量层时 inode 消耗较高，aufs 相对更节省
4. 官方推荐：overlay2 是 Docker 官方推荐的首选驱动，aufs 已标记为废弃

---

## 架构设计题

### Q010: 为什么 containerd 从 Docker 中分离？

**类型**：架构设计题（开放题）
**概念**：`containerd` → `Docker 架构`
**难度**：0.8
**前置知识**：`容器运行时`

**题目**：
2017 年，Docker 将 containerd 捐赠给 CNCF，成为一个独立项目。请分析：

1. 这个决策背后的技术原因是什么？
2. 对 Docker 的架构有什么影响？
3. 对容器生态系统有什么影响？

**参考答案**：
1. 技术原因：将容器运行时标准化，让 Kubernetes 等编排系统可以直接对接 containerd，而无需依赖 Docker 守护进程。这降低了系统耦合度，提高了稳定性。
2. 架构影响：Docker 从"大而全"的架构拆分为 dockerd（管理面）+ containerd（运行时）+ runc（底层执行）的三层架构。dockerd 专注于用户体验和 API 管理，运行时职责下放。
3. 生态系统影响：促进了 OCI 标准的发展，其他容器工具（如 Podman、CRI-O）也能基于 containerd 或 runc 构建，形成了开放的容器运行时生态。

---

### Q011: Docker 网络模型设计

**类型**：架构设计题
**概念**：`网络模型`
**难度**：0.7
**前置知识**：`Linux 网络`

**题目**：
Docker 支持 bridge、overlay、host、macvlan、none 五种网络驱动。请设计一个决策树，帮助用户根据场景选择合适的网络模式。

**参考答案**（决策树）：
```
是否需要跨主机通信？
├── 是 → overlay 网络（Swarm 或 Docker 网络）
└── 否 → 是否需要端口映射？
    ├── 是 → bridge 网络（默认模式）
    └── 否 → 是否需要高性能网络？
        ├── 是 → host 网络（直接使用宿主机网络栈）
        └── 否 → 是否需要 MAC 地址？
            ├── 是 → macvlan（直接暴露到物理网络）
            └── 否 → bridge 网络
```

---

## 高级挑战题

### Q012: runc 的 init 流程

**类型**：代码分析题（高级）
**概念**：`runc` → `容器生命周期`
**难度**：0.9
**前置知识**：`Linux 系统调用` → `Go 汇编`

**题目**：
runc 在创建容器时，会执行一个特殊的 init 进程。这个进程在 runc 退出后仍然存在，直到容器被停止。请分析：

1. init 进程的入口在哪里？
2. init 进程做了哪些关键操作？
3. 为什么 runc 需要先 fork 一个子进程，再让子进程执行 init？

**参考答案**：
1. 入口在 `runc/libcontainer/init_linux.go` 中的 `Init()` 函数
2. 关键操作：设置 cgroups 限制、创建/加入 namespaces、挂载 rootfs、设置 capabilities、执行 seccomp 规则、最后通过 `execve` 系统调用切换到容器内的用户进程
3. 需要 fork 子进程的原因：runc 需要在子进程中完成所有 namespace 和 cgroup 的配置，然后子进程通过 `execve` 替换为容器内的进程。这样 runc 父进程可以安全退出，而子进程（通过 shim 接管）继续运行。

---

### Q013: 镜像构建缓存策略

**类型**：设计与分析题
**概念**：`镜像构建` → `builder`
**难度**：0.8
**前置知识**：`镜像层`

**题目**：
Docker 构建镜像时会使用缓存层来加速。假设有以下 Dockerfile：

```dockerfile
FROM golang:1.20 AS builder
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o app

FROM alpine:3.18
COPY --from=builder /app /app
CMD ["/app"]
```

问题：如果修改了 `main.go` 中的一行代码，哪些层会命中缓存，哪些层会失效？如果修改了 `go.mod` 添加了一个依赖呢？

**参考答案**：
- 修改 `main.go`：COPY go.mod/go.sum 和 RUN go mod download 层命中缓存，COPY . . 层失效（因为 `main.go` 改变了），后续所有层都失效
- 修改 `go.mod`：COPY go.mod/go.sum 层失效（文件 checksum 改变），后续所有层都失效

这就是"先复制依赖文件再下载，再复制源码"的排序策略的原因——最大化缓存命中率。

---

### Q014: 综合源码分析

**类型**：综合题
**概念**：`容器创建` → `runc` → `daemon`
**难度**：0.9
**前置知识**：`Go 并发` → `容器运行时`

**题目**：
以下代码是 Docker 的 daemon 创建容器的简化版本：

```go
func (daemon *Daemon) containerCreate(params types.ContainerCreateConfig) (container.Container, error) {
    if err := daemon.verifyContainerSettings(params); err != nil {
        return nil, err
    }
    c, err := daemon.newContainer(params)
    if err != nil {
        return nil, err
    }
    if err := daemon.setupContainerNetwork(c); err != nil {
        return nil, err
    }
    if err := daemon.setupContainerMounts(c); err != nil {
        return nil, err
    }
    return c, nil
}
```

问题：
1. 为什么 `setupContainerNetwork` 在 `newContainer` 之后调用？
2. 如果 `setupContainerMounts` 失败，已经设置的网络如何处理？
3. 这个函数返回后，容器在运行了吗？

**参考答案**：
1. `newContainer` 创建容器对象并分配 ID，后续网络和存储配置需要容器 ID 作为标识。
2. 这里存在资源泄漏风险。理想情况下应该使用 defer 或错误处理来回滚。实际源码中使用了清理机制。
3. 没有运行。返回后容器处于 Created 状态。启动需要单独调用 start 接口。这是"创建"和"启动"分离的设计。

---

## 新增扩展题目

### Q015: cgroups 资源限制

**类型**：选择题（单选）
**概念**：`cgroups` → `容器运行时`
**难度**：0.4
**前置知识**：`容器`

**题目**：
cgroups 在 Docker 中主要用于实现什么功能？

A. 限制容器可以使用的 CPU、内存等资源
B. 提供容器的网络通信能力
C. 管理容器的文件系统挂载
D. 加密容器间的数据传输

**正确答案**：A
**解析**：cgroups（Control Groups）是 Linux 内核功能，用于限制、记录和隔离进程组的资源使用（CPU、内存、磁盘 I/O 等）。Docker 利用 cgroups 实现容器的资源限制。

---

### Q016: namespaces 隔离

**类型**：判断题
**概念**：`namespaces` → `容器运行时`
**难度**：0.3
**前置知识**：`容器`

**题目**：
Linux namespaces 可以隔离容器的进程视图、网络栈和文件系统挂载点。

**正确答案**：正确
**解析**：Linux namespaces 提供多种隔离：PID namespace（进程视图）、Network namespace（网络栈）、Mount namespace（文件系统挂载）、UTS namespace（主机名）、IPC namespace（进程间通信）、User namespace（用户权限）。

---

### Q017: UnionFS 联合文件系统

**类型**：选择题（单选）
**概念**：`UnionFS` → `层`
**难度**：0.5
**前置知识**：`镜像`

**题目**：
UnionFS（联合文件系统）在 Docker 中的主要作用是什么？

A. 将多个目录合并为一个统一视图，实现分层存储
B. 提供容器间的网络通信
C. 加密镜像层内容
D. 管理容器的生命周期

**正确答案**：A
**解析**：UnionFS 将多个目录堆叠在一起，形成一个统一的文件系统视图。在 Docker 中，镜像的每一层是一个只读目录，UnionFS 将它们叠加，容器运行时在最上层添加可写层。

---

### Q018: Dockerfile 构建

**类型**：填空题
**概念**：`Dockerfile` → `构建`
**难度**：0.4
**前置知识**：`镜像`

**题目**：
Dockerfile 中用于指定基础镜像的关键字是 `____`，用于执行 shell 命令的关键字是 `____`。

**正确答案**：FROM, RUN
**解析**：FROM 指令指定基础镜像，必须是 Dockerfile 的第一条指令。RUN 指令在构建时执行命令并创建新的镜像层，常用于安装软件包。

---

### Q019: 镜像仓库 Registry

**类型**：选择题（单选）
**概念**：`镜像仓库` → `registry`
**难度**：0.5
**前置知识**：`镜像`

**题目**：
Docker Hub 和私有 Registry 的关系是什么？

A. Docker Hub 是公共的镜像仓库，私有 Registry 是企业内部的镜像存储
B. Docker Hub 是私有 Registry 的一种
C. 私有 Registry 必须与 Docker Hub 同步
D. 两者没有关系

**正确答案**：A
**解析**：Docker Hub 是 Docker 官方的公共镜像仓库，任何人都可以拉取公开镜像。私有 Registry 是企业或组织内部部署的镜像存储服务，用于存放私有镜像。

---

### Q020: 网络模型

**类型**：多选题
**概念**：`网络模型` → `bridge`
**难度**：0.6
**前置知识**：`容器`

**题目**：
Docker 支持以下哪些网络驱动？（多选）

A. bridge
B. host
C. overlay
D. nat

**正确答案**：A, B, C
**解析**：Docker 支持多种网络驱动：bridge（默认，容器通过虚拟网桥通信）、host（与宿主机共享网络栈）、overlay（跨主机容器通信）、macvlan（为容器分配 MAC 地址）、none（无网络）。

---

### Q021: Volume 存储卷

**类型**：选择题（单选）
**概念**：`Volume` → `存储卷`
**难度**：0.4
**前置知识**：`容器`

**题目**：
Docker Volume 与 bind mount 的主要区别是什么？

A. Volume 由 Docker 管理，bind mount 直接绑定宿主机路径
B. Volume 更快
C. Volume 只能在 Linux 上使用
D. bind mount 更安全

**正确答案**：A
**解析**：Volume 由 Docker 创建和管理，存储在 Docker 的数据目录中。bind mount 直接绑定宿主机的任意路径。Volume 更易备份和移植，不依赖宿主机目录结构。

---

### Q022: dockerd 守护进程

**类型**：判断题
**概念**：`dockerd` → `Docker 守护进程`
**难度**：0.3
**前置知识**：无

**题目**：
dockerd 是 Docker 的客户端命令行工具。

**正确答案**：错误
**解析**：dockerd 是 Docker 的后台守护进程（daemon），负责管理容器、镜像、网络和存储。Docker CLI（docker 命令）才是客户端工具，通过 REST API 与 dockerd 通信。

---

### Q023: containerd 运行时

**类型**：选择题（单选）
**概念**：`containerd` → `容器运行时`
**难度**：0.6
**前置知识**：`容器运行时`

**题目**：
containerd 在 Docker 架构中扮演什么角色？

A. 高级运行时，管理镜像传输和容器生命周期
B. 低级运行时，直接创建容器进程
C. 网络代理
D. 存储驱动

**正确答案**：A
**解析**：containerd 是高级容器运行时，负责镜像管理、容器生命周期管理、网络配置等。runc 是低级运行时，直接执行容器进程。Docker 架构：dockerd → containerd → shim → runc。

---

### Q024: runc OCI 实现

**类型**：填空题
**概念**：`runc` → `OCI`
**难度**：0.5
**前置知识**：`容器运行时`

**题目**：
runc 是 ____（组织）制定的 ____（标准）的参考实现。

**正确答案**：OCI, OCI Runtime Specification
**解析**：OCI（Open Container Initiative）是一个开放治理结构，OCI Runtime Specification 定义了容器运行时的配置和生命周期。runc 是该标准的 Go 语言参考实现。

---

### Q025: 容器创建流程

**类型**：排序题
**概念**：`容器创建` → `生命周期`
**难度**：0.7
**前置知识**：`容器运行时`, `dockerd`

**题目**：
请将以下容器创建步骤按正确顺序排列：

A. runc 创建容器进程
B. docker CLI 发送创建请求
C. containerd 创建 shim 进程
D. dockerd 验证参数并准备配置
E. shim 调用 runc

**正确顺序**：B → D → C → E → A
**解析**：1) CLI 发送请求到 dockerd；2) dockerd 验证参数并准备容器配置；3) containerd 创建 shim 进程；4) shim 调用 runc；5) runc 创建实际的容器进程（调用 clone() + exec()）。

---

### Q026: shim 进程作用

**类型**：简答题
**概念**：`shim` → `containerd`
**难度**：0.7
**前置知识**：`containerd`, `runc`

**题目**：
为什么 containerd 需要一个 shim 进程来管理容器？直接调用 runc 不行吗？

**参考答案**：
shim 进程的核心作用是解耦 containerd 和容器进程。当 runc 创建容器后，runc 进程会退出，此时容器进程变成了孤儿进程。shim 作为中间层：1) 接管容器进程的 stdin/stdout/stderr；2) 等待容器退出并报告 exit code；3) 使 containerd 可以热升级而不中断容器（因为 shim 保持运行）。如果 containerd 直接管理，runc 退出后 containerd 无法追踪容器状态。

---

### Q027: 镜像构建缓存

**类型**：选择题（单选）
**概念**：`构建缓存` → `Dockerfile`
**难度**：0.5
**前置知识**：`Dockerfile`

**题目**：
Dockerfile 构建时，什么情况下会复用缓存层？

A. Dockerfile 中某条指令和之前构建完全相同
B. 基础镜像更新时
C. 使用 --no-cache 参数时
D. 每次构建都会复用

**正确答案**：A
**解析**：Docker 构建镜像时会逐条执行 Dockerfile 指令，每条指令创建一个新层。如果该指令和之前构建的指令完全相同（且前面的层也相同），Docker 会复用缓存层，大幅提升构建速度。

---

### Q028: Docker 安全

**类型**：判断题
**概念**：`安全` → `namespaces`
**难度**：0.6
**前置知识**：`namespaces`, `cgroups`

**题目**：
Docker 容器是完全安全的，因为 namespaces 和 cgroups 提供了完整的隔离。

**正确答案**：错误
**解析**：虽然 namespaces 和 cgroups 提供了隔离，但容器仍然共享宿主机内核。内核漏洞可能突破容器隔离。此外，配置不当（如特权容器、挂载敏感目录）也会带来安全风险。Docker 是"安全默认"而非"完全安全"。

---

### Q029: 容器状态机

**类型**：选择题（单选）
**概念**：`容器状态` → `生命周期`
**难度**：0.6
**前置知识**：`容器`

**题目**：
Docker 容器的状态转换中，以下哪条路径是正确的？

A. Created → Running → Paused → Running → Exited
B. Created → Paused → Running → Exited
C. Running → Exited → Running
D. Created → Exited → Running

**正确答案**：A
**解析**：容器创建后处于 Created 可以启动到 Running，Running 可以暂停到 Paused（暂停时进程冻结），Paused 可以恢复到 Running，最后停止到 Exited。Exited 的容器不能直接回到 Running，需要重新 start。

---

### Q030: Go 并发在 Docker 中的应用

**类型**：代码分析题
**概念**：`Go 并发` → `goroutine`
**难度**：0.8
**前置知识**：`dockerd`

**题目**：
以下代码是 Docker daemon 监控容器状态的简化版本：

```go
func (daemon *Daemon) monitorContainers(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case event := <-daemon.events:
            go func() {
                daemon.handleEvent(event)
            }()
        }
    }
}
```

问题：
1. 这里使用了什么 Go 并发模式？
2. `go func()` 启动的 goroutine 有什么潜在问题？
3. ctx.Done() 的作用是什么？

**参考答案**：
1. 使用了 goroutine + channel 的事件驱动模式。for-select 循环监听事件通道和上下文取消信号。
2. 潜在问题：如果 handleEvent 执行很慢，大量事件会创建大量 goroutine。应该使用有界并发（worker pool）或 buffered channel 控制并发数。另外，event 变量在 goroutine 中捕获可能导致闭包问题（Go 1.22 之前）。
3. ctx.Done() 用于优雅退出。当 ctx 被取消（如 daemon 关闭时），monitorContainers 循环退出，避免 goroutine 泄漏。