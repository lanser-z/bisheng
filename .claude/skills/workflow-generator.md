# BISHENG 工作流生成技能

根据文字描述生成可导入的工作流 JSON 文件。

## 触发场景

- 用户要求生成工作流 JSON
- 用户描述工作流逻辑需要导出为文件
- 用户说"生成工作流"、"创建流程"、"帮我写一个工作流"等

---

## 工作流 JSON 结构

```json
{
  "name": "工作流名称",
  "description": "描述",
  "status": 2,
  "flow_type": 10,
  "nodes": [...],
  "edges": [...],
  "viewport": {"x": 0, "y": 0, "zoom": 1}
}
```

### 核心字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| nodes | array | 节点列表 |
| edges | array | 节点连接 |
| viewport | object | 画布视图 |

---

## 节点目录

### 1. 开始节点 (start)

**⚠️ 关键：start 节点必须包含完整的参数列表！**

后端代码会直接访问 `node_params['guide_question']` 和 `node_params['preset_question']`，如果缺少这些字段会导致 KeyError 异常。

**必须参数**（都必须有）:
| 参数 | 类型 | 说明 |
|------|------|------|
| guide_word | textarea | 开场引导语，必须有 `label` 和 `placeholder` |
| guide_question | input_list | 预设问题，`value` 必须是 `[""]`，必须有 `help`, `label`, `placeholder` |
| user_info | var | 用户信息变量 |
| current_time | var | 当前时间变量 |
| chat_history | chat_history_num | 对话历史条数 |
| preset_question | input_list | 预置问题，`value` 格式: `[{"key": "xxx", "value": ""}]` |
| custom_variables | global_var | 自定义变量，`value: []` |

**输出变量**:
- `user_info`: 用户信息
- `current_time`: 当前时间
- `chat_history`: 对话历史

**完整模板**（必须精确匹配）:
```json
{
  "id": "start_xxx",
  "type": "flowNode",
  "position": {"x": 100, "y": 100},
  "data": {
    "v": "3",
    "id": "start_xxx",
    "name": "开始",
    "type": "start",
    "description": "工作流运行的起始节点。",
    "group_params": [
      {
        "name": "开场引导",
        "params": [
          {"key": "guide_word", "type": "textarea", "label": "true", "value": "引导语", "placeholder": "true"},
          {"key": "guide_question", "help": "true", "type": "input_list", "label": "true", "value": [""], "placeholder": "true"}
        ]
      },
      {
        "name": "全局变量",
        "params": [
          {"key": "user_info", "type": "var", "label": "true", "value": "", "global": "key"},
          {"key": "current_time", "type": "var", "label": "true", "value": "", "global": "key"},
          {"key": "chat_history", "type": "chat_history_num", "value": 10, "global": "key"},
          {"key": "preset_question", "help": "true", "type": "input_list", "label": "true", "value": [{"key": "abc123", "value": ""}], "global": "item:input_list", "placeholder": "true"},
          {"key": "custom_variables", "help": "true", "type": "global_var", "label": "true", "value": [], "global": "item:input_list"}
        ]
      }
    ]
  },
  "measured": {"width": 334, "height": 493}
}
```

---

### 2. 结束节点 (end)

**必须参数**: 无

**完整模板**:
```json
{
  "id": "end_xxx",
  "type": "flowNode",
  "position": {"x": 800, "y": 100},
  "data": {
    "v": "1",
    "id": "end_xxx",
    "name": "结束",
    "type": "end",
    "description": "工作流运行到此结束",
    "group_params": []
  },
  "measured": {"width": 334, "height": 135}
}
```

---

### 3. 输入节点 (input)

**两种模式**: dialog_input (对话框) / form_input (表单)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| tab.value | string | 输入模式: "dialog_input" 或 "form_input" |

**对话框模式参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_input | var | 用户输入文本变量 |
| user_input_file | boolean | 是否允许上传文件 |

**表单模式参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| form_input | form | 表单字段配置 |

**表单字段格式**:
```json
{
  "key": "field_name",
  "type": "text",
  "value": "字段标签",
  "required": true
}
```

**输出变量**: 根据表单字段定义

**模板**:
```json
{
  "id": "input_xxx",
  "type": "flowNode",
  "position": {"x": 300, "y": 100},
  "data": {
    "type": "input",
    "name": "输入",
    "v": "3",
    "tab": {"value": "form_input", "options": [...]},
    "group_params": [{
      "params": [{
        "key": "form_input",
        "type": "form",
        "value": [
          {"key": "kb_id", "type": "text", "value": "知识库ID", "required": true},
          {"key": "query", "type": "text", "value": "问题", "required": true}
        ]
      }]
    }]
  }
}
```

---

### 4. 输出节点 (output)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| message | var_textarea_file | 输出消息，支持变量引用 |

**消息格式**:
```json
{
  "msg": "回复内容 {{#node_id.output#}}",
  "files": []
}
```

**模板**:
```json
{
  "id": "output_xxx",
  "type": "flowNode",
  "position": {"x": 600, "y": 100},
  "data": {
    "type": "output",
    "name": "输出",
    "v": "2",
    "group_params": [{
      "params": [{
        "key": "message",
        "type": "var_textarea_file",
        "value": {"msg": "", "files": []}
      }]
    }]
  }
}
```

---

### 5. 大模型节点 (llm)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| model_id | bisheng_model | 模型ID（数字） |
| user_prompt | var_textarea | 用户提示词 |

**可选参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| system_prompt | var_textarea | "" | 系统提示词 |
| temperature | slide | 0.7 | 温度 [0-2] |
| output_user | switch | true | 是否流式输出 |

**输出变量**:
- `output`: 模型输出

**模板**:
```json
{
  "id": "llm_xxx",
  "type": "flowNode",
  "position": {"x": 400, "y": 100},
  "data": {
    "type": "llm",
    "name": "大模型",
    "v": "2",
    "tab": {"value": "single"},
    "group_params": [
      {"name": "模型设置", "params": [
        {"key": "model_id", "type": "bisheng_model", "value": 1},
        {"key": "temperature", "type": "slide", "value": 0.7}
      ]},
      {"name": "提示词", "params": [
        {"key": "system_prompt", "type": "var_textarea", "value": ""},
        {"key": "user_prompt", "type": "var_textarea", "value": "{{#input_xxx.user_input#}}"}
      ]},
      {"name": "输出", "params": [
        {"key": "output_user", "type": "switch", "value": true},
        {"key": "output", "type": "var", "value": []}
      ]}
    ]
  }
}
```

---

### 6. 代码节点 (code)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| code_input | code_input | 入参配置 |
| code | code | Python 代码 |
| code_output | code_output | 出参配置 |

**入参格式**:
```json
[
  {"key": "arg1", "type": "ref", "value": "node_id.param", "label": "变量描述"}
]
```

**出参格式**:
```json
[
  {"key": "result", "type": "str"}
]
```

**代码模板**:
```python
def main(arg1: str, arg2: str) -> dict:
    return {'result': arg1 + arg2}
```

**模板**:
```json
{
  "id": "code_xxx",
  "type": "flowNode",
  "position": {"x": 400, "y": 100},
  "data": {
    "type": "code",
    "name": "代码",
    "v": "1",
    "group_params": [
      {"name": "入参", "params": [{
        "key": "code_input",
        "type": "code_input",
        "value": [{"key": "data", "type": "ref", "value": "llm_xxx.output"}]
      }]},
      {"name": "执行代码", "params": [{
        "key": "code",
        "type": "code",
        "value": "def main(data: str) -> dict:\n    return {'result': data}"
      }]},
      {"name": "出参", "params": [{
        "key": "code_output",
        "type": "code_output",
        "value": [{"key": "result", "type": "str"}]
      }]}
    ]
  }
}
```

---

### 7. 条件分支节点 (condition)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| condition | condition | 条件表达式 |

**条件格式**:
```json
[{
  "id": "cond_id",
  "operator": "and",
  "conditions": [{
    "id": "sub_id",
    "left_var": "node_id.param",
    "left_label": "变量描述",
    "right_value": "比较值",
    "right_value_type": "input",
    "comparison_operation": "equals"
  }]
}]
```

**比较操作**:
- `equals`: 等于
- `not_equals`: 不等于
- `contains`: 包含
- `is_empty`: 为空
- `is_not_empty`: 不为空
- `greater_than`: 大于
- `less_than`: 小于

**模板**:
```json
{
  "id": "condition_xxx",
  "type": "flowNode",
  "position": {"x": 400, "y": 100},
  "data": {
    "type": "condition",
    "name": "条件分支",
    "v": "1",
    "group_params": [{
      "params": [{
        "key": "condition",
        "type": "condition",
        "value": [{
          "id": "cond_1",
          "operator": "and",
          "conditions": [{
            "id": "sub_1",
            "left_var": "code_xxx.result",
            "left_label": "结果",
            "right_value": "continue",
            "right_value_type": "input",
            "comparison_operation": "equals"
          }]
        }]
      }]
    }]
  }
}
```

---

### 8. QA知识库检索Pro (qa_retriever_pro)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_question | var_select | 问题变量引用 |
| qa_knowledge_id_variable | var_select | 知识库ID变量引用 |
| score | slide | 相似度阈值 [0.01-0.99] |

**输出变量**:
- `retrieved_result`: 检索结果

**模板**:
```json
{
  "id": "qa_retriever_pro_xxx",
  "type": "flowNode",
  "position": {"x": 400, "y": 100},
  "data": {
    "type": "qa_retriever_pro",
    "name": "QA知识库检索Pro",
    "v": "1",
    "group_params": [
      {"name": "检索设置", "params": [
        {"key": "user_question", "type": "var_select", "value": "input_xxx.query"},
        {"key": "qa_knowledge_id_variable", "type": "var_select", "value": "input_xxx.kb_id"},
        {"key": "score", "type": "slide", "value": 0.8}
      ]},
      {"name": "输出", "params": [
        {"key": "retrieved_result", "type": "var", "value": ""}
      ]}
    ]
  }
}
```

---

### 9. RagFlow检索节点 (ragflow_retriever)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| ragflow_api_url | input | RagFlow API 地址 |
| ragflow_api_key | input | RagFlow API 密钥 |
| question | var_select | 问题变量引用 |
| dataset_ids | var_select | 数据集ID变量引用 |

**可选参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| similarity_threshold | slide | 0.2 | 相似度阈值 [0.01-1.0] |
| vector_similarity_weight | slide | 0.3 | 向量权重 [0.0-1.0] |
| page_size | number | 10 | 返回条数 [1-100] |
| use_kg | switch | false | 启用知识图谱 |
| max_content_length | number | 15000 | 内容最大长度 [1000-100000] |

**输出变量**:
- `retrieved_result`: 检索结果文本
- `chunks`: 原始分块列表

**模板**:
```json
{
  "id": "ragflow_retriever_xxx",
  "type": "flowNode",
  "position": {"x": 400, "y": 100},
  "data": {
    "type": "ragflow_retriever",
    "name": "RagFlow检索",
    "v": "1",
    "group_params": [
      {"name": "RagFlow配置", "params": [
        {"key": "ragflow_api_url", "type": "input", "value": "http://ragflow-server"},
        {"key": "ragflow_api_key", "type": "input", "value": "ragflow-api-key"}
      ]},
      {"name": "检索设置", "params": [
        {"key": "question", "type": "var_select", "value": "input_xxx.query"},
        {"key": "dataset_ids", "type": "var_select", "value": "input_xxx.dataset_id"},
        {"key": "similarity_threshold", "type": "slide", "value": 0.2},
        {"key": "page_size", "type": "number", "value": 10},
        {"key": "max_content_length", "type": "number", "value": 15000}
      ]},
      {"name": "输出", "params": [
        {"key": "retrieved_result", "type": "var", "value": ""},
        {"key": "chunks", "type": "var", "value": ""}
      ]}
    ]
  }
}
```

