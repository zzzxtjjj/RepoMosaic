import pytest

from repoatlas.llm.config import LLMConfig
from repoatlas.llm.factory import create_llm_client
from repoatlas.llm.openai_compatible import OpenAICompatibleClient


def test_create_openai_compatible_client():
    """验证 Factory 为已支持的 provider 创建正确客户端。"""
    config = LLMConfig(
        provider="openai-compatible",
        model="test-model",
        base_url="https://example.com/v1",
    )

    client = create_llm_client(config)

    assert isinstance(client, OpenAICompatibleClient)
    assert client.config is config


def test_unknown_provider_raises_clear_error():
    """验证未知 provider 的异常包含原始 provider 名称。"""
    config = LLMConfig(
        provider="unknown-provider",
        model="test-model",
    )

    with pytest.raises(ValueError, match="unknown-provider"):
        create_llm_client(config)
