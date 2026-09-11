from typing import Protocol


class LLMClient(Protocol):
    """定义 RepoAtlas LLM 客户端需要实现的最小接口。"""

    def generate(self, prompt: str) -> str:
        """根据 prompt 返回模型生成的文本。"""
        ...
