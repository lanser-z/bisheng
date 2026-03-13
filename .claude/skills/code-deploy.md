# 代码部署更新技能

## 触发条件

用户请求以下任务时触发：
- "把改动更新到容器"
- "同步代码到容器"
- "更新后端代码"
- "更新前端代码"
- "部署到容器"
- "同步改动"

---

## 执行流程

### 1. 检测改动

```bash
# 查看已修改的文件
git status --short

# 或查看最近一次提交的改动
git diff --name-only HEAD~1
```

### 2. 分类处理

根据文件路径判断类型：

| 路径前缀 | 类型 | 容器路径 |
|----------|------|----------|
| `src/backend/bisheng/` | 后端代码 | `/app/bisheng/` |
| `src/backend/bisheng_langchain/` | 后端代码 | `/app/bisheng_langchain/` |
| `src/frontend/platform/` | 前端管理端 | `/usr/share/nginx/html/platform/` |
| `src/frontend/client/` | 前端用户端 | `/usr/share/nginx/html/client/` |

### 3. 后端更新流程

```bash
# 1. 复制文件到两个容器
docker cp src/backend/bisheng/workflow/nodes/my_node/my_node.py bisheng-backend:/app/bisheng/workflow/nodes/my_node/
docker cp src/backend/bisheng/workflow/nodes/my_node/my_node.py bisheng-backend-worker:/app/bisheng/workflow/nodes/my_node/

# 2. 重启容器使改动生效
docker restart bisheng-backend bisheng-backend-worker

# 3. 查看日志确认启动正常
docker logs bisheng-backend --tail 50
```

### 4. 前端更新流程

**platform（管理端）**：
```bash
# 1. 构建
cd /home/data/stx/ai_application/bisheng/src/frontend/platform
npm run build

# 2. 复制到容器（无需重启）
docker cp build/. bisheng-frontend:/usr/share/nginx/html/platform/
```

**client（用户端）**：
```bash
# 1. 构建
cd /home/data/stx/ai_application/bisheng/src/frontend/client
npm run build

# 2. 复制到容器（无需重启）
docker cp build/. bisheng-frontend:/usr/share/nginx/html/client/
```

---

## 容器说明

| 容器 | 内容 | 重启要求 |
|------|------|----------|
| `bisheng-backend` | API 服务 | 需要 docker restart |
| `bisheng-backend-worker` | Celery 异步任务 | 需要 docker restart |
| `bisheng-frontend` | Nginx 静态资源 | 无需重启 |

---

## 特殊情况

### 新增 Python 依赖

如果修改了 `src/backend/pyproject.toml`，需要重新构建镜像：

```bash
cd /home/data/stx/ai_application/bisheng/src/backend
docker build -t bisheng-backend:dev .

# 修改 docker-compose.yml 使用新镜像后重启
cd /home/data/stx/ai_application/bisheng/docker
docker compose -p bisheng down && docker compose -p bisheng up -d
```

### 验证部署成功

```bash
# 后端日志
docker logs bisheng-backend --tail 100

# 前端访问
curl http://localhost:9290/platform/
curl http://localhost:9290/client/
```