# BISHENG 工作流节点开发指南

## 触发条件

当用户请求以下任务时自动触发此技能：
- 新增工作流节点
- 添加自定义节点类型
- 修改现有节点功能
- 开发节点组件
- 实现节点执行逻辑

---

## 概述

BISHENG 工作流引擎基于 LangGraph 构建，采用节点-边（Node-Edge）图结构。每个节点是独立的功能单元，通过全局变量池进行数据传递。

### 核心架构

```
workflow/
├── common/                    # 公共定义
│   ├── node.py               # NodeType枚举、BaseNodeData
│   └── workflow.py           # WorkflowStatus
├── graph/                     # 图引擎
│   ├── graph_engine.py       # LangGraph执行引擎
│   └── graph_state.py        # 全局状态/变量池
├── nodes/                     # 节点实现
│   ├── base.py               # BaseNode抽象基类
│   ├── node_manage.py        # NodeFactory工厂
│   ├── start/                # 开始节点
│   ├── end/                  # 结束节点
│   ├── llm/                  # LLM节点
│   ├── rag/                  # RAG节点
│   ├── agent/                # Agent节点
│   ├── tool/                 # 工具节点
│   ├── code/                 # 代码节点
│   ├── condition/            # 条件节点
│   ├── input/                # 输入节点
│   ├── output/               # 输出节点
│   ├── report/               # 报告节点
│   ├── knowledge_retriever/  # 知识检索节点
│   └── qa_retriever/         # QA检索节点
├── edges/                     # 边管理
│   └── edges.py              # EdgeManage
└── callback/                  # 回调机制
    ├── base_callback.py      # BaseCallback
    └── event.py              # 事件定义
```

---

## 新增节点完整步骤

### 步骤 1: 定义节点类型枚举

**文件**: `src/backend/bisheng/workflow/common/node.py`

在 `NodeType` 枚举中添加新类型：

```python
class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    INPUT = "input"
    OUTPUT = "output"
    LLM = "llm"
    # ... 现有类型

    # 新增节点类型
    MY_NEW_NODE = "my_new_node"
```

---

### 步骤 2: 创建节点目录结构

```
src/backend/bisheng/workflow/nodes/my_new_node/
├── __init__.py
└── my_new_node.py
```

---

### 步骤 3: 实现节点类

**文件**: `src/backend/bisheng/workflow/nodes/my_new_node/my_new_node.py`

