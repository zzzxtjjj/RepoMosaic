from repoatlas.llm.config import LLMConfig
from repoatlas.llm.openai_compatible import OpenAICompatibleClient
import pytest


# 模拟 HTTP 响应对象，避免测试时真的调用大模型 API
class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": "Hello from fake model"
                    }
                }
            ]
        }


# 验证 OpenAICompatibleClient 能正确发送请求并提取模型返回文本
def test_generate_returns_model_text(monkeypatch):

    # 保存 fake_post 收到的请求信息，方便后面断言
    captured_request = {}


    # 模拟 httpx.post，并记录 RepoAtlas 实际发送的请求
    def fake_post(url, headers, json):
        captured_request["url"] = url
        captured_request["headers"] = headers
        captured_request["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        "repoatlas.llm.openai_compatible.httpx.post",
        fake_post,
    )

    config = LLMConfig(
        provider="openai-compatible",
        model="test-model",
        api_key="test-key",
        base_url="https://example.com/v1/",
    )

    client = OpenAICompatibleClient(config)

    result = client.generate("Hello")

    assert result == "Hello from fake model"
    assert captured_request["url"] == (
        "https://example.com/v1/chat/completions"
    )
    assert captured_request["headers"]["Authorization"] == (
        "Bearer test-key"
    )
    assert captured_request["json"]["model"] == "test-model"
    assert captured_request["json"]["messages"][0]["content"] == "Hello"


# 验证没有 API key 时，请求头中不会添加 Authorization
def test_generate_without_api_key(monkeypatch):
    captured_request = {}

    def fake_post(url, headers, json):
        captured_request["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(
        "repoatlas.llm.openai_compatible.httpx.post",
        fake_post,
    )

    config = LLMConfig(
        provider="openai-compatible",
        model="local-model",
        api_key=None,
        base_url="http://localhost:8000/v1",
    )

    client = OpenAICompatibleClient(config)

    result = client.generate("Hello")

    assert result == "Hello from fake model"
    assert "Authorization" not in captured_request["headers"]


# 验证缺少 base_url 时，客户端会主动抛出明确的 ValueError
def test_generate_requires_base_url():
    config = LLMConfig(
        provider="openai-compatible",
        model="test-model",
        api_key="test-key",
        base_url=None,
    )

    client = OpenAICompatibleClient(config)

    with pytest.raises(ValueError, match="base_url"):
        client.generate("Hello")
