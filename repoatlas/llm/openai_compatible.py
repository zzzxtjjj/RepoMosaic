import httpx
from repoatlas.llm.base import LLMError
from repoatlas.llm.config import LLMConfig


class OpenAICompatibleClient:
    """
    通过 OpenAI-compatible HTTP API 调用用户指定的大模型服务。
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    # 向兼容的大模型接口发送 prompt，并返回模型生成的纯文本结果
    def generate(self, prompt: str) -> str:
    
        if not self.config.base_url:
            raise ValueError(
                "base_url is required for an OpenAI-compatible provider."
            )

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
     
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
      
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # 向模型服务发送 HTTP POST 请求
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise LLMError(
                "LLM request timed out."
            ) from error

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code

            if status_code in (401, 403):
                raise LLMError(
                    f"LLM authentication failed (HTTP {status_code})."
                )

            if status_code == 429:
                raise LLMError(
                    "LLM rate limit exceeded (HTTP 429)."
                ) from error

            if status_code >= 500:
                raise LLMError(
                    f"LLM service error (HTTP {status_code})."
                ) from error
            
            raise LLMError(
                f"LLM request failed (HTTP {status_code})."
            ) from error

        except httpx.RequestError as error:
            raise LLMError(
                "Could not connect to the LLM service."
            ) from error

        try:
            data = response.json()

        except ValueError as error:
            raise LLMError(
                "LLM returned an invalid JSON response."
            ) from error

        try:
            content = data["choices"][0]["message"]["content"]

        except (KeyError, IndexError, TypeError) as error:
            raise LLMError(
                "LLM returned an unexpected response format."
            ) from error

        if not isinstance(content, str):
            raise LLMError(
                "LLM returned an unexpected response format."
            )

        return content
