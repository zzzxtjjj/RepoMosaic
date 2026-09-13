from repomosaic.llm.base import LLMClient
from repomosaic.llm.config import LLMConfig
from repomosaic.llm.openai_compatible import OpenAICompatibleClient


# 根据用户的大模型配置，创建对应的 LLM Client
def create_llm_client(config: LLMConfig) -> LLMClient:

    if config.provider == "openai-compatible":
        return OpenAICompatibleClient(config)

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )