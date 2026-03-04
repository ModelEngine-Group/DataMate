"""
DashScope 重排序客户端

DashScope 的 rerank API 不支持 OpenAI 兵容模式,需要使用原生 API 端点。
参考: https://help.aliyun.com/zh/model-studio/developer-reference/api-rerank
"""

import logging
from typing import List, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DashScopeRerankRequest(BaseModel):
    """DashScope rerank request format"""

    model: str
    input: dict  # DashScope uses 'input' instead of 'query' + 'documents'
    parameters: Optional[dict] = None


class DashScopeRerankResult(BaseModel):
    """DashScope rerank result"""

    index: int
    relevance_score: float
    document: Optional[str] = None


class DashScopeRerankResponse(BaseModel):
    """DashScope rerank API response"""

    output: dict  # DashScope wraps results in 'output'


class DashScopeRerankClient:
    """DashScope 原生 rerank API 客户端

    用于调用不支持 OpenAI 兼容模式的 DashScope rerank API。
    API 端点: https://dashscope.aliyuncs.com/api/v1/services/rerank/rerank
    """

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        """初始化客户端

        Args:
            api_key: DashScope API Key
            model_name: 模型名称 (如 gte-rerank)
            base_url: 可选的自定义 API 端点
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url or "https://dashscope.aliyuncs.com"
        self.api_endpoint = f"{self.base_url}/api/v1/services/rerank/rerank"

        logger.info(
            f"DashScopeRerankClient initialized - model: {model_name}, endpoint: {self.api_endpoint}"
        )

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[DashScopeRerankResult]:
        """执行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前K个结果

        Returns:
            重排序结果列表
        """
        if not documents:
            return []

        request_body = {
            "model": self.model_name,
            "input": {"query": query, "documents": documents},
            "parameters": {"top_k": top_k},
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            logger.debug(f"Sending rerank request to: {self.api_endpoint}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers=headers,
                    json=request_body,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Rerank API call failed with status: {response.status_code}, body: {response.text}"
                    )
                    raise RuntimeError(
                        f"Rerank API call failed: {response.status_code}"
                    )

                response_json = response.json()
                logger.debug(f"Received rerank response: {response_json}")

                # Parse DashScope response format
                if "output" not in response_json:
                    logger.error(f"Invalid response format: {response_json}")
                    raise RuntimeError(
                        "Invalid response format: missing 'output' field"
                    )

                results_data = response_json["output"].get("results", [])
                results = []
                for item in results_data:
                    results.append(
                        DashScopeRerankResult(
                            index=item.get("index", 0),
                            relevance_score=item.get("relevance_score", 0.0),
                            document=item.get("document"),
                        )
                    )

                logger.info(f"Successfully reranked {len(results)} documents")
                return results[:top_k]

        except Exception as e:
            logger.error(f"Rerank API call failed: {str(e)}")
            raise RuntimeError(f"Rerank API call failed: {str(e)}") from e