```python
from typing import Any, Dict, List, Optional
from loguru import logger

from bisheng.workflow.nodes.base import BaseNode
from bisheng.workflow.callback.event import NodeEndData


class MyNewNode(BaseNode):
    """
    自定义节点实现

    节点功能：[描述节点的核心功能]
    输入参数：[描述输入参数]
    输出结果：[描述输出结果]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化节点参数
        # 参数从 node_params 中获取，由前端配置传入
        self._param1 = self.node_params.get('param1', 'default_value')
        self._param2 = self.node_params.get('param2', [])

        # 初始化内部状态
        self._log_data = []

    def _run(self, unique_id: str) -> Dict[str, Any]:
        """
        节点执行核心逻辑 - 必须实现

        Args:
            unique_id: 本次执行的唯一标识

        Returns:
            Dict[str, Any]: 返回结果会存入全局变量池
                格式: {变量名: 变量值}
                其他节点可通过 {node_id.变量名} 访问
        """
        self._log_data = []

        try:
            # 1. 获取其他节点的变量
            input_data = self._get_input_variables()

            # 2. 执行核心业务逻辑
            result = self._execute_logic(input_data)

            # 3. 处理输出
            output = self._process_output(result)

            return output

        except Exception as e:
            logger.exception(f'{self.name} node execute error: {e}')
            raise e

    def _get_input_variables(self) -> Dict[str, Any]:
        """
        从全局变量池获取其他节点的输出
        """
        input_vars = {}

        # 获取单个变量: node_id.variable_key
        # 示例: 获取开始节点的用户输入
        user_input = self.get_other_node_variable('start.user_input')
        input_vars['user_input'] = user_input

        # 获取带索引的变量: node_id.variable_key#index
        # 示例: 获取列表的第一个元素
        first_item = self.get_other_node_variable('rag.output#0')
        input_vars['first_item'] = first_item

        return input_vars

    def _execute_logic(self, input_data: Dict[str, Any]) -> Any:
        """
        执行节点的核心业务逻辑
        """
        # TODO: 实现具体的业务逻辑
        result = f"处理结果: {input_data}"
        return result

    def _process_output(self, result: Any) -> Dict[str, Any]:
        """
        处理输出结果
        """
        return {
            'output': result,
            'status': 'success'
        }

    def parse_log(self, unique_id: str, result: dict) -> Any:
        """
        定义节点执行日志格式

        返回格式:
        [
            [
                {"key": "参数名", "value": "参数值", "type": "params"},
                {"key": "变量名", "value": "变量值", "type": "variable"},
                {"key": "工具名", "value": "工具输出", "type": "tool"}
            ]
        ]
        """
        log_entry = []

        # 添加输入参数日志
        log_entry.append({
            "key": "param1",
            "value": self._param1,
            "type": "params"
        })

        # 添加输出变量日志
        log_entry.append({
            "key": f"{self.id}.output",
            "value": result.get('output'),
            "type": "variable"
        })

        return [log_entry]

    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """
        返回用户输入表单的schema（用于Human in the Loop）

        如果节点需要用户在执行过程中输入数据，返回表单定义
        否则返回 None

        Returns:
            表单schema定义
        """
        # 如果不需要用户交互，返回 None
        return None

        # 如果需要用户交互，返回表单定义
        # return {
        #     "type": "object",
        #     "properties": {
        #         "user_confirm": {
        #             "type": "boolean",
        #             "title": "确认执行",
        #             "default": False
        #         }
        #     }
        # }

    def route_node(self, state: dict) -> str:
        """
        条件路由逻辑（仅条件节点需要实现）

        Returns:
            下一个要执行的节点ID
        """
        # 仅 condition 类型节点需要实现
        raise NotImplementedError
```

---

### 步骤 4: 注册节点到工厂

**文件**: `src/backend/bisheng/workflow/nodes/node_manage.py`

```python
from bisheng.workflow.common.node import NodeType
from bisheng.workflow.nodes.my_new_node.my_new_node import MyNewNode

# 节点类型到节点类的映射
NODE_CLASS_MAP = {
    NodeType.START.value: StartNode,
    NodeType.END.value: EndNode,
    NodeType.INPUT.value: InputNode,
    NodeType.OUTPUT.value: OutputNode,
    NodeType.LLM.value: LLMNode,
    NodeType.RAG.value: RagNode,
    NodeType.AGENT.value: AgentNode,
    NodeType.TOOL.value: ToolNode,
    NodeType.CODE.value: CodeNode,
    NodeType.CONDITION.value: ConditionNode,
    NodeType.REPORT.value: ReportNode,
    NodeType.QA_RETRIEVER.value: QARetrieverNode,
    NodeType.KNOWLEDGE_RETRIEVER.value: KnowledgeRetriever,

    # 注册新节点
    NodeType.MY_NEW_NODE.value: MyNewNode,
}
```

---

### 步骤 5: 前端类型定义

**文件**: `src/frontend/platform/src/types/flow/index.ts`

```typescript
export interface WorkflowNode {
  id: string;
  name: string;
  description: string;
  type: string; // 添加 'my_new_node' 类型支持
  group_params: {
    name?: string;
    groupKey?: string;
    params: WorkflowNodeParam[];
  }[];
  tab?: {
    value: string;
    options: {
      label: string;
      key: string;
      help?: string;
    }[];
  };
  tool_id?: string;
}
```

---

## BaseNode 基类参考

