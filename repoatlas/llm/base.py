from typing import Protocol


class LLMError(RuntimeError):
    """表示 RepoAtlas 调用大模型服务时发生的可预期错误。"""


class LLMClient(Protocol):
    """定义 RepoAtlas LLM 客户端需要实现的最小接口。"""

    def generate(self, prompt: str) -> str:
        """根据 prompt 返回模型生成的文本。"""
        ...
