# BISHENG 工作流 API 接口文档

基于后端代码整理，包含 v1（需认证）和 v2（开放API）两个版本。

## 基础信息

| 版本 | Base URL | 认证方式 | 用途 |
|------|----------|----------|------|
| v1 | `/api/v1/workflow` | JWT Token | 前端管理界面 |
| v2 | `/api/v2/workflow` | 免登录 | 外部系统集成 |

### 统一响应格式

```json
{
  "status_code": 200,
  "status_message": "SUCCESS",
  "data": { ... }
}
```

---

# V2 开放 API

**适用场景**: 第三方系统集成、免登录调用、SSE流式响应

---

## 2.1 执行工作流（核心接口）

```
POST /api/v2/workflow/invoke
```

**请求体**:
```json
{
  "workflow_id": "6a95b4003e2b4a41b6d222f2c555f1b0",
  "input": {
    "kb_id": "knowledge_123",
    "query": "什么是机器学习？"
  },
  "stream": true,
  "session_id": null,
  "message_id": null,
  "override": null
}
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workflow_id | string(UUID) | 是 | 工作流ID |
| input | object | 否 | 用户输入，键值对形式 |
| stream | boolean | 否 | 是否流式返回，默认true |
| session_id | string | 否 | 会话ID，不传则自动生成 |
| message_id | int | 否 | 消息ID，继续执行时必传 |
| override | object | 否 | 覆盖节点参数 |

### 流式响应（stream=true）

返回 `text/event-stream` 格式：

```
data: {"session_id":"abc123","data":{"event":"guide_word","output_schema":{"message":"你好，有什么可以帮助你？"}}}

data: {"session_id":"abc123","data":{"event":"input","input_schema":{"input_type":"form_input","value":[{"key":"query","type":"text","required":true}]}}}

data: {"session_id":"abc123","data":{"event":"stream_msg","status":"stream","node_id":"llm_xxx","output_schema":{"message":"机器学习是..."}}}

data: {"session_id":"abc123","data":{"event":"stream_msg","status":"end","output_schema":{"message":"完整回答"}}}

data: {"session_id":"abc123","data":{"event":"close"}}
```

### 非流式响应（stream=false）

```json
{
  "status_code": 200,
  "data": {
    "session_id": "abc123",
    "events": [
      {"event": "guide_word", "output_schema": {"message": "引导语"}},
      {"event": "input", "input_schema": {...}},
      {"event": "stream_msg", "output_schema": {"message": "完整输出"}},
      {"event": "close"}
    ]
  }
}
```

### 事件类型

| event | 说明 | 必要字段 |
|-------|------|----------|
| `guide_word` | 开场引导语 | `output_schema.message` |
| `guide_question` | 预设问题 | `output_schema.message` |
| `input` | 请求用户输入 | `input_schema` |
| `output_msg` | 输出消息 | `output_schema.message` |
| `output_with_input_msg` | 输出+请求输入 | `output_schema` + `input_schema` |
| `output_with_choose_msg` | 输出+选项选择 | `output_schema` + `input_schema` |
| `stream_msg` | 流式输出 | `status`(stream/end), `output_schema.message` |
| `close` | 会话结束 | - |
| `error` | 错误 | `output_schema.message` |

### 输入模式

**对话框输入**:
```json
{
  "input_schema": {
    "input_type": "dialog_input",
    "value": [
      {"key": "user_input", "type": "text", "required": true, "value": ""},
      {"key": "dialog_files_content", "type": "dialog_file", "value": []}
    ]
  }
}
```

**表单输入**:
```json
{
  "input_schema": {
    "input_type": "form_input",
    "value": [
      {"key": "kb_id", "type": "text", "label": "知识库ID", "required": true},
      {"key": "query", "type": "text", "label": "问题", "required": true}
    ]
  }
}
```

### 多轮对话示例

**第一轮请求**:
```json
{
  "workflow_id": "xxx",
  "input": {"query": "什么是AI"},
  "stream": true
}
```

**响应**（等待用户输入）:
```json
{"event": "input", "message_id": 123, "input_schema": {...}}
```

**第二轮请求**（继续会话）:
```json
{
  "workflow_id": "xxx",
  "session_id": "previous_session_id",
  "message_id": 123,
  "input": {"query": "能详细说说吗"}
}
```

---

## 2.2 停止工作流

```
POST /api/v2/workflow/stop
```

**请求体**:
```json
{
  "workflow_id": "workflow_id",
  "session_id": "session_id"
}
```

---

## 2.3 WebSocket 会话

```
WS /api/v2/workflow/chat/{workflow_id}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| workflow_id | UUID | 工作流ID |

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| chat_id | string | 会话ID（可选）|

**特点**: 免登录，使用默认操作员身份

---

# V1 管理 API

**适用场景**: 前端管理界面、工作流CRUD操作

### 1. 工作流管理

#### 1.1 创建工作流

```
POST /api/v1/workflow/create
```

**请求体**:
```json
{
  "name": "工作流名称",
  "description": "描述",
  "logo": "logo相对路径",
  "data": {
    "nodes": [],
    "edges": [],
    "viewport": {"x": 0, "y": 0, "zoom": 1}
  }
}
```