### 核心属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 节点唯一标识 |
| `type` | str | 节点类型 |
| `name` | str | 节点名称 |
| `node_data` | BaseNodeData | 节点完整数据 |
| `node_params` | dict | 节点参数（已处理） |
| `graph_state` | GraphState | 全局状态管理 |
| `callback_manager` | BaseCallback | 回调管理器 |
| `workflow_id` | str | 工作流ID |
| `user_id` | int | 用户ID |

### 核心方法

| 方法 | 必须 | 说明 |
|------|------|------|
| `_run(unique_id)` | ✓ | 节点执行核心逻辑 |
| `parse_log(unique_id, result)` | | 定义执行日志格式 |
| `get_input_schema()` | | 返回用户输入表单schema |
| `route_node(state)` | | 条件节点路由逻辑 |
| `get_other_node_variable(key)` | | 获取其他节点变量 |
| `parse_msg_with_variables(msg)` | | 解析带变量的消息 |
| `handle_input(user_input)` | | 处理用户输入 |

---

## 节点类型说明

### 1. 普通执行节点

标准执行节点，处理输入并产生输出。

**示例**: LLM节点、RAG节点、代码节点、工具节点

### 2. 交互节点

需要用户在执行过程中输入数据，实现 Human in the Loop。

**实现要点**:
- 重写 `get_input_schema()` 返回表单定义
- 节点会在执行时暂停，等待用户输入
- 用户输入后通过 `handle_input()` 处理

**示例**: 输入节点、输出节点

### 3. 条件节点

根据条件决定执行分支。

**实现要点**:
- 重写 `route_node(state)` 返回下一节点ID
- 返回值必须与边的 `sourceHandle` 对应

**示例**: 条件节点

### 4. 特殊节点

**开始节点**:
- 初始化全局状态
- 设置预设问题、引导语
- 输出用户信息、当前时间等

**结束节点**:
- 工作流终点
- 无输出

---

## 全局变量池使用

### GraphState 核心方法

```python
# 设置变量
graph_state.set_variable(node_id, key, value)

# 获取变量
graph_state.get_variable(node_id, key)
graph_state.get_variable_by_str("node_id.key")
graph_state.get_variable_by_str("node_id.key#index")  # 带索引

# 获取所有变量
graph_state.get_all_variables()

# 聊天历史
graph_state.get_history_memory(count)
graph_state.save_context(content, msg_sender)
```

### 变量访问语法

| 语法 | 说明 |
|------|------|
| `{node_id.key}` | 访问节点的输出变量 |
| `{node_id.key#index}` | 访问列表/字典的指定元素 |
| `{start.chat_history}` | 访问聊天历史 |
| `{start.user_info}` | 访问用户信息 |
| `{start.current_time}` | 访问当前时间 |

---

## 实际案例参考

### 案例1: LLM节点

位置: `workflow/nodes/llm/llm.py`

特点:
- 支持单次和批量执行
- 支持图片输入
- 支持流式输出回调

### 案例2: RAG节点

位置: `workflow/nodes/rag/rag.py`

特点:
- 集成知识库检索
- 支持重排序
- 支持多种检索策略

### 案例3: 条件节点

位置: `workflow/nodes/condition/condition.py`

特点:
- 实现条件分支
- 重写 `route_node()` 方法

### 案例4: 工具节点

位置: `workflow/nodes/tool/tool.py`

特点:
- 动态加载工具
- 支持参数模板

---

## 前端节点配置

节点参数通过前端配置，存储在 `BaseNodeData.group_params` 中。

### 参数类型

```typescript
interface WorkflowNodeParam {
  key: string;          // 参数键
  label?: string;       // 显示标签
  type: string;         // 参数类型
  value: any;           // 参数值
  placeholder?: string; // 占位符
  help?: string;        // 帮助文本
  tab?: string;         // 所属tab
  required?: boolean;   // 是否必填
  multi?: boolean;      // 是否多值
  options?: any[];      // 选项列表
}
```

### 参数类型对照