---

### 10. Agent节点 (agent)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| model_id | agent_model | 模型ID |
| system_prompt | var_textarea | 系统提示词 |
| user_prompt | var_textarea | 用户提示词 |

**可选参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| knowledge_id | knowledge_select_multi | 关联知识库 |
| tool_list | add_tool | 工具列表 |
| sql_agent | sql_config | 数据库配置 |

**输出变量**:
- `output`: Agent输出

---

### 11. RAG节点 (rag)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_question | user_question | 问题变量引用 |
| knowledge | knowledge_select_multi | 知识库选择 |
| system_prompt | var_textarea | 系统提示词 |
| model_id | bisheng_model | 模型ID |

**输出变量**:
- `retrieved_result`: 检索结果
- `output_user_input`: 输出变量列表

---

### 12. 工具节点 (tool)

**必须参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| tool_key | string | 工具唯一标识 |
| group_params | array | 工具参数配置 |

**模板**:
```json
{
  "id": "tool_xxx",
  "type": "flowNode",
  "data": {
    "type": "tool",
    "name": "工具名称",
    "tool_key": "tool_unique_key",
    "group_params": [
      {"name": "工具参数", "params": [
        {"key": "query", "type": "var_textarea", "value": "{{#input_xxx.user_input#}}"}
      ]},
      {"name": "输出", "params": [
        {"key": "output", "type": "var", "value": ""}
      ]}
    ]
  }
}
```

---

## 变量引用语法

### 基本语法
```
{{#节点ID.参数名#}}
```

### 示例
```
{{#input_xxx.query#}}          # 引用输入节点的query字段
{{#llm_xxx.output#}}           # 引用大模型节点的输出
{{#code_xxx.result#}}          # 引用代码节点的result出参
{{#qa_retriever_pro_xxx.retrieved_result#}}  # 引用检索结果
```

---

## 边(Edge)配置

### 格式
```json
{
  "id": "xy-edge__sourceId-targetId",
  "type": "customEdge",
  "source": "source_node_id",
  "target": "target_node_id",
  "animated": true,
  "sourceHandle": "right_handle",
  "targetHandle": "left_handle"
}
```

### 条件分支边
```json
{
  "id": "xy-edge__conditionId-conditionId-targetId",
  "source": "condition_xxx",
  "target": "target_node_id",
  "sourceHandle": "condition_id",  # 条件ID作为handle
  "targetHandle": "left_handle"
}
```

---

## 生成流程

### 1. 解析用户描述
- 识别所需节点
- 确定节点顺序
- 提取参数配置

### 2. 生成节点
- 分配唯一ID（格式: `type_5位随机字符`）
- 计算position坐标（从左到右排列）
- 填充group_params

### 3. 生成边
- 按顺序连接节点
- 处理条件分支

### 4. 验证
- 检查必须参数
- 验证变量引用是否存在
- 检查循环依赖

### 5. 预览
生成 PlantUML 图表展示工作流结构

---

## PlantUML 预览格式

```
@startuml
skinparam componentStyle rectangle

start "开始" as start_xxx
input "输入" as input_xxx
llm "大模型" as llm_xxx
output "输出" as output_xxx
end "结束" as end_xxx

start_xxx --> input_xxx
input_xxx --> llm_xxx : user_input
llm_xxx --> output_xxx : output
output_xxx --> end_xxx

note right of llm_xxx
  model_id: 1
  temperature: 0.7
end note
@enduml
```

---

## 错误预测规则

### 导入前检查

| 错误类型 | 检查规则 |
|----------|----------|
| 必须参数缺失 | 检查所有required参数是否有值 |
| 变量引用无效 | 检查引用的节点ID和参数是否存在 |
| 节点ID冲突 | 检查ID是否唯一 |
| 循环依赖 | 检查边是否形成闭环（条件分支除外） |
| 类型不匹配 | 检查参数值类型是否正确 |

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 模型ID不存在 | 使用数字ID，系统会自动映射 |
| 知识库ID不存在 | 导入时会自动清空，需要重新选择 |
| 变量引用格式错误 | 使用 `{{#node_id.param#}}` 格式 |
| 节点缺少必须参数 | 检查并补充required参数 |

