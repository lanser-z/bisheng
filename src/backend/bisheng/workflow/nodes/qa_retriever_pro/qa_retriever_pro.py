"""
QA知识库检索Pro节点

与 qa_retriever 节点的区别：
- qa_retriever: 知识库ID在配置时固定选择
- qa_retriever_pro: 知识库ID在运行时从变量动态获取

适用场景：
- 根据用户输入动态切换知识库
- 多租户场景下按租户ID选择知识库
- 条件分支后选择不同的知识库
"""
import json
from typing import Any, Dict, List, Union

from loguru import logger

from bisheng.interface.initialize.loading import instantiate_vectorstore
from bisheng.interface.vector_store.custom import MilvusWithPermissionCheck
from bisheng.user.domain.models.user import UserDao
from bisheng.workflow.nodes.base import BaseNode
from bisheng_langchain.chains.retrieval.retrieval_chain import RetrievalChain


class QARetrieverProNode(BaseNode):
    """
    QA知识库检索Pro节点

    支持运行时动态获取知识库ID，实现灵活的知识库切换
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 用户问题变量引用
        self._user_question = self.node_params.get('user_question', '')

        # 知识库ID变量引用（核心差异：从变量获取而非固定配置）
        self._qa_knowledge_id_variable = self.node_params.get('qa_knowledge_id_variable', '')

        # 相似度阈值
        self._score = self.node_params.get('score', 0.6)

    def _parse_knowledge_id(self, knowledge_id_value: Any) -> List[str]:
        """
        解析知识库ID，支持多种格式

        支持格式：
        - 字符串: "knowledge_123"
        - 列表: ["knowledge_123", "knowledge_456"]
        - 选择器格式: [{"key": "knowledge_123", "label": "产品手册"}]

        Returns:
            知识库ID字符串列表
        """
        if not knowledge_id_value:
            return []

        if isinstance(knowledge_id_value, str):
            return [knowledge_id_value]

        if isinstance(knowledge_id_value, list):
            result = []
            for item in knowledge_id_value:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict) and 'key' in item:
                    result.append(item['key'])
            return result

        return [str(knowledge_id_value)]

    def _create_retriever(self, knowledge_ids: List[str]) -> RetrievalChain:
        """
        创建检索器实例

        Args:
            knowledge_ids: 知识库ID列表

        Returns:
            RetrievalChain 实例
        """
        if not knowledge_ids:
            raise ValueError("知识库ID不能为空")

        params = {}
        params['search_kwargs'] = {'k': 1, 'score_threshold': self._score}
        params['search_type'] = 'similarity_score_threshold'
        # instantiate_vectorstore 期望 collection_name 格式为 [{'key': 'knowledge_id'}]
        params['collection_name'] = [{'key': kid} for kid in knowledge_ids]
        params['user_name'] = UserDao.get_user(self.user_id).user_name
        params['_is_check_auth'] = False

        knowledge_retriever = instantiate_vectorstore(
            node_type='MilvusWithPermissionCheck',
            class_object=MilvusWithPermissionCheck,
            params=params,
        )

        return RetrievalChain(retriever=knowledge_retriever)

    def _run(self, unique_id: str) -> Dict[str, Any]:
        """
        执行节点逻辑

        核心流程：
        1. 从变量获取知识库ID
        2. 解析知识库ID
        3. 创建检索器
        4. 执行检索
        5. 返回结果
        """
        # 1. 获取用户问题
        question = self.get_other_node_variable(self._user_question)
        if not question:
            logger.warning(f"节点 {self.name}: 用户问题为空")
            return {'retrieved_result': ''}

        # 2. 从变量获取知识库ID（核心差异点）
        knowledge_id_value = self.get_other_node_variable(self._qa_knowledge_id_variable)
        if not knowledge_id_value:
            logger.warning(f"节点 {self.name}: 知识库ID变量 {self._qa_knowledge_id_variable} 的值为空")
            return {'retrieved_result': ''}

        # 3. 解析知识库ID
        knowledge_ids = self._parse_knowledge_id(knowledge_id_value)
        if not knowledge_ids:
            logger.warning(f"节点 {self.name}: 无法解析知识库ID: {knowledge_id_value}")
            return {'retrieved_result': ''}

        logger.info(f"节点 {self.name}: 使用知识库 {knowledge_ids} 检索问题: {question}")

        # 4. 创建检索器（每次执行时创建，支持动态切换）
        retriever = self._create_retriever(knowledge_ids)

        # 5. 执行检索
        result = retriever.invoke({'query': question})

        # 6. 处理结果
        if result['result']:
            # 存储原始文档对象供后续使用
            self.graph_state.set_variable(self.id, '$retrieved_result$', result['result'][0])
            # 提取答案文本
            try:
                result_str = json.loads(result['result'][0].metadata['extra'])['answer']
            except (KeyError, json.JSONDecodeError) as e:
                logger.warning(f"节点 {self.name}: 解析答案失败: {e}")
                result_str = result['result'][0].page_content
        else:
            result_str = ''
            self.graph_state.set_variable(self.id, '$retrieved_result$', None)

        return {
            'retrieved_result': result_str
        }

    def parse_log(self, unique_id: str, result: dict) -> Any:
        """
        定义执行日志格式
        """
        # 获取实际使用的知识库ID
        knowledge_id_value = self.get_other_node_variable(self._qa_knowledge_id_variable)
        knowledge_ids = self._parse_knowledge_id(knowledge_id_value)

        return [[
            {
                "key": "user_question",
                "value": self.get_other_node_variable(self._user_question),
                "type": "params"
            },
            {
                "key": "knowledge_ids",
                "value": knowledge_ids,
                "type": "params"
            },
            {
                "key": "retrieved_result",
                "value": result['retrieved_result'],
                "type": "params"
            }
        ]]