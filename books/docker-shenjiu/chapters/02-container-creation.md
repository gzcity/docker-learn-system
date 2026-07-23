# 第 2 章：容器创建流程详解

> 从 `docker run` 到容器进程启动的完整链路。

## 2.1 一条命令的旅程

```bash
docker run -it --rm ubuntu:22.04 /bin/bash
```

这条命令背后经历了以下步骤：

### Step 1: CLI 解析
```
docker run → CLI 解析参数
  → 构建 API 请求（POST /containers/create）
  → 发送给 dockerd
```

### Step 2: dockerd 处理
```
dockerd 接收请求
  → 解析镜像名（ubuntu:22.04）
  → 检查本地是否已有镜像
  → 如果没有，开始拉取
  → 创建容器配置（资源限制、网络、挂载）
  → 调用 containerd 创建容器
```

### Step 3: containerd 处理
```
containerd 接收请求
  → 创建容器元数据（存到 boltdb）
  → 准备容器的 rootfs（挂载镜像层）
  → 创建 shim 进程
  → 等待 shim 返回结果
```

### Step 4: shim 启动
```
shim 进程启动
  → 创建容器运行时环境
  → 调用 runc 创建容器
  → 保持 IO 连接
  → 上报容器状态
```

### Step 5: runc 执行
```
runc 接收 OCI bundle
  → 读取 config.json（容器配置）
  → 创建 namespaces（PID、NET、IPC、UTS、MNT）
  → 配置 cgroups（CPU、内存限制）
  → 挂载 rootfs
  → 执行容器进程（/bin/bash）
  → runc 退出
```

## 2.2 关键源码路径

```go
// 1. dockerd 创建容器
daemon/create.go → daemon.ContainerCreate()

// 2. dockerd 启动容器
daemon/start.go → daemon.ContainerStart()

// 3. 调用 containerd
daemon/containerd.go → containerd. NewContainer()

// 4. containerd 创建任务
// containerd 内部: NewTask → shim 启动

// 5. runc 创建容器
// vendor/github.com/opencontainers/runc/libcontainer/
//   → linuxContainer.Start()
```

## 2.3 关键数据结构

```go
// containerd 容器结构
type Container struct {
    ID      string
    Image   string
    Runtime RuntimeInfo
    Spec    specs.Spec  // OCI 运行时规范
    // ...
}

// OCI 运行时规范
type Spec struct {
    Version string
    Process Process      // 容器进程
    Root    Root         // 文件系统
    Mounts  []Mount      // 挂载点
    Linux   Linux        // Linux 特有配置
    // ...
}
```

## 2.4 设计要点

- **异步创建**: dockerd 不等待容器完全创建，而是通过事件机制监听
- **优雅退出**: 每个组件都有清晰的退出路径，确保资源释放
- **错误传播**: 从 runc 到 dockerd，错误信息逐层传递

---

**思考题**：为什么需要 shim 这个中间层？如果直接让 containerd 管理 runc 会有什么问题？