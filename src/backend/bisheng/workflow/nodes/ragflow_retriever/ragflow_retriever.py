"""
RagFlow检索节点

通过 RagFlow API 进行知识库检索，支持运行时动态配置知识库ID。

特点：
- 支持多知识库检索
- 支持相似度阈值、向量权重等参数配置
- 支持知识图谱检索（多跳）
- 支持跨语言检索
"""
import json
from typing import Any, Dict, List

import httpx
from loguru import logger

from bisheng.workflow.nodes.base import BaseNode


class RagFlowRetrieverNode(BaseNode):
    """
    RagFlow检索节点

    通过 RagFlow HTTP API 进行知识库检索
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # RagFlow服务配置
        self._api_url = self.node_params.get('ragflow_api_url', '').rstrip('/')
        self._api_key = self.node_params.get('ragflow_api_key', '')

        # 检索参数
        self._question_var = self.node_params.get('question', '')
        self._dataset_ids_var = self.node_params.get('dataset_ids', '')

        # 可选参数
        self._similarity_threshold = self.node_params.get('similarity_threshold', 0.2)
        self._vector_similarity_weight = self.node_params.get('vector_similarity_weight', 0.3)
        self._top_k = self.node_params.get('top_k', 1024)
        self._page_size = self.node_params.get('page_size', 10)
        self._rerank_id = self.node_params.get('rerank_id', '')
        self._use_kg = self.node_params.get('use_kg', False)
        self._keyword = self.node_params.get('keyword', False)

    def _parse_dataset_ids(self, dataset_ids_value: Any) -> List[str]:
        """
        解析知识库ID，支持多种格式

        支持格式：
        - 字符串: "dataset_123"
        - 逗号分隔: "dataset_123,dataset_456"
        - JSON列表: ["dataset_123", "dataset_456"]
        """
        if not dataset_ids_value:
            return []

        if isinstance(dataset_ids_value, list):
            return [str(item) for item in dataset_ids_value]

        if isinstance(dataset_ids_value, str):
            # 尝试解析JSON
            try:
                parsed = json.loads(dataset_ids_value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass

            # 逗号分隔
            if ',' in dataset_ids_value:
                return [s.strip() for s in dataset_ids_value.split(',') if s.strip()]

            return [dataset_ids_value]

        return [str(dataset_ids_value)]

    def _call_ragflow_api(self, question: str, dataset_ids: List[str]) -> Dict[str, Any]:
        """
        调用 RagFlow 检索 API
        """
        if not self._api_url or not self._api_key:
            raise ValueError("RagFlow API URL 或 API Key 未配置")

        url = f"{self._api_url}/api/v1/retrieval"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "question": question,
            "dataset_ids": dataset_ids,
            "similarity_threshold": self._similarity_threshold,
            "vector_similarity_weight": self._vector_similarity_weight,
            "top_k": self._top_k,
            "page_size": self._page_size,
            "keyword": self._keyword,
        }

        # 可选参数
        if self._rerank_id:
            payload["rerank_id"] = self._rerank_id
        if self._use_kg:
            payload["use_kg"] = self._use_kg

        logger.info(f"节点 {self.name}: 调用 RagFlow API, question={question}, dataset_ids={dataset_ids}")

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _run(self, unique_id: str) -> Dict[str, Any]:
        """
        执行检索逻辑
        """
        # 1. 获取问题
        question = self.get_other_node_variable(self._question_var)
        if not question:
            logger.warning(f"节点 {self.name}: 问题为空")
            return {'retrieved_result': '', 'chunks': []}

        # 2. 获取知识库ID
        dataset_ids_value = self.get_other_node_variable(self._dataset_ids_var)
        if not dataset_ids_value:
            logger.warning(f"节点 {self.name}: 知识库ID为空")
            return {'retrieved_result': '', 'chunks': []}

        dataset_ids = self._parse_dataset_ids(dataset_ids_value)
        if not dataset_ids:
            logger.warning(f"节点 {self.name}: 无法解析知识库ID: {dataset_ids_value}")
            return {'retrieved_result': '', 'chunks': []}

        # 3. 调用 RagFlow API
        try:
            result = self._call_ragflow_api(question, dataset_ids)
        except httpx.HTTPStatusError as e:
            logger.error(f"节点 {self.name}: RagFlow API 请求失败: {e}")
            return {'retrieved_result': f'检索失败: {e.response.text}', 'chunks': []}
        except Exception as e:
            logger.error(f"节点 {self.name}: RagFlow API 调用异常: {e}")
            return {'retrieved_result': f'检索异常: {str(e)}', 'chunks': []}

        # 4. 处理结果
        if result.get('code', 0) != 0:
            logger.error(f"节点 {self.name}: RagFlow API 返回错误: {result}")
            return {'retrieved_result': f"API错误: {result.get('message', '未知错误')}", 'chunks': []}

        chunks = result.get('data', {}).get('chunks', [])

        if not chunks:
            logger.info(f"节点 {self.name}: 未检索到相关内容")
            return {'retrieved_result': '', 'chunks': []}

        # 拼接检索结果
        content_list = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', '')
            similarity = chunk.get('similarity', 0)
            doc_name = chunk.get('document_name', '未知文档')
            content_list.append(f"[{i}] {content}\n(来源: {doc_name}, 相似度: {similarity:.3f})")

        retrieved_result = '\n\n'.join(content_list)

        logger.info(f"节点 {self.name}: 检索到 {len(chunks)} 条结果")

        # 存储原始chunks供后续节点使用
        self.graph_state.set_variable(self.id, '$chunks$', chunks)

        return {
            'retrieved_result': retrieved_result,
            'chunks': chunks
        }

    def parse_log(self, unique_id: str, result: dict) -> Any:
        """
        定义执行日志格式
        """
        return [[
            {
                "key": "question",
                "value": self.get_other_node_variable(self._question_var),
                "type": "params"
            },
            {
                "key": "dataset_ids",
                "value": self._parse_dataset_ids(self.get_other_node_variable(self._dataset_ids_var)),
                "type": "params"
            },
            {
                "key": "chunk_count",
                "value": len(result.get('chunks', [])),
                "type": "params"
            },
            {
                "key": "retrieved_result",
                "value": result.get('retrieved_result', '')[:500] + '...' if len(result.get('retrieved_result', '')) > 500 else result.get('retrieved_result', ''),
                "type": "params"
            }
        ]]