**响应**:
```json
{
  "status_code": 200,
  "data": {
    "id": "workflow_id",
    "name": "工作流名称",
    "description": "描述",
    "status": 1,
    "flow_type": 10,
    "version_id": 1,
    "create_time": "2026-03-18T10:00:00",
    "update_time": "2026-03-18T10:00:00"
  }
}
```

---

#### 1.2 获取工作流列表

```
GET /api/v1/workflow/list
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 名称模糊搜索 |
| status | int | 否 | 状态：1-下线，2-上线 |
| tag_id | int | 否 | 标签ID |
| flow_type | int | 否 | 类型：1-flow, 5-assistant, 10-workflow |
| page_num | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| managed | bool | 否 | 是否查询有管理权限的应用 |

**响应**:
```json
{
  "status_code": 200,
  "data": {
    "data": [
      {
        "id": "workflow_id",
        "name": "工作流名称",
        "description": "描述",
        "logo": "logo_url",
        "status": 2,
        "flow_type": 10,
        "user_id": 1,
        "user_name": "创建者",
        "write": true,
        "version_list": [...],
        "group_ids": [1, 2],
        "tags": [...],
        "create_time": "...",
        "update_time": "..."
      }
    ],
    "total": 100
  }
}
```

---

#### 1.3 获取单个工作流

```
GET /api/v1/workflow/get_one_flow/{flow_id}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 工作流ID |

**响应**:
```json
{
  "status_code": 200,
  "data": {
    "id": "workflow_id",
    "name": "名称",
    "description": "描述",
    "data": {
      "nodes": [...],
      "edges": [...],
      "viewport": {...}
    },
    "status": 2,
    "version_id": 1
  }
}
```

---

#### 1.4 更新工作流信息

```
PATCH /api/v1/workflow/update/{flow_id}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 工作流ID |

**请求体**:
```json
{
  "name": "新名称",
  "description": "新描述",
  "logo": "新logo",
  "status": 1
}
```

**注意**: 上线状态的工作流不能修改（下线除外）

---

#### 1.5 更新工作流状态（上线/下线）

```
PATCH /api/v1/workflow/status
```

**请求体**:
```json
{
  "flow_id": "workflow_id",
  "version_id": 1,
  "status": 2
}
```

**状态说明**:
| 值 | 状态 |
|----|------|
| 1 | 下线 |
| 2 | 上线 |

---

#### 1.6 检查编辑权限

```
GET /api/v1/workflow/write/auth
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 应用ID |
| flow_type | int | 应用类型 |

**响应**:
```json
{
  "status_code": 200
}
```

---

### 2. 版本管理

#### 2.1 获取版本列表

```
GET /api/v1/workflow/versions
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 工作流ID |

**响应**:
```json
{
  "status_code": 200,
  "data": [
    {
      "id": 1,
      "flow_id": "workflow_id",
      "name": "版本名称",
      "description": "版本描述",
      "is_current": true,
      "create_time": "..."
    }
  ]
}
```

---

#### 2.2 创建新版本

```
POST /api/v1/workflow/versions
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 工作流ID |

**请求体**:
```json
{
  "name": "版本名称",
  "description": "版本描述",
  "data": {
    "nodes": [...],
    "edges": [...]
  },
  "original_version_id": 1
}
```

---

#### 2.3 获取版本详情

```
GET /api/v1/workflow/versions/{version_id}
```

---

#### 2.4 更新版本

```
PUT /api/v1/workflow/versions/{version_id}
```

**请求体**:
```json
{
  "name": "版本名称",
  "description": "版本描述",
  "data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

#### 2.5 删除版本

```
DELETE /api/v1/workflow/versions/{version_id}
```

---

#### 2.6 切换当前版本

```
POST /api/v1/workflow/change_version
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| flow_id | string | 工作流ID |
| version_id | int | 版本ID |

---

### 3. 工作流执行

#### 3.1 单节点运行

```
POST /api/v1/workflow/run_once
```

**请求体**:
```json
{
  "workflow_id": "workflow_id",
  "node_input": {
    "arg1": "value1",
    "arg2": "value2"
  },
  "node_data": {
    "id": "node_id",
    "data": {
      "type": "llm",
      "name": "大模型",
      ...
    }
  }
}
```

**响应**:
```json
{
  "status_code": 200,
  "data": [
    [
      {"key": "output", "value": "执行结果", "type": "variable"}
    ]
  ]
}
```

---

#### 3.2 WebSocket 会话

