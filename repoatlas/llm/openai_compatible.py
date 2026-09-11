import httpx

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
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
        data = response.json()
        
        return data["choices"][0]["message"]["content"]
