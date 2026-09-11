from dataclasses import dataclass


# 保存用户选择的大模型提供方、模型名称和连接配置
@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None