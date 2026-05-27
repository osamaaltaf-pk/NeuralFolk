"""
Context Limit Diagnostics Test
==============================
This test progressively scales context input lengths (from 1k to 32k tokens)
to determine the exact hardware limits, latency, and memory footprints of the
local system.

Run with:
    pytest tests/integration/test_context_limits.py -v -s
"""
import pytest
import httpx
import time
import json
from typing import Dict, Any

MODEL = "openbmb/minicpm5:fp16"
OLLAMA_HOST = "http://localhost:11434"
TIMEOUT = 300.0  # Allow up to 5 minutes for extreme context prefill

# Base sentence approx 10 tokens
BASE_PADDED_SENTENCE = "The swift brown fox easily jumps over the lazy sleeping dog. "

def get_live_memory_usage() -> Dict[str, Any]:
    """Queries Ollama live memory endpoint to verify exact GPU VRAM and CPU footprint."""
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/ps", timeout=5.0)
        if r.status_code == 200:
            models = r.json().get("models", [])
            for m in models:
                if m.get("name") == MODEL:
                    return {
                        "size_total": m.get("size", 0),
                        "size_vram": m.get("size_vram", 0),
                        "context_length": m.get("context_length", 4096)
                    }
    except Exception:
        pass
    return {"size_total": 0, "size_vram": 0, "context_length": 0}


@pytest.mark.integration
def test_context_limits_matrix() -> None:
    """
    Tests local GPU/CPU hardware boundaries by sending prompts scaled to:
    - 1,000 tokens (Standard)
    - 4,000 tokens (Base context)
    - 8,000 tokens (Medium context)
    - 16,000 tokens (High context)
    - 32,000 tokens (Max engine context)
    
    Reports latency, throughput, and hardware VRAM footprint for each run.
    """
    # Probing Ollama reachability
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{OLLAMA_HOST}/api/tags")
        if r.status_code != 200:
            pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")
    except Exception:
        pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")

    # Matrix: (Token Count, Word Multiplier)
    context_matrix = [
        (1000, 100),
        (4000, 400),
        (8000, 800),
        (16000, 1600),
        (32000, 3200)
    ]

    print("\n" + "="*80)
    print("      NEURALFOLK CONTEXT RANGE & VRAM DIAGNOSTIC MATRIX")
    print("="*80)
    print(f"Model under test: {MODEL}")
    print("-"*80)

    for target_tokens, multiplier in context_matrix:
        # Construct large prompt
        padding_text = BASE_PADDED_SENTENCE * multiplier
        prompt = f"{padding_text}\n\n[TASK] Read all the text above. Reply with exactly the single word: 'DONE'."
        
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 10,
                "num_ctx": target_tokens + 500  # Expand Ollama context window size accordingly
            }
        }

        print(f"\n[DIAGNOSTIC] Testing Context Length: {target_tokens} tokens...")
        
        start_time = time.perf_counter()
        success = False
        error_msg = ""
        response_text = ""
        eval_count = 0
        prompt_eval_count = 0
        
        try:
            # Query the endpoint
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
                
            duration = time.perf_counter() - start_time
            
            if res.status_code == 200:
                success = True
                data = res.json()
                response_text = data.get("message", {}).get("content", "").strip()
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)
            else:
                error_msg = f"HTTP Error {res.status_code}: {res.text[:150]}"
        except Exception as e:
            duration = time.perf_counter() - start_time
            error_msg = str(e)

        # Query live memory statistics
        mem = get_live_memory_usage()
        vram_mb = mem["size_vram"] / 1024 / 1024
        total_mb = mem["size_total"] / 1024 / 1024

        # Output diagnostics
        if success:
            vram_status = f"{vram_mb:.1f} MB" if vram_mb > 0 else "0 MB (CPU fallback)"
            print(f"  --> [OK] Successfully completed in {duration:.2f} seconds!")
            print(f"      Tokens Processed: Prefill={prompt_eval_count}, Generation={eval_count}")
            print(f"      Latency Statistics: Prefill Speed = {prompt_eval_count / duration:.2f} tokens/sec")
            print(f"      GPU Allocations   : VRAM = {vram_status}, Total Memory = {total_mb:.1f} MB")
            print(f"      Response Received : '{response_text}'")
        else:
            print(f"  --> [FAIL] Context limit reached or failed at {target_tokens} tokens!")
            print(f"      Duration Elapsed: {duration:.2f} seconds")
            print(f"      Error Details   : {error_msg}")
            
            # Since context tests grow, if one fails due to resources, we skip the rest to prevent system lockups
            print(f"\n[WARN] Aborting remaining matrix tests due to context limits at {target_tokens} tokens.")
            break

    print("\n" + "="*80)