---

## 生成示例

### 用户输入
```
创建一个简单的问答工作流：
1. 用户输入问题
2. 调用GPT-4回答
3. 输出答案
```

### 生成的JSON
```json
{
  "name": "简单问答",
  "description": "用户输入问题，GPT-4回答",
  "status": 2,
  "flow_type": 10,
  "nodes": [
    {
      "id": "start_a1b2c",
      "type": "flowNode",
      "position": {"x": 100, "y": 100},
      "data": {"type": "start", "name": "开始", "v": "3", "group_params": []}
    },
    {
      "id": "input_d3e4f",
      "type": "flowNode",
      "position": {"x": 300, "y": 100},
      "data": {
        "type": "input",
        "name": "输入",
        "v": "3",
        "tab": {"value": "dialog_input"},
        "group_params": [{
          "name": "接收文本",
          "params": [{"key": "user_input", "type": "var", "global": "key"}]
        }]
      }
    },
    {
      "id": "llm_g5h6i",
      "type": "flowNode",
      "position": {"x": 500, "y": 100},
      "data": {
        "type": "llm",
        "name": "大模型",
        "v": "2",
        "tab": {"value": "single"},
        "group_params": [
          {"name": "模型设置", "params": [
            {"key": "model_id", "type": "bisheng_model", "value": 1},
            {"key": "temperature", "type": "slide", "value": 0.7}
          ]},
          {"name": "提示词", "params": [
            {"key": "system_prompt", "type": "var_textarea", "value": "你是一个有帮助的助手"},
            {"key": "user_prompt", "type": "var_textarea", "value": "{{#input_d3e4f.user_input#}}"}
          ]}
        ]
      }
    },
    {
      "id": "output_j7k8l",
      "type": "flowNode",
      "position": {"x": 700, "y": 100},
      "data": {
        "type": "output",
        "name": "输出",
        "v": "2",
        "group_params": [{
          "params": [{
            "key": "message",
            "type": "var_textarea_file",
            "value": {"msg": "{{#llm_g5h6i.output#}}", "files": []}
          }]
        }]
      }
    },
    {
      "id": "end_m9n0o",
      "type": "flowNode",
      "position": {"x": 900, "y": 100},
      "data": {"type": "end", "name": "结束", "v": "1", "group_params": []}
    }
  ],
  "edges": [
    {"id": "e1", "type": "customEdge", "source": "start_a1b2c", "target": "input_d3e4f", "animated": true, "sourceHandle": "right_handle", "targetHandle": "left_handle"},
    {"id": "e2", "type": "customEdge", "source": "input_d3e4f", "target": "llm_g5h6i", "animated": true, "sourceHandle": "right_handle", "targetHandle": "left_handle"},
    {"id": "e3", "type": "customEdge", "source": "llm_g5h6i", "target": "output_j7k8l", "animated": true, "sourceHandle": "right_handle", "targetHandle": "left_handle"},
    {"id": "e4", "type": "customEdge", "source": "output_j7k8l", "target": "end_m9n0o", "animated": true, "sourceHandle": "right_handle", "targetHandle": "left_handle"}
  ],
  "viewport": {"x": 0, "y": 0, "zoom": 1}
}
```

### PlantUML 预览
```
@startuml
skinparam componentStyle rectangle

(*) --> "开始" as start_a1b2c
rectangle "输入" as input_d3e4f
rectangle "大模型" as llm_g5h6i
rectangle "输出" as output_j7k8l
"结束" as end_m9n0o --> (*)

start_a1b2c --> input_d3e4f
input_d3e4f --> llm_g5h6i : user_input
llm_g5h6i --> output_j7k8l : output
output_j7k8l --> end_m9n0o

note right of llm_g5h6i
  model: GPT-4
  temperature: 0.7
end note
@enduml
```

---

## 语法检查清单（必须执行）

生成JSON后，必须逐项检查以下语法规则：

