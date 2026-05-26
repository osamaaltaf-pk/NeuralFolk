from ollama import AsyncClient  # type: ignore[attr-defined]
from typing import List, Dict, Any, Optional
from inference.backends.base import BaseInferenceBackend
import structlog

logger = structlog.get_logger()

class OllamaBackend(BaseInferenceBackend):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.client = AsyncClient(host=base_url)

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        options = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )
            return {
                "model": response.get("model", model),
                "message": {
                    "role": response.get("message", {}).get("role", "assistant"),
                    "content": response.get("message", {}).get("content", ""),
                },
                "usage": {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0),
                    "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
                }
            }
        except Exception as e:
            await logger.aerror("ollama_chat_failed", error=str(e), host=self.base_url)
            raise
