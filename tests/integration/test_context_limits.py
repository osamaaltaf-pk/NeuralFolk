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
import asyncio
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

def calculate_percentile(values: list, p: float) -> float:
    """Calculates the p-th percentile of a list of values using linear interpolation."""
    if not values:
        return 0.0
    sorted_val = sorted(values)
    k = (len(sorted_val) - 1) * (p / 100.0)
    idx = int(k)
    rem = k - idx
    if idx + 1 < len(sorted_val):
        return sorted_val[idx] * (1.0 - rem) + sorted_val[idx + 1] * rem
    return sorted_val[idx]


@pytest.mark.integration
def test_context_limits_matrix() -> None:
    """
    Tests local GPU/CPU hardware boundaries by sending prompts scaled to:
    - 1,000 tokens (Standard)
    - 4,000 tokens (Base context)
    - 8,000 tokens (Medium context)
    - 16,000 tokens (High context)
    - 32,000 tokens (Max engine context)
    - 64,000 tokens (Super-extended context)
    - 100,000 tokens (Ultra-long context)
    
    Runs 3 trials per context level to capture latency percentiles (p50, p90, p95, p99)
    for both input (prefill) and output (generation) phases.
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
        (32000, 3200),
        (64000, 6400),
        (100000, 10000)
    ]

    num_trials = 3  # Stable and fast default count of trials per matrix level

    print("\n" + "="*80)
    print("      NEURALFOLK CONTEXT RANGE & VRAM DIAGNOSTIC MATRIX (MULTI-TRIAL)")
    print("="*80)
    print(f"Model under test: {MODEL}")
    print(f"Trials per level: {num_trials}")
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
        
        prefill_latencies = []
        gen_latencies = []
        total_latencies = []
        prefill_throughputs = []
        gen_throughputs = []
        vram_allocations = []
        
        success_count = 0
        error_msg = ""
        response_text = ""
        prompt_eval_count = 0
        eval_count = 0
        
        for trial in range(1, num_trials + 1):
            trial_start = time.perf_counter()
            trial_success = False
            trial_error = ""
            prefill_dur = 0.0
            gen_dur = 0.0
            
            try:
                with httpx.Client(timeout=TIMEOUT) as client:
                    res = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
                
                trial_duration = time.perf_counter() - trial_start
                
                if res.status_code == 200:
                    trial_success = True
                    data = res.json()
                    response_text = data.get("message", {}).get("content", "").strip()
                    
                    # Ollama timings are in nanoseconds
                    prompt_eval_dur_ns = data.get("prompt_eval_duration", 0)
                    eval_dur_ns = data.get("eval_duration", 0)
                    
                    if prompt_eval_dur_ns > 0:
                        prefill_dur = prompt_eval_dur_ns / 1e9
                    else:
                        prefill_dur = trial_duration * 0.8  # fallback approximation
                        
                    if eval_dur_ns > 0:
                        gen_dur = eval_dur_ns / 1e9
                    else:
                        gen_dur = trial_duration * 0.2  # fallback approximation
                    
                    p_eval_count = data.get("prompt_eval_count", 0)
                    g_eval_count = data.get("eval_count", 0)
                    
                    if p_eval_count > 0:
                        prompt_eval_count = p_eval_count
                    if g_eval_count > 0:
                        eval_count = g_eval_count
                        
                    prefill_latencies.append(prefill_dur)
                    gen_latencies.append(gen_dur)
                    total_latencies.append(trial_duration)
                    
                    if prefill_dur > 0 and prompt_eval_count > 0:
                        prefill_throughputs.append(prompt_eval_count / prefill_dur)
                    if gen_dur > 0 and eval_count > 0:
                        gen_throughputs.append(eval_count / gen_dur)
                        
                    success_count += 1
                else:
                    trial_error = f"HTTP Error {res.status_code}: {res.text[:150]}"
            except Exception as e:
                trial_duration = time.perf_counter() - trial_start
                trial_error = str(e)
                
            # Query live memory statistics per trial
            mem = get_live_memory_usage()
            vram_mb = mem["size_vram"] / 1024 / 1024
            if vram_mb > 0:
                vram_allocations.append(vram_mb)
                
            if trial_success:
                print(f"   Trial {trial}/{num_trials}: OK in {trial_duration:.2f}s | Prefill: {prefill_dur:.2f}s | Gen: {gen_dur:.2f}s | VRAM: {vram_mb:.1f} MB")
            else:
                print(f"   Trial {trial}/{num_trials}: FAIL | Error: {trial_error}")
                error_msg = trial_error
                break
        
        # Output diagnostics
        if success_count == num_trials:
            avg_vram = sum(vram_allocations) / len(vram_allocations) if vram_allocations else 0.0
            vram_status = f"{avg_vram:.1f} MB" if avg_vram > 0 else "0 MB (CPU fallback)"
            
            p50_prefill = calculate_percentile(prefill_latencies, 50)
            p90_prefill = calculate_percentile(prefill_latencies, 90)
            p95_prefill = calculate_percentile(prefill_latencies, 95)
            p99_prefill = calculate_percentile(prefill_latencies, 99)
            
            p50_gen = calculate_percentile(gen_latencies, 50)
            p90_gen = calculate_percentile(gen_latencies, 90)
            p95_gen = calculate_percentile(gen_latencies, 95)
            p99_gen = calculate_percentile(gen_latencies, 99)
            
            p50_total = calculate_percentile(total_latencies, 50)
            p90_total = calculate_percentile(total_latencies, 90)
            p95_total = calculate_percentile(total_latencies, 95)
            p99_total = calculate_percentile(total_latencies, 99)
            
            avg_prefill_throughput = sum(prefill_throughputs) / len(prefill_throughputs) if prefill_throughputs else 0.0
            avg_gen_throughput = sum(gen_throughputs) / len(gen_throughputs) if gen_throughputs else 0.0
            
            print(f"  --> [OK] All {num_trials} trials completed successfully!")
            print(f"      Tokens Processed: Prefill={prompt_eval_count}, Generation={eval_count}")
            print(f"      GPU Allocations : Average VRAM = {vram_status}")
            print(f"      --------------------------------------------------")
            print(f"      Latency Percentiles (Seconds):")
            print(f"        Phase     |   p50   |   p90   |   p95   |   p99   |")
            print(f"        ----------+---------+---------+---------+---------+")
            print(f"        Prefill   |  {p50_prefill:6.2f}s |  {p90_prefill:6.2f}s |  {p95_prefill:6.2f}s |  {p99_prefill:6.2f}s |")
            print(f"        Generation|  {p50_gen:6.2f}s |  {p90_gen:6.2f}s |  {p95_gen:6.2f}s |  {p99_gen:6.2f}s |")
            print(f"        Total     |  {p50_total:6.2f}s |  {p90_total:6.2f}s |  {p95_total:6.2f}s |  {p99_total:6.2f}s |")
            print(f"      --------------------------------------------------")
            print(f"      Throughput Speed:")
            print(f"        Prefill Speed    = {avg_prefill_throughput:8.2f} tokens/sec")
            print(f"        Generation Speed = {avg_gen_throughput:8.2f} tokens/sec")
            print(f"      Response Snippet: '{response_text}'")
        else:
            print(f"  --> [FAIL] Context limit reached or failed at {target_tokens} tokens!")
            print(f"      Error Details   : {error_msg}")
            
            # Since context tests grow, if one fails due to resources, we skip the rest to prevent system lockups
            print(f"\n[WARN] Aborting remaining matrix tests due to context limits at {target_tokens} tokens.")
            break

    print("\n" + "="*80)


async def send_single_concurrent_request(client: httpx.AsyncClient, prompt: str, target_tokens: int) -> Dict[str, Any]:
    """Helper function to fire a single concurrent request and return its metrics."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 10,
            "num_ctx": target_tokens + 500
        }
    }
    
    start_time = time.perf_counter()
    try:
        res = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=TIMEOUT)
        duration = time.perf_counter() - start_time
        if res.status_code == 200:
            data = res.json()
            # extract durations
            p_dur_ns = data.get("prompt_eval_duration", 0)
            e_dur_ns = data.get("eval_duration", 0)
            
            prefill_dur = p_dur_ns / 1e9 if p_dur_ns > 0 else duration * 0.8
            gen_dur = e_dur_ns / 1e9 if e_dur_ns > 0 else duration * 0.2
            
            return {
                "success": True,
                "duration": duration,
                "prefill_dur": prefill_dur,
                "gen_dur": gen_dur,
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0)
            }
        else:
            return {"success": False, "error": f"HTTP {res.status_code}: {res.text[:150]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@pytest.mark.asyncio
async def test_concurrent_batches_matrix() -> None:
    """
    Tests local hardware capabilities for multi-agent workloads by running
    concurrent batch sizes of [1, 2, 4, 8] agents.
    Each agent prompt utilizes a standard ~4,000 token context window.
    """
    # Probing Ollama reachability
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
        if r.status_code != 200:
            pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")
    except Exception:
        pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")

    batch_sizes = [1, 2, 4, 8]
    target_tokens = 4000
    multiplier = 400
    padding_text = BASE_PADDED_SENTENCE * multiplier
    prompt = f"{padding_text}\n\n[TASK] Read all the text above. Reply with exactly the single word: 'DONE'."

    print("\n" + "="*80)
    print("      NEURALFOLK CONCURRENT BATCH / AGENT WORKFORCE DIAGNOSTIC MATRIX")
    print("="*80)
    print(f"Model under test: {MODEL}")
    print(f"Base context size per agent request: {target_tokens} tokens")
    print("-"*80)

    for size in batch_sizes:
        print(f"\n[DIAGNOSTIC] Testing Concurrent Agent Batch Size: {size} agents...")
        
        start_batch = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            tasks = [send_single_concurrent_request(client, prompt, target_tokens) for _ in range(size)]
            results = await asyncio.gather(*tasks)
            
        batch_duration = time.perf_counter() - start_batch
        
        # Query live memory statistics at peak/end of run
        mem = get_live_memory_usage()
        vram_mb = mem["size_vram"] / 1024 / 1024
        vram_status = f"{vram_mb:.1f} MB" if vram_mb > 0 else "0 MB (CPU fallback)"
        
        successes = [r for r in results if r.get("success")]
        failures = [r for r in results if not r.get("success")]
        
        print(f"   Batch {size}: Completed in {batch_duration:.2f}s | Successes: {len(successes)}/{size} | VRAM: {vram_status}")
        
        if failures:
            print(f"   --> [WARNING] Batch size {size} experienced {len(failures)} failures!")
            for idx, fail in enumerate(failures):
                print(f"       Fail {idx+1}: {fail.get('error')}")
        
        if successes:
            prefill_lats = [r["prefill_dur"] for r in successes]
            gen_lats = [r["gen_dur"] for r in successes]
            total_lats = [r["duration"] for r in successes]
            
            p50_pref = calculate_percentile(prefill_lats, 50)
            p90_pref = calculate_percentile(prefill_lats, 90)
            p95_pref = calculate_percentile(prefill_lats, 95)
            p99_pref = calculate_percentile(prefill_lats, 99)
            
            p50_gen = calculate_percentile(gen_lats, 50)
            p90_gen = calculate_percentile(gen_lats, 90)
            p95_gen = calculate_percentile(gen_lats, 95)
            p99_gen = calculate_percentile(gen_lats, 99)
            
            p50_tot = calculate_percentile(total_lats, 50)
            p90_tot = calculate_percentile(total_lats, 90)
            p95_tot = calculate_percentile(total_lats, 95)
            p99_tot = calculate_percentile(total_lats, 99)
            
            # Throughput
            total_input_tokens = sum(r["prompt_eval_count"] for r in successes)
            total_output_tokens = sum(r["eval_count"] for r in successes)
            total_tokens = total_input_tokens + total_output_tokens
            
            throughput = total_tokens / batch_duration
            
            print(f"      --------------------------------------------------")
            print(f"      Latency Percentiles (Seconds) for {len(successes)} Successful Agents:")
            print(f"        Phase     |   p50   |   p90   |   p95   |   p99   |")
            print(f"        ----------+---------+---------+---------+---------+")
            print(f"        Prefill   |  {p50_pref:6.2f}s |  {p90_pref:6.2f}s |  {p95_pref:6.2f}s |  {p99_pref:6.2f}s |")
            print(f"        Generation|  {p50_gen:6.2f}s |  {p90_gen:6.2f}s |  {p95_gen:6.2f}s |  {p99_gen:6.2f}s |")
            print(f"        Total     |  {p50_tot:6.2f}s |  {p90_tot:6.2f}s |  {p95_tot:6.2f}s |  {p99_tot:6.2f}s |")
            print(f"      --------------------------------------------------")
            print(f"      Total Batch Statistics:")
            print(f"        Makespan (Total Wall Time) = {batch_duration:.2f} seconds")
            print(f"        Total Processed Tokens    = {total_tokens} (Input={total_input_tokens}, Gen={total_output_tokens})")
            print(f"        System Batch Throughput    = {throughput:.2f} tokens/sec")
        else:
            print(f"  --> [FAIL] Entire batch of size {size} failed to complete.")
            print(f"\n[WARN] Aborting remaining concurrent agent tests due to system limits at batch size {size}.")
            break

    print("\n" + "="*80)


@pytest.mark.integration
def test_generation_length_matrix() -> None:
    """
    Tests sustained 100% hardware utilization by scaling output (generation/decode)
    lengths progressively from 100 to 32,000 tokens.
    """
    # Probing Ollama reachability
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{OLLAMA_HOST}/api/tags")
        if r.status_code != 200:
            pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")
    except Exception:
        pytest.skip("Ollama is not reachable. Ensure inference service is healthy.")

    # Matrix: Output length targets
    output_matrix = [100, 500, 1000, 2000, 4000, 16000, 32000]
    
    print("\n" + "="*80)
    print("      NEURALFOLK SUSTAINED DECODE & GENERATION DIAGNOSTIC MATRIX (EXTREME)")
    print("="*80)
    print(f"Model under test: {MODEL}")
    print("System Prompt: Simple prompt requesting continuous counting to sustain decode phase.")
    print("-"*80)

    prompt = "Generate a massive, endless, detailed list of integers from 1 to 35,000. For each integer, write a dedicated paragraph describing its mathematical properties. For example, write: 'Number 1 is the first positive integer...'. Do not skip any numbers and keep writing without stopping."

    for target_output in output_matrix:
        print(f"\n[DIAGNOSTIC] Testing Output (Decode) Limit: {target_output} tokens...")
        
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": target_output,
                "num_ctx": target_output + 2000  # Expand context window dynamically to avoid ceiling cutoff
            }
        }
        
        start_time = time.perf_counter()
        success = False
        error_msg = ""
        response_text = ""
        eval_count = 0
        prompt_eval_count = 0
        prefill_dur = 0.0
        gen_dur = 0.0
        
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
                
            duration = time.perf_counter() - start_time
            
            if res.status_code == 200:
                success = True
                data = res.json()
                response_text = data.get("message", {}).get("content", "").strip()
                
                # Ollama timings are in nanoseconds
                p_dur_ns = data.get("prompt_eval_duration", 0)
                e_dur_ns = data.get("eval_duration", 0)
                
                prefill_dur = p_dur_ns / 1e9 if p_dur_ns > 0 else duration * 0.05
                gen_dur = e_dur_ns / 1e9 if e_dur_ns > 0 else duration * 0.95
                
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)
            else:
                error_msg = f"HTTP Error {res.status_code}: {res.text[:150]}"
        except Exception as e:
            duration = time.perf_counter() - start_time
            error_msg = str(e)
            
        # Query live memory statistics at peak/end of run
        mem = get_live_memory_usage()
        vram_mb = mem["size_vram"] / 1024 / 1024
        vram_status = f"{vram_mb:.1f} MB" if vram_mb > 0 else "0 MB (CPU fallback)"
        
        if success:
            prefill_speed = prompt_eval_count / prefill_dur if prefill_dur > 0 else 0.0
            gen_speed = eval_count / gen_dur if gen_dur > 0 else 0.0
            
            print(f"  --> [OK] Successfully completed generation!")
            print(f"      Tokens Processed: Input={prompt_eval_count}, Generated={eval_count} (Target={target_output})")
            print(f"      Execution Times : Prefill Time = {prefill_dur:.2f}s | Generation Time = {gen_dur:.2f}s (Total={duration:.2f}s)")
            print(f"      Throughput Speed:")
            print(f"        Prefill Speed    = {prefill_speed:8.2f} tokens/sec")
            print(f"        Generation Speed = {gen_speed:8.2f} tokens/sec (~{1000 * gen_dur / (eval_count or 1):.2f} ms/token)")
            print(f"      GPU Allocations : VRAM = {vram_status}")
            print(f"      Response Length : {len(response_text)} characters")
        else:
            print(f"  --> [FAIL] Sustained generation failed at output limit {target_output}!")
            print(f"      Duration Elapsed: {duration:.2f} seconds")
            print(f"      Error Details   : {error_msg}")
            
            # If a long generation fails due to timeouts/resources, skip the rest
            print(f"\n[WARN] Aborting remaining generation tests due to limits at output size {target_output}.")
            break

    print("\n" + "="*80)
