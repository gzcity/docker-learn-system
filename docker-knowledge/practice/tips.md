# Docker 实践技巧

> Docker 使用、调试和优化实践。

## 调试技巧

### 查看容器内部
```bash
# 进入运行中的容器
docker exec -it <container> /bin/sh

# 查看容器进程
docker top <container>

# 查看容器日志
docker logs -f <container>

# 查看容器元数据（JSON 格式）
docker inspect <container>
```

### 调试容器镜像
```bash
# 查看镜像层级
docker history <image>

# 查看镜像元数据
docker inspect <image>

# 导出镜像内容
docker save <image> | tar -x
```

### 调试网络
```bash
# 查看容器网络
docker network inspect <network>

# 查看容器端口映射
docker port <container>

# 查看容器网络统计
docker stats <container>
```

---

## 性能优化

### 镜像优化
```dockerfile
# 1. 多阶段构建
FROM golang:1.20 AS builder
COPY . .
RUN go build -o app

FROM alpine:3.18
COPY --from=builder /app /app
CMD ["/app"]

# 2. 合并 RUN 指令（减少层数）
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 使用 .dockerignore 减少构建上下文
```

### 容器运行时优化
```bash
# 资源限制
docker run --memory=512m --cpus=2 <image>

# 重启策略
docker run --restart=unless-stopped <image>

# 日志限制
docker run --log-opt max-size=10m --log-opt max-file=3 <image>
```

---

## 源码调试

### 编译调试版本
```bash
# 编译 Docker 调试版本
make build
./bundle/docker-dev

# 附加调试信息
make build DOCKER_DEBUG=true
```

### 查看运行时状态
```bash
# dockerd 调试端点
curl http://localhost:2375/debug/pprof/

# 查看 containerd 状态
containerd --config /etc/containerd/config.toml

# 查看 runc 状态
runc state <container-id>
```

---

## 常见问题排查

### 容器无法启动
1. 检查日志：`docker logs <container>`
2. 检查配置：`docker inspect <container>`
3. 检查资源：`docker stats` 查看资源使用
4. 检查端口冲突：`docker port <container>`
5. 检查挂载：`docker inspect <container> | jq .Mounts`

### 镜像拉取慢
1. 配置镜像加速器
2. 使用 `--platform` 指定架构
3. 检查网络：`docker system df` 查看磁盘使用
4. 清理缓存：`docker system prune`

### 容器网络问题
1. 检查网络驱动：`docker network ls`
2. 检查 DNS：`docker run --dns 8.8.8.8`
3. 检查端口映射：`docker port <container>`
4. 检查网络隔离：`docker network inspect <network>`