### 1. 顶层结构检查

| 检查项 | 要求 | 示例 |
|--------|------|------|
| name | 必填，字符串 | `"name": "工作流名称"` |
| status | 必填，整数 | `2` (上线) 或 `1` (下线) |
| flow_type | 必填，整数 | `10` (工作流) |
| nodes | 必填，数组 | `[]` |
| edges | 必填，数组 | `[]` |
| viewport | 必填，对象 | `{"x": 0, "y": 0, "zoom": 1}` |

### 2. 节点通用检查

**⚠️ 关键：每个节点必须有以下字段！**

| 检查项 | 要求 | 说明 |
|--------|------|------|
| id | 格式 `type_5位字符` | 如 `start_a1b2c`, `llm_7e8f9` |
| type | 必须是 `"flowNode"` | 不是节点类型！ |
| position | 必须有 x, y | `{"x": 100, "y": 200}` |
| **data.id** | 必须与顶层 id 相同 | 前端依赖此字段 |
| **data.type** | 节点实际类型 | `"data": {"type": "llm", "id": "llm_7e8f9", ...}` |
| **measured** | 必须有 | `{"width": 334, "height": 200}` |
| data.v | 版本号 | start: `"3"`, llm: `"2"`, code: `"1"` |

**正确示例**:
```json
{
  "id": "llm_7e8f9",
  "type": "flowNode",
  "position": {"x": 600, "y": 200},
  "data": {
    "type": "llm",
    "id": "llm_7e8f9",
    "name": "LLM节点",
    "v": "2",
    ...
  },
  "measured": {"width": 334, "height": 200}
}
```

### 3. 输入节点 (input) 检查

**⚠️ 关键：input 节点必须有完整的 `group_params` 结构！**

前端变量选择器 `SelectVar.tsx` 通过 `global: "item:form_input"` 注册表单字段变量。
如果结构不正确，变量将无法在下拉框中显示。

| 检查项 | 要求 | 说明 |
|--------|------|------|
| v | 必须是 `"3"` | 版本号，避免触发兼容性转换 |
| data.id | 必须与顶层 id 相同 | 前端依赖此字段 |
| tab.value | `dialog_input` 或 `form_input` | 决定默认输入模式 |
| tab.options | 每项必须有 `key`, `label`, `help` | UI显示所需 |
| **group_params** | 必须有 **4 个组** | 见下方完整结构 |
| form_input.type | 必须是 `"form"` | 类型标识 |
| **form_input.global** | 必须是 `"item:form_input"` | 变量注册关键字段！ |
| form_input.label | 必须是 `"true"` | UI显示所需 |
| 表单字段 | 需要完整字段 | 见下方示例 |
| **measured** | 必须有 | `{"width": 334, "height": 358}` |

