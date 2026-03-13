# BISHENG 容器错误排查技能

## 架构说明

BISHENG 采用前后端分离 + 异步Worker架构：

| 容器 | 职责 | 日志内容 |
|------|------|----------|
| `bisheng-backend` | API服务、WebSocket连接 | 请求日志、输入输出数据 |
| `bisheng-backend-worker` | 工作流执行引擎 | **运行期错误、异常堆栈** |
| `bisheng-frontend` | 静态前端资源 | Nginx访问日志 |

**关键点**：工作流节点的运行时错误在 `bisheng-backend-worker` 中查看，而不是 `bisheng-backend`。

## 排查命令

### 1. 查看Worker运行错误

```bash
# 查看最近200行日志中的异常信息
docker logs --tail=200 bisheng-backend-worker 2>&1 | grep -E "(error|Error|ERROR|exception|Exception|Traceback)" -i -A5

# 搜索特定节点类型的错误
docker logs --tail=200 bisheng-backend-worker 2>&1 | grep -E "(qa_retriever|llm|rag)" -i -A5

# 查看Python异常堆栈
docker logs --tail=200 bisheng-backend-worker 2>&1 | grep -E "Traceback|TypeError|AttributeError|KeyError|ImportError|ValueError" -A10
```

### 2. 查看Backend请求日志

```bash
# 查看API请求
docker logs --tail=100 bisheng-backend 2>&1 | grep -E "POST|GET|api"

# 查看WebSocket消息
docker logs --tail=100 bisheng-backend 2>&1 | grep -E "message|action|flow_id"
```

### 3. 实时跟踪日志

```bash
# 实时查看Worker日志
docker logs -f bisheng-backend-worker 2>&1 | grep --line-buffered -E "(ERROR|Exception|Traceback)" -A5

# 实时查看所有错误
docker logs -f bisheng-backend-worker 2>&1
```

## 常见错误模式

### TypeError: string indices must be integers
- **原因**：代码期望字典列表 `[{'key': 'value'}]`，实际收到字符串或字符串列表
- **排查**：检查参数格式转换逻辑
- **示例**：`instantiate_vectorstore` 需要 `[{'key': 'id'}]` 格式

### AttributeError: 'NoneType' object has no attribute
- **原因**：变量或对象未正确初始化
- **排查**：检查上游节点是否正确传递数据

### KeyError: 'xxx'
- **原因**：访问不存在的字典键
- **排查**：检查数据结构、节点参数配置

### ImportError / ModuleNotFoundError
- **原因**：模块未正确部署或路径错误
- **排查**：
  ```bash
  # 检查文件是否存在
  docker exec bisheng-backend ls -la /app/bisheng/workflow/nodes/xxx/
  ```

## 节点调试技巧

### 1. 添加日志输出

在节点代码中使用 logger：
```python
from loguru import logger

def _run(self, unique_id: str):
    logger.info(f"节点 {self.name}: 参数值 = {self._some_param}")
    logger.debug(f"节点 {self.name}: 中间结果 = {result}")
```

### 2. 检查节点是否注册

```bash
# 检查节点类是否在映射表中
docker exec bisheng-backend grep -A2 "NODE_CLASS_MAP" /app/bisheng/workflow/nodes/node_manage.py
```

### 3. 检查节点文件是否部署

```bash
# 检查节点目录
docker exec bisheng-backend ls -la /app/bisheng/workflow/nodes/<node_type>/

# 检查Python缓存是否更新
docker exec bisheng-backend ls -la /app/bisheng/workflow/nodes/<node_type>/__pycache__/
```

## 代码更新后生效

### 后端代码更新

```bash
# 1. 复制代码到容器
docker cp src/backend/bisheng/workflow/nodes/xxx/ bisheng-backend:/app/bisheng/workflow/nodes/
docker cp src/backend/bisheng/workflow/nodes/xxx/ bisheng-backend-worker:/app/bisheng/workflow/nodes/

# 2. 重启容器
docker restart bisheng-backend-worker
docker restart bisheng-backend  # 可选，API变更时需要
```

### 前端代码更新

```bash
# 1. 构建前端
cd src/frontend/platform && npm run build

# 2. 复制到容器
docker cp dist/ bisheng-frontend:/usr/share/nginx/html/platform/
# 前端无需重启，静态文件直接生效
```

## 排查流程

1. **确认错误发生**：用户报告工作流执行失败
2. **查看Worker日志**：`docker logs bisheng-backend-worker` 找异常堆栈
3. **定位错误位置**：根据 `File "/app/bisheng/..."` 找到具体代码行
4. **分析错误原因**：结合错误类型和日志上下文
5. **修复代码**：修改源码
6. **部署验证**：复制到容器，重启，再次测试