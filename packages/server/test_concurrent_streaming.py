#!/usr/bin/env python3
"""
FS-B-2 RIGOROUS FIX: Benchmark the async server (uvicorn + FastAPI).
Measures:
- Sequential TTFB (1000 requests): P50, P95, P99
- Concurrent TTFB (100 simultaneous): P50, P95, P99
- Chaos: random disconnect mid-stream (50 times)

Gate: 100 concurrent P99 < 5ms
"""

import asyncio
import time
import json
import statistics
import sys
from pathlib import Path

try:
    import aiohttp
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "-q"])
    import aiohttp

SCRIPT_DIR = Path(__file__).parent
SERVER_URL = "http://127.0.0.1:8082"


async def measure_ttfb_single(session):
    """Measure TTFB for a single request (time to first byte of body)."""
    start = time.perf_counter_ns()
    async with session.get(f"{SERVER_URL}/stream") as resp:
        # TTFB = time from request sent to first byte of response body
        first_byte = await resp.content.readany()
        ttfb_ns = time.perf_counter_ns() - start
        # Drain the rest to free connection
        async for _ in resp.content.iter_any():
            pass
    return ttfb_ns / 1_000_000  # Convert to ms


async def sequential_benchmark(count=1000):
    """Sequential requests to measure baseline TTFB."""
    times = []
    async with aiohttp.ClientSession() as session:
        for _ in range(count):
            t = await measure_ttfb_single(session)
            times.append(t)
    times.sort()
    return {
        "count": count,
        "p50": round(times[len(times) // 2], 3),
        "p95": round(times[int(len(times) * 0.95)], 3),
        "p99": round(times[int(len(times) * 0.99)], 3),
        "mean": round(statistics.mean(times), 3),
        "stdev": round(statistics.stdev(times), 3) if len(times) > 1 else 0,
        "min": round(min(times), 3),
        "max": round(max(times), 3),
    }


async def concurrent_benchmark(concurrency=100, rounds=10):
    """Concurrent requests to measure under load."""
    all_times = []
    async with aiohttp.ClientSession() as session:
        for _ in range(rounds):
            tasks = [measure_ttfb_single(session) for _ in range(concurrency)]
            results = await asyncio.gather(*tasks)
            all_times.extend(results)
    all_times.sort()
    total = len(all_times)
    return {
        "concurrency": concurrency,
        "rounds": rounds,
        "total_requests": total,
        "p50": round(all_times[total // 2], 3),
        "p95": round(all_times[int(total * 0.95)], 3),
        "p99": round(all_times[int(total * 0.99)], 3),
        "mean": round(statistics.mean(all_times), 3),
        "stdev": round(statistics.stdev(all_times), 3) if total > 1 else 0,
        "min": round(min(all_times), 3),
        "max": round(max(all_times), 3),
    }


async def chaos_disconnect(count=50):
    """Simulate random disconnects mid-stream."""
    successes = 0
    errors = 0
    async with aiohttp.ClientSession() as session:
        for _ in range(count):
            try:
                async with session.get(f"{SERVER_URL}/stream") as resp:
                    # Read only partial data then abort
                    await resp.content.read(10)
                    # Don't read the rest — simulate disconnect
                successes += 1
            except Exception:
                errors += 1
    return {"attempts": count, "graceful": successes, "errors": errors}


async def main():
    print("=" * 70)
    print("FS-B-2 RIGOROUS FIX: Async Server Benchmark (uvicorn + FastAPI)")
    print("=" * 70)
    print()

    # Wait for server to be ready
    print("[0/3] Waiting for server...")
    async with aiohttp.ClientSession() as session:
        for attempt in range(30):
            try:
                async with session.get(f"{SERVER_URL}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"       Server ready: {data}")
                        break
            except Exception:
                await asyncio.sleep(0.5)
        else:
            print("       ERROR: Server not responding after 15s")
            sys.exit(1)

    # Phase 1: Sequential
    print()
    print("[1/3] Sequential TTFB (1000 requests)...")
    seq = await sequential_benchmark(1000)
    print(f"       P50={seq['p50']}ms  P95={seq['p95']}ms  P99={seq['p99']}ms")
    print(f"       Mean={seq['mean']}ms  StdDev={seq['stdev']}ms")

    # Phase 2: Concurrent
    print()
    print("[2/3] Concurrent TTFB (100 simultaneous × 10 rounds)...")
    conc = await concurrent_benchmark(100, 10)
    print(f"       P50={conc['p50']}ms  P95={conc['p95']}ms  P99={conc['p99']}ms")
    print(f"       Mean={conc['mean']}ms  StdDev={conc['stdev']}ms")

    # Phase 3: Chaos
    print()
    print("[3/3] Chaos: random disconnect mid-stream (50 attempts)...")
    chaos = await chaos_disconnect(50)
    print(f"       Graceful: {chaos['graceful']}/{chaos['attempts']}")

    # Summary
    print()
    print("-" * 70)
    print("RESULTS:")
    
    seq_pass = seq["p99"] < 16
    conc_pass = conc["p99"] < 5
    chaos_pass = chaos["graceful"] == chaos["attempts"]
    
    print(f"  Sequential P99:   {seq['p99']}ms {'✅ PASS' if seq_pass else '❌ FAIL'} (target: < 16ms)")
    print(f"  Concurrent P99:   {conc['p99']}ms {'✅ PASS' if conc_pass else '❌ FAIL'} (target: < 5ms)")
    print(f"  Chaos graceful:   {chaos['graceful']}/{chaos['attempts']} {'✅ PASS' if chaos_pass else '❌ FAIL'}")
    print("-" * 70)

    all_pass = seq_pass and conc_pass and chaos_pass
    if all_pass:
        print("✅ FS-B-2 ASYNC FIX: ALL GATES PASSED")
    else:
        print("⚠️  FS-B-2 ASYNC FIX: Some gates not met")

    # Save report
    report = {
        "experiment": "FS-B-2-rigorous-async-fix",
        "server": "uvicorn + FastAPI (async)",
        "sequential": seq,
        "concurrent": conc,
        "chaos": chaos,
        "gates": {
            "sequential_p99_lt_16ms": seq_pass,
            "concurrent_p99_lt_5ms": conc_pass,
            "chaos_graceful": chaos_pass
        },
        "all_pass": all_pass,
        "comparison_vs_sync": {
            "old_concurrent_p99_ms": 512,
            "new_concurrent_p99_ms": conc["p99"],
            "improvement_factor": round(512 / max(conc["p99"], 0.001), 1)
        }
    }
    with open(SCRIPT_DIR / "report_async.json", "w") as f:
        json.dump(report, f, indent=2)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