**完整 input 节点结构（必须精确匹配）**:
```json
{
  "id": "input_xxx",
  "data": {
    "v": "3",
    "id": "input_xxx",
    "tab": {
      "value": "form_input",
      "options": [
        {"key": "dialog_input", "help": "true", "label": "true"},
        {"key": "form_input", "help": "true", "label": "true"}
      ]
    },
    "name": "输入",
    "type": "input",
    "group_params": [
      {
        "name": "接收文本",
        "params": [
          {"key": "user_input", "tab": "dialog_input", "type": "var", "label": "true", "global": "key"}
        ]
      },
      {
        "name": "",
        "params": [
          {"key": "user_input_file", "tab": "dialog_input", "value": true, "groupTitle": true},
          {"key": "file_parse_mode", "tab": "dialog_input", "type": "select_parsemode", "value": "extract_text"},
          {"key": "dialog_files_content", "tab": "dialog_input", "type": "var", "label": "true", "global": "key"},
          {"key": "dialog_files_content_size", "min": 0, "tab": "dialog_input", "type": "char_number", "label": "true", "value": 15000},
          {"key": "dialog_file_accept", "tab": "dialog_input", "type": "select_fileaccept", "label": "true", "value": "all"},
          {"key": "dialog_image_files", "tab": "dialog_input", "help": "true", "type": "var", "label": "true", "global": "key"},
          {"key": "dialog_file_paths", "tab": "dialog_input", "help": "true", "type": "var", "label": "true", "global": "key"}
        ],
        "groupKey": "inputfile"
      },
      {
        "name": "",
        "params": [
          {"key": "recommended_questions_flag", "tab": "dialog_input", "help": "true", "label": "true", "value": false, "hidden": "true", "groupTitle": true},
          {"key": "recommended_llm", "tab": "dialog_input", "type": "bisheng_model", "label": "true", "value": 1, "required": true, "placeholder": "true"},
          {"key": "recommended_system_prompt", "tab": "dialog_input", "type": "var_textarea", "label": "true", "value": "", "required": true},
          {"key": "recommended_history_num", "tab": "dialog_input", "help": "true", "step": 1, "type": "slide", "label": "true", "scope": [1, 10], "value": 2}
        ],
        "groupKey": "custom"
      },
      {
        "name": "",
        "params": [
          {
            "key": "form_input",
            "tab": "form_input",
            "type": "form",
            "label": "true",
            "value": [
              {"key": "query", "type": "text", "value": "问题", "options": [], "multiple": false, "required": true, "file_path": "file_path", "file_type": "all", "image_file": "image_file", "file_content": "file_content", "file_parse_mode": "extract_text", "file_content_size": 15000}
            ],
            "global": "item:form_input"
          }
        ]
      }
    ]
  },
  "type": "flowNode",
  "dragging": false,
  "measured": {"width": 334, "height": 358},
  "position": {"x": 350, "y": 200}
}
```

**变量引用格式**: `{{#input_xxx.字段key#}}`
- 例如: `{{#input_4c5d6.user_text#}}`
- 需要在使用变量的节点添加 `varZh` 字段: `"varZh": {"input_4c5d6.user_text": "输入/user_text"}`

### 4. 大模型节点 (llm) 检查

| 检查项 | 要求 | 错误示例 → 正确示例 |
|--------|------|---------------------|
| var_textarea | 必须有 `test: "var"` | `{"key": "system_prompt", "type": "var_textarea"}` → 添加 `"test": "var"` |
| model_id | 类型为数字 | `"model_id": "gpt-4"` → `"model_id": 1` |
| temperature | 值范围 [0, 2] | `"temperature": 3` → `"temperature": 0.7` |
| varZh | **必须有** | 变量中文映射，用于前端下拉框显示 |

**⚠️ varZh 字段说明**:
`varZh` 是变量在 UI 中显示的中文名称映射，格式为 `"节点ID.变量名": "节点名称/变量名称"`。
如果没有 `varZh`，前端下拉框中可能无法正确显示变量选项。

**正确示例**:
```json
{
  "key": "system_prompt",
  "type": "var_textarea",
  "test": "var",
  "value": "你是一个助手"
},
{
  "key": "user_prompt",
  "type": "var_textarea",
  "test": "var",
  "value": "{{#input_xxx.query#}}",
  "required": true,
  "varZh": {
    "input_xxx.query": "输入/query"
  }
}
```

### 5. 代码节点 (code) 检查

| 检查项 | 要求 | 错误示例 → 正确示例 |
|--------|------|---------------------|
| code_input.type | 必须是 `"code_input"` | 正确 |
| code_input.test | 必须是 `"input"` | 缺失 → 添加 `"test": "input"` |
| code_input.required | 必须是 `true` | 缺失 → 添加 `"required": true` |
| code.type | 必须是 `"code"` | 正确 |
| code.required | 必须是 `true` | 缺失 → 添加 `"required": true` |
| code_output.type | 必须是 `"code_output"` | 正确 |
| code_output.required | 必须是 `true` | 缺失 → 添加 `"required": true` |
| code_output.global | 必须有 | 缺失 → 添加 `"global": "code:value.map(el => ({ label: el.key, value: el.key }))"` |
| 入参value | 每项要有 `key`, `type`, `label`, `value` | 缺失 `label` → 添加 `"label": "描述"` |