| type | 说明 | value格式 |
|------|------|-----------|
| `str` | 字符串 | `"text"` |
| `int` | 整数 | `123` |
| `float` | 浮点数 | `1.5` |
| `bool` | 布尔 | `true/false` |
| `select` | 单选 | `"option1"` |
| `multiselect` | 多选 | `["opt1", "opt2"]` |
| `dict` | 字典 | `{key: value}` |
| `list` | 列表 | `[item1, item2]` |
| `code` | 代码 | `"def func():..."` |
| `prompt` | 提示词模板 | `"你好，{name}"` |
| `file` | 文件路径 | `"/path/to/file"` |

---

## 调试与测试

### 单元测试示例

```python
import pytest
from bisheng.workflow.nodes.my_new_node.my_new_node import MyNewNode
from bisheng.workflow.common.node import BaseNodeData

def test_my_new_node():
    # 构造节点数据
    node_data = BaseNodeData(
        id="test_node",
        type="my_new_node",
        name="测试节点",
        group_params=[{
            "name": "基础配置",
            "params": [{
                "key": "param1",
                "value": "test_value"
            }]
        }]
    )

    # 创建节点实例
    node = MyNewNode(
        node_data=node_data,
        workflow_id="test_workflow",
        user_id=1,
        graph_state=GraphState(),
        target_edges=[],
        max_steps=10,
        callback=BaseCallback()
    )

    # 执行节点
    result = node._run("test_unique_id")

    # 验证结果
    assert 'output' in result
    assert result['status'] == 'success'
```

---

## 常见问题

### Q1: 如何获取其他节点的输出？

```python
# 方式1: 直接获取
output = self.get_other_node_variable('llm_node.output')

# 方式2: 解析模板字符串
msg, variables = self.parse_msg_with_variables("你好，{start.user_info}")
```

### Q2: 如何实现流式输出？

```python
from bisheng.workflow.callback.llm_callback import LLMNodeCallbackHandler
from langchain_core.runnables import RunnableConfig

llm_callback = LLMNodeCallbackHandler(
    callback=self.callback_manager,
    unique_id=unique_id,
    node_id=self.id,
    node_name=self.name
)
config = RunnableConfig(callbacks=[llm_callback])
result = self._llm.invoke(inputs, config=config)
```

### Q3: 如何实现 Human in the Loop？

```python
def get_input_schema(self) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "title": "确认执行",
                "default": True
            },
            "comment": {
                "type": "string",
                "title": "备注"
            }
        },
        "required": ["confirm"]
    }

def _run(self, unique_id: str) -> Dict[str, Any]:
    # 节点会在此暂停，等待用户输入
    # 用户输入后继续执行
    user_input = self.node_params.get('user_input', {})
    # 处理用户输入...
```

### Q4: 如何处理多分支节点？

```python
def route_node(self, state: dict) -> str:
    # 根据条件返回下一个节点ID
    condition = self.node_params.get('condition')

    if condition == 'A':
        return 'node_a'  # 对应 sourceHandle
    else:
        return 'node_b'
```

---

## 检查清单

新增节点完成后，确认以下事项：

- [ ] `NodeType` 枚举已添加新类型
- [ ] 节点类继承 `BaseNode` 并实现 `_run()` 方法
- [ ] `NODE_CLASS_MAP` 已注册新节点
- [ ] 前端类型定义已更新
- [ ] 单元测试已编写
- [ ] 文档已更新

---

## 相关文件快速导航

| 功能 | 文件路径 |
|------|----------|
| 节点类型枚举 | `workflow/common/node.py` |
| 节点基类 | `workflow/nodes/base.py` |
| 节点工厂 | `workflow/nodes/node_manage.py` |
| 图执行引擎 | `workflow/graph/graph_engine.py` |
| 全局状态 | `workflow/graph/graph_state.py` |
| 回调基类 | `workflow/callback/base_callback.py` |
| 前端类型 | `frontend/platform/src/types/flow/index.ts` |