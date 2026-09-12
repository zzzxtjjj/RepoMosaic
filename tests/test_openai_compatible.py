import httpx
import pytest

from repoatlas.llm.base import LLMError
from repoatlas.llm.config import LLMConfig
from repoatlas.llm.openai_compatible import OpenAICompatibleClient


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
    def fake_post(url, headers, json, timeout):
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

    def fake_post(url, headers, json, timeout):
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

# 创建测试使用的 OpenAI-compatible 客户端
def make_test_client() -> OpenAICompatibleClient:
    config = LLMConfig(
        provider="openai-compatible",
        model="test-model",
        api_key="test-key",
        base_url="https://example.com/v1",
    )
    return OpenAICompatibleClient(config)


# 验证 LLM 请求超时时，会转换成 RepoAtlas 自己的 LLMError
def test_generate_handles_timeout(monkeypatch):
    client = make_test_client()

    def fake_post(url, headers, json, timeout):
        raise httpx.TimeoutException(
            "request timed out",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match="LLM request timed out",
    ):
        client.generate("hello")


# 验证 401 认证错误不会直接暴露 httpx traceback
def test_generate_handles_authentication_error(monkeypatch):
    client = make_test_client()

    def fake_post(url, headers, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            401,
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match=r"authentication failed.*401",
    ):
        client.generate("hello")


# 验证 API 触发限流时，会返回明确的 RepoAtlas 错误
def test_generate_handles_rate_limit(monkeypatch):
    client = make_test_client()

    def fake_post(url, headers, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            429,
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match=r"rate limit exceeded.*429",
    ):
        client.generate("hello")


# 验证模型服务出现 5xx 错误时，会转换成统一的 LLMError
def test_generate_handles_server_error(monkeypatch):
    client = make_test_client()

    def fake_post(url, headers, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            500,
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match=r"service error.*500",
    ):
        client.generate("hello")


# 验证网络连接失败时，会转换成清晰的 RepoAtlas 错误
def test_generate_handles_connection_error(monkeypatch):
    client = make_test_client()

    def fake_post(url, headers, json, timeout):
        raise httpx.ConnectError(
            "connection failed",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match="Could not connect to the LLM service",
    ):
        client.generate("hello")


# 验证服务返回非法 JSON 时，不会泄露底层解析异常
def test_generate_handles_invalid_json(monkeypatch):
    client = make_test_client()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("invalid json")

    def fake_post(url, headers, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match="invalid JSON response",
    ):
        client.generate("hello")


# 验证服务返回合法 JSON 但结构不兼容时，会给出明确错误
def test_generate_handles_unexpected_response_format(monkeypatch):
    client = make_test_client()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "result": "hello",
            }

    def fake_post(url, headers, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(
        LLMError,
        match="unexpected response format",
    ):
        client.generate("hello")