**正确示例**:
```json
{
  "name": "入参",
  "params": [{
    "key": "code_input",
    "type": "code_input",
    "test": "input",
    "required": true,
    "value": [
      {"key": "data", "type": "ref", "label": "数据", "value": "llm_xxx.output"}
    ]
  }]
},
{
  "name": "出参",
  "params": [{
    "key": "code_output",
    "type": "code_output",
    "required": true,
    "global": "code:value.map(el => ({ label: el.key, value: el.key }))",
    "value": [
      {"key": "result", "type": "str"}
    ]
  }]
}
```

### 6. 输出节点 (output) 检查

| 检查项 | 要求 | 错误示例 → 正确示例 |
|--------|------|---------------------|
| message.type | 必须是 `"var_textarea_file"` | 正确 |
| message.label | 必须是 `"true"` | 缺失 → 添加 `"label": "true"` |
| message.global | 必须是 `"key"` | 缺失 → 添加 `"global": "key"` |
| message.required | 必须是 `true` | 缺失 → 添加 `"required": true` |
| message.placeholder | 建议添加 | 缺失 → 添加 `"placeholder": "true"` |
| message.varZh | 建议添加变量映射 | 缺失 → 添加变量中文描述 |

**正确示例**:
```json
{
  "key": "message",
  "type": "var_textarea_file",
  "label": "true",
  "global": "key",
  "required": true,
  "placeholder": "true",
  "value": {
    "msg": "{{#llm_xxx.output#}}",
    "files": []
  },
  "varZh": {
    "llm_xxx.output": "大模型/output"
  }
}
```

### 7. 边(Edge)检查

| 检查项 | 要求 | 错误示例 → 正确示例 |
|--------|------|---------------------|
| id | 格式 `xy-edge__sourceHandle-targetHandle` | `"e1"` → `"xy-edge__start_1a2b3right_handle-input_4c5d6left_handle"` |
| type | 必须是 `"customEdge"` | 正确 |
| source | 必须是存在的节点ID | 与nodes中的id匹配 |
| target | 必须是存在的节点ID | 与nodes中的id匹配 |
| animated | 必须是 `true` | 正确 |
| sourceHandle | 必须是 `"right_handle"` 或条件ID | 正确 |
| targetHandle | 必须是 `"left_handle"` | 正确 |

**正确示例**:
```json
{
  "id": "xy-edge__start_1a2b3right_handle-input_4c5d6left_handle",
  "type": "customEdge",
  "source": "start_1a2b3",
  "target": "input_4c5d6",
  "animated": true,
  "sourceHandle": "right_handle",
  "targetHandle": "left_handle"
}
```

### 8. 变量引用检查

| 检查项 | 要求 |
|--------|------|
| 格式 | `{{#节点ID.参数名#}}` |
| 节点存在 | 引用的节点ID必须在nodes中存在 |
| 参数存在 | 引用的参数必须是节点的输出变量 |

### 9. 检查流程

生成JSON后执行以下检查步骤：

```
1. JSON格式验证 - 确保是有效JSON
2. 顶层结构检查 - name, status, flow_type, nodes, edges, viewport
3. 遍历nodes:
   - 检查 id, type, position, data.type, data.v
   - 根据节点类型执行专项检查
4. 遍历edges:
   - 检查 id格式, source, target, sourceHandle, targetHandle
   - 验证source/target引用的节点存在
5. 变量引用检查:
   - 提取所有 {{#...#}} 引用
   - 验证节点ID和参数存在
6. 输出检查报告，修复所有错误
```

---

## 执行指令

当用户请求生成工作流时：

1. **分析需求**: 识别节点类型、参数、连接顺序
2. **生成JSON**: 按模板结构生成完整JSON
3. **预览图表**: 生成PlantUML展示工作流结构
4. **语法检查**: 按上述清单逐项检查，修复所有错误
5. **输出文件**: 保存为 `workflow_xxx.json` 供用户导入

**重要**: 第4步语法检查必须执行，不得跳过！