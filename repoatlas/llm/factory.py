from repoatlas.llm.base import LLMClient
from repoatlas.llm.config import LLMConfig
from repoatlas.llm.openai_compatible import OpenAICompatibleClient


# 根据用户的大模型配置，创建对应的 LLM Client
def create_llm_client(config: LLMConfig) -> LLMClient:

    if config.provider == "openai-compatible":
        return OpenAICompatibleClient(config)

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )