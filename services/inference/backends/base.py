from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseInferenceBackend(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes a chat completion query against the target LLM backend.
        """
        pass
