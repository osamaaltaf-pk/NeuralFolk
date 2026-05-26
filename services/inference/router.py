from typing import Dict, List, Any, Optional
import structlog
from inference.backends.base import BaseInferenceBackend
from inference.backends.ollama import OllamaBackend
from inference.backends.vllm import VLLMBackend
from inference.backends.sglang import SGLangBackend
from inference.backends.llamacpp import LlamaCppBackend
from inference.backends.tensorrt import TensorRTBackend
from inference.backends.litert import LiteRTBackend
from core.config import settings

logger = structlog.get_logger()

class InferenceRouter:
    def __init__(self) -> None:
        # Load backend URLs dynamically from config/environment parameters
        self.backends: Dict[str, BaseInferenceBackend] = {
            "ollama": OllamaBackend(base_url=settings.OLLAMA_HOST),
            "vllm": VLLMBackend(base_url=getattr(settings, "VLLM_HOST", "http://vllm:8000")),
            "sglang": SGLangBackend(base_url=getattr(settings, "SGLANG_HOST", "http://sglang:30000")),
            "llamacpp": LlamaCppBackend(base_url=getattr(settings, "LLAMACPP_HOST", "http://llamacpp:8080")),
            "tensorrt": TensorRTBackend(base_url=getattr(settings, "TENSORRT_HOST", "http://tensorrt:8000")),
            "litert": LiteRTBackend(base_url="")
        }

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        task_type: Optional[str] = None,
        context_length: Optional[int] = None,
        batch_size: Optional[int] = 1,
        hardware: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically selects the best inference engine based on STACK.md rules:
        - context_length > 32k  -> SGLang
        - hardware == "no_gpu"   -> llama.cpp
        - batch_size > 4         -> vLLM
        - hardware == "nvidia"   -> TensorRT-LLM
        - hardware == "edge"     -> LiteRT
        
        Falls back gracefully to the active Ollama backend under Phase 1 if the
        chosen target backend is offline or unconfigured.
        """
        # Calculate context length dynamically if not explicitly provided
        char_count = sum(len(m.get("content", "")) for m in messages)
        est_tokens = char_count // 4
        ctx_len = context_length or est_tokens

        # 1. Evaluate routing selector
        target_backend = "ollama"  # Default fallback

        if ctx_len > 32000:
            target_backend = "sglang"
        elif hardware == "no_gpu" or getattr(settings, "ENVIRONMENT", "") == "cpu-only":
            target_backend = "llamacpp"
        elif batch_size and batch_size > 4:
            target_backend = "vllm"
        elif hardware == "nvidia":
            target_backend = "tensorrt"
        elif hardware == "edge":
            target_backend = "litert"

        await logger.ainfo(
            "inference_routing",
            selected_backend=target_backend,
            estimated_tokens=ctx_len,
            task_type=task_type,
            batch_size=batch_size
        )

        # 2. Attempt target execution, falling back gracefully to Ollama on failure
        try:
            backend = self.backends[target_backend]
            return await backend.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            if target_backend == "ollama":
                raise
            
            await logger.awarning(
                "inference_backend_fallback",
                failed_backend=target_backend,
                error=str(e),
                fallback_backend="ollama"
            )
            return await self.backends["ollama"].chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
