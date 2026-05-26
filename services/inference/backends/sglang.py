import httpx
from typing import List, Dict, Any, Optional
from inference.backends.base import BaseInferenceBackend

class SGLangBackend(BaseInferenceBackend):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            return {
                "model": data["model"],
                "message": {
                    "role": choice["message"]["role"],
                    "content": choice["message"]["content"],
                },
                "usage": data.get("usage", {})
            }
