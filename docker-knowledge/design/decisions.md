# Docker 设计决策

> 理解 Docker 架构设计背后的原理和关键决策。

## 镜像拉取流程

### 完整流程
```
docker pull ubuntu:22.04
  → dockerd 解析镜像名
  → 查询本地缓存（已有层跳过）
  → 联系 registry（索引）
  → 获取 manifest（清单文件）
  → 按层下载（并行 + 断点续传）
  → 解压并存储到本地存储驱动
  → 更新镜像索引
```

### 关键设计
- **分层下载**: 只下载本地没有的层，已有层复用
- **并行下载**: 多个层同时下载，提高速度
- **断点续传**: 下载中断后从断点继续
- **内容寻址**: 使用 digest (sha256) 标识层，确保完整性

### 源码位置
- `distribution/pull.go` — 拉取逻辑
- `distribution/xfer/` — 传输管理
- `reference/` — 镜像引用解析

### 源码关键点
```go
// 拉取的核心是 p.Download()
func (p *Puller) Download(ctx context.Context) error {
    // 1. 解析镜像引用
    // 2. 获取 manifest
    // 3. 按需下载层
    // 4. 验证 digest
    // 5. 存储到本地
}
```

---

## 镜像构建流程

### Dockerfile 构建流程
```
docker build -t myapp .
  → 读取 Dockerfile
  → 解析每条指令
  → 对每个 RUN/COPY/ADD 创建新层
  → 缓存命中：跳过层
  → 缓存未命中：执行指令，提交层
  → 生成最终镜像
```

### 构建缓存策略
- **上次构建缓存**: 基于之前构建的镜像层
- **指令匹配**: 比较指令内容和顺序
- **上下文检查**: 比较 ADD/COPY 的文件内容和元数据
- **缓存失效**: 某层缓存失效后，后续所有层失效

### 源码位置
- `builder/` — 构建器
- `builder/dockerfile/` — Dockerfile 解析和执行
- `builder/remotecontext/` — 构建上下文

### 关键设计决策
- **每层一条指令**: 不是所有指令都创建层（ENV/LABEL 不创建）
- **层缓存**: 基于指令的哈希值，实现缓存
- **多阶段构建**: 通过多个 FROM 语句分离构建环境和运行环境

---

## 网络模型

### CNM (Container Network Model)
Docker 使用自有的 CNM 网络模型，由 libnetwork 实现。

```
Sandbox (网络命名空间)
    ↓
  Endpoint (网卡接口)
    ↓
  Network (网桥/overlay/macvlan)
```

### 网络驱动
| 驱动 | 用途 | 隔离性 | 跨主机 |
|------|------|--------|--------|
| bridge | 默认，单机 NAT | 中 | 否 |
| host | 共享宿主机网络 | 低 | 否 |
| overlay | 跨主机通信 | 高 | 是 |
| macvlan | 直接分配 MAC | 高 | 是 |
| none | 无网络 | - | - |

### 源码位置
- `libnetwork/` — 网络库
- `libnetwork/drivers/bridge/` — 网桥驱动
- `libnetwork/drivers/overlay/` — 覆盖网络驱动

### 关键设计
- **CNM 与 CNI 的区别**: Docker 使用自有的 CNM，Kubernetes 使用 CNI
- **overlay 网络**: 使用 VXLAN 封装，支持跨主机通信
- **DNS 解析**: 内置 DNS 服务，容器间通过名称通信

---

## 存储驱动

### 支持的存储驱动
| 驱动 | 文件系统 | 特点 |
|------|---------|------|
| overlay2 | xfs/ext4 | 推荐，性能好 |
| fuse-overlayfs | 任意 | rootless 模式 |
| devicemapper | 直接管理块设备 | 已弃用 |
| aufs | 特定内核 | 已弃用 |
| btrfs/zfs | 原生 | 特定场景 |

### overlay2 原理
```
/var/lib/docker/overlay2/
├── l/                    # 符号链接（缩短路径）
├── <layer-id>/           # 层目录
│   ├── diff/             # 该层的文件变更
│   ├── link              # 符号链接指向
│   └── lower             # 下层层ID
└── <container-id>/       # 容器可写层
    └── merged/           # 合并后的视图
```

### 源码位置
- `daemon/graphdriver/overlay2/` — overlay2 驱动
- `daemon/graphdriver/` — 存储驱动接口

---

## 插件系统

### 插件类型
- **Volume 插件**: 管理存储卷
- **Network 插件**: 管理网络
- **Authorization 插件**: 访问控制
- **Logging 插件**: 日志驱动

### 插件通信
```
dockerd → Plugin API → 插件进程
         ← 插件响应 ←
```

### 源码位置
- `plugin/` — 插件管理
- `plugin/v2/` — v2 插件协议

### 关键设计
- 插件以容器方式运行
- 通过 Unix socket 或 HTTP 与 dockerd 通信
- 支持插件生命周期管理（安装、启动、停止、移除）