```
WS /api/v1/workflow/chat/{workflow_id}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| workflow_id | string | 工作流ID |

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| chat_id | string | 会话ID（可选，不传则新建） |

**消息格式**:

**客户端发送**:
```json
{
  "type": "user_input",
  "data": {
    "input": "用户输入内容"
  }
}
```

**服务端响应事件**:

| 事件类型 | 说明 |
|----------|------|
| `user_input` | 请求用户输入（表单/对话框） |
| `guide_word` | 开场引导语 |
| `guide_question` | 预设问题 |
| `output` | 输出消息 |
| `stream` | 流式输出 |
| `error` | 错误消息 |
| `close` | 会话结束 |

**响应消息格式**:
```json
{
  "event": "stream",
  "message_id": 123,
  "status": "stream",
  "node_id": "llm_xxx",
  "node_name": "大模型",
  "node_execution_id": "exec_id",
  "output_schema": {
    "message": "输出内容",
    "output_key": "output"
  }
}
```

**用户输入事件格式**:
```json
{
  "event": "user_input",
  "input_schema": {
    "input_type": "form_input",
    "value": [
      {
        "key": "kb_id",
        "type": "text",
        "label": "知识库ID",
        "required": true,
        "value": ""
      }
    ]
  }
}
```

---

### 4. 报告模板

#### 4.1 获取报告模板文件

```
GET /api/v1/workflow/report/file
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| workflow_id | string | 工作流ID |
| version_key | string | 版本key（可选） |

**响应**:
```json
{
  "status_code": 200,
  "data": {
    "url": "文件下载链接",
    "version_key": "version_key_timestamp"
  }
}
```

---

#### 4.2 复制报告模板

```
POST /api/v1/workflow/report/copy
```

**请求体**:
```json
{
  "version_key": "原版本key"
}
```

**响应**:
```json
{
  "status_code": 200,
  "data": {
    "version_key": "新版本key"
  }
}
```

---

#### 4.3 报告模板回调（Office编辑器）

```
POST /api/v1/workflow/report/callback
```

**请求体**:
```json
{
  "status": 2,
  "url": "文件URL",
  "key": "version_key"
}
```

**status 说明**:
| 值 | 状态 |
|----|------|
| 2 | 保存 |
| 6 | 强制保存 |

---

## 数据模型

### FlowCreate

```typescript
interface FlowCreate {
  name: string;           // 工作流名称
  description?: string;   // 描述
  logo?: string;          // logo相对路径
  data?: {                // 工作流数据
    nodes: Node[];
    edges: Edge[];
    viewport: Viewport;
  };
}
```

### FlowVersionCreate

```typescript
interface FlowVersionCreate {
  name?: string;              // 版本名称
  description?: string;       // 版本描述
  data?: GraphData;           // 节点数据
  original_version_id?: int;  // 源版本ID
  flow_type?: int;            // 类型，默认10
}
```

### WorkflowEvent

```typescript
interface WorkflowEvent {
  event: string;              // 事件类型
  message_id: int;            // 消息ID
  status: string;             // 状态
  node_id?: string;           // 节点ID
  node_name?: string;         // 节点名称
  node_execution_id?: string; // 执行ID
  input_schema?: WorkflowInputSchema;   // 输入定义
  output_schema?: WorkflowOutputSchema; // 输出定义
}
```

### WorkflowInputSchema

```typescript
interface WorkflowInputSchema {
  input_type: string;  // dialog_input | form_input | message_inline_input | message_inline_option
  value: WorkflowInputItem[];
}

interface WorkflowInputItem {
  key: string;
  type: string;      // text | select | dialog_file | dialog_file_accept
  label?: string;
  value: any;
  required?: boolean;
  options?: {label: string, value: string}[];
}
```

### WorkflowOutputSchema

```typescript
interface WorkflowOutputSchema {
  message?: string;           // 消息内容
  files?: File[];             // 文件列表
  output_key?: string;        // 输出变量
  source_url?: string;        // 资源URL
  extra?: any;                // 额外信息
  reasoning_content?: string; // 推理内容
}
```

---

## 错误码

| 错误 | 说明 |
|------|------|
| WorkflowNameExistsError | 工作流名称已存在 |
| WorkFlowOnlineEditError | 上线状态不能编辑 |
| WorkFlowInitError | 工作流初始化失败 |
| AppWriteAuthError | 无编辑权限 |
| UnAuthorizedError | 未授权 |
| NotFoundError | 资源不存在 |

---

## 示例

### 完整工作流执行流程

1. **获取工作流列表**
   ```
   GET /api/v1/workflow/list?flow_type=10
   ```

2. **建立 WebSocket 连接**
   ```
   WS /api/v1/workflow/chat/{workflow_id}
   ```

3. **接收引导语事件**
   ```json
   {"event": "guide_word", "output_schema": {"message": "你好，有什么可以帮助你？"}}
   ```

4. **接收用户输入事件**
   ```json
   {
     "event": "user_input",
     "input_schema": {
       "input_type": "dialog_input",
       "value": [{"key": "user_input", "type": "text", "required": true}]
     }
   }
   ```

5. **发送用户输入**
   ```json
   {"type": "user_input", "data": {"input": "帮我写一首诗"}}
   ```

6. **接收流式输出**
   ```json
   {"event": "stream", "status": "stream", "output_schema": {"message": "春眠不觉晓..."}}
   {"event": "stream", "status": "end", "output_schema": {"message": "春眠不觉晓，处处闻啼鸟。"}}
   ```

7. **会话结束**
   ```json
   {"event": "close"}
   ```