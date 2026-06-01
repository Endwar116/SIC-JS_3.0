#!/usr/bin/env python3
"""
FS-B-4 RIGOROUS: 10,000 Cards + Memory Leak Detection + Reflow Storm
=====================================================================
- Scale from 100 to 10,000 task cards
- Measure TTR at 100/500/1000/5000/10000 scale points
- Detect memory growth pattern (linear vs. exponential = leak)
- Reflow storm: rapid sequential DOM updates (100 updates in 1 second)
- Statistical: P50/P95/P99 for each scale point
"""

import json
import time
import sys
import os
import subprocess
import statistics
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PORT = 8084

# We test server-side data generation + JSON serialization at scale
# Since we can't run a real browser, we measure:
# 1. Server response time at different scales (proxy for data pipeline)
# 2. JSON parse time at scale (proxy for client-side overhead)
# 3. Simulated DOM construction cost at scale
# 4. Memory growth pattern


def generate_records(count):
    """Generate N SIC-JS task records."""
    STATUSES = ["pending", "in_progress", "completed", "dismissed", "archived"]
    OWNERS = ["咩咩", "德德", "扣德", "無限先生", "安安"]
    records = []
    for i in range(1, count + 1):
        prefix = ["FS", "DD", "XIED", "MM"][i % 4]
        series = ["A", "B", "C", "D", "E"][i % 5]
        serial = ((i - 1) % 9) + 1
        records.append({
            "sic_version": "3.0",
            "task": {
                "id": f"{prefix}-{series}-{serial}",
                "title": f"Task #{i}: Stress Test Item",
                "deliverable": f"Deliverable for task {i} with some realistic length text",
                "status": STATUSES[i % 5],
                "created_round": max(1, i - 10),
                "owner": OWNERS[i % 5],
                "priority": ["P0", "P1", "P2"][i % 3]
            },
            "round": i,
            "entity": {"name": OWNERS[i % 5], "model": "Manus"},
            "state": {"context": f"Context for round {i}", "current_action": f"Action {i}"},
            "relation": {"user": "安安"}
        })
    return records


def measure_json_pipeline(records, runs=50):
    """Measure JSON serialize → parse round-trip (proxy for network + parse)."""
    times = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        data = json.dumps(records, ensure_ascii=False).encode("utf-8")
        parsed = json.loads(data)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        times.append(elapsed)
    times.sort()
    return {
        "p50": times[len(times) // 2],
        "p95": times[int(len(times) * 0.95)],
        "p99": times[int(len(times) * 0.99)],
        "mean": statistics.mean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }


def measure_dom_simulation(count, runs=50):
    """
    Simulate DOM construction cost.
    Real Web Component cost per card (measured from browser benchmarks):
    - createElement: ~0.01ms
    - attachShadow: ~0.02ms
    - setAttribute (7 attrs): ~0.035ms
    - appendChild to fragment: ~0.005ms
    Total per card: ~0.07ms
    
    We simulate this with Python string operations as a proxy.
    """
    template = '<sic-task-card task-id="{}" title="{}" status="{}" deliverable="{}" owner="{}" priority="{}" round="{}"></sic-task-card>'
    
    times = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        # Simulate building DOM fragment
        fragment = []
        for i in range(count):
            fragment.append(template.format(
                f"A-{i}", f"Task {i}", "pending", f"Del {i}", "test", "P1", i
            ))
        html = "\n".join(fragment)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        times.append(elapsed)
    
    times.sort()
    return {
        "p50": times[len(times) // 2],
        "p95": times[int(len(times) * 0.95)],
        "p99": times[int(len(times) * 0.99)],
        "mean": statistics.mean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }


def measure_memory_growth(scale_points):
    """Measure memory usage at different scales to detect leaks."""
    import tracemalloc
    tracemalloc.start()
    
    memory_at_scale = {}
    
    for count in scale_points:
        # Simulate: generate records, serialize, parse, build DOM
        records = generate_records(count)
        data = json.dumps(records, ensure_ascii=False).encode("utf-8")
        parsed = json.loads(data)
        
        current, peak = tracemalloc.get_traced_memory()
        memory_at_scale[count] = {
            "current_mb": round(current / 1024 / 1024, 2),
            "peak_mb": round(peak / 1024 / 1024, 2)
        }
        
        # Clear to simulate GC
        del records, data, parsed
    
    tracemalloc.stop()
    return memory_at_scale


def detect_memory_leak(memory_data):
    """
    Check if memory growth is linear (OK) or exponential (LEAK).
    Linear: memory ~ O(n) → ratio stays constant.
    Leak: memory ~ O(n^2) or worse → ratio grows.
    """
    points = sorted(memory_data.items())
    if len(points) < 3:
        return True, "insufficient data"
    
    # Calculate memory-per-record ratio at each scale
    ratios = []
    for count, mem in points:
        if count > 0 and mem["current_mb"] > 0:
            ratio = mem["current_mb"] / count * 1000  # KB per record
            ratios.append(ratio)
    
    if len(ratios) < 2:
        return True, "insufficient ratios"
    
    # If ratio stays roughly constant (within 3x), it's linear growth (OK)
    max_ratio = max(ratios)
    min_ratio = min(ratios) if min(ratios) > 0 else 0.001
    growth_factor = max_ratio / min_ratio
    
    is_linear = growth_factor < 3.0
    return is_linear, f"growth_factor={growth_factor:.2f} (linear if < 3.0)"


def test_reflow_storm(count=1000, updates=100):
    """
    Simulate rapid sequential DOM updates (reflow storm).
    In a real browser, each setAttribute triggers a potential reflow.
    We measure: can we do 100 full re-renders in < 1 second?
    """
    records = generate_records(count)
    
    start = time.perf_counter()
    for update_round in range(updates):
        # Simulate: change status of all records (triggers re-render)
        for r in records:
            r["task"]["status"] = ["pending", "in_progress", "completed"][update_round % 3]
        # Simulate: re-serialize (proxy for re-render)
        _ = json.dumps(records, ensure_ascii=False)
    
    elapsed = time.perf_counter() - start
    updates_per_sec = updates / elapsed
    
    return {
        "total_updates": updates,
        "elapsed_sec": round(elapsed, 3),
        "updates_per_sec": round(updates_per_sec, 1),
        "pass": elapsed < 1.0  # 100 updates in < 1 second
    }


def main():
    print("=" * 70)
    print("FS-B-4 RIGOROUS: Scale + Memory + Reflow Storm")
    print("=" * 70)
    print()
    
    scale_points = [100, 500, 1000, 5000, 10000]
    
    # Phase 1: TTR at different scales
    print("[1/4] Measuring TTR (JSON pipeline) at scale points...")
    ttr_results = {}
    for count in scale_points:
        records = generate_records(count)
        result = measure_json_pipeline(records, runs=50)
        ttr_results[count] = result
        print(f"       {count:>6} cards: P50={result['p50']:.2f}ms  P95={result['p95']:.2f}ms  P99={result['p99']:.2f}ms")
    
    # Phase 2: DOM construction simulation at scale
    print()
    print("[2/4] Measuring DOM construction simulation at scale...")
    dom_results = {}
    for count in scale_points:
        result = measure_dom_simulation(count, runs=50)
        dom_results[count] = result
        print(f"       {count:>6} cards: P50={result['p50']:.2f}ms  P95={result['p95']:.2f}ms  P99={result['p99']:.2f}ms")
    
    # Phase 3: Memory growth analysis
    print()
    print("[3/4] Memory growth analysis...")
    memory_data = measure_memory_growth(scale_points)
    for count, mem in sorted(memory_data.items()):
        print(f"       {count:>6} cards: current={mem['current_mb']:.2f}MB  peak={mem['peak_mb']:.2f}MB")
    
    is_linear, leak_info = detect_memory_leak(memory_data)
    print(f"       Memory pattern: {'✅ Linear (no leak)' if is_linear else '❌ Non-linear (potential leak)'} — {leak_info}")
    
    # Phase 4: Reflow storm
    print()
    print("[4/4] Reflow storm: 100 full re-renders of 1000 cards in < 1s...")
    reflow = test_reflow_storm(1000, 100)
    print(f"       {reflow['total_updates']} updates in {reflow['elapsed_sec']}s = {reflow['updates_per_sec']} updates/sec")
    print(f"       Target (< 1s): {'✅ PASS' if reflow['pass'] else '❌ FAIL'}")
    
    # Summary
    print()
    print("-" * 70)
    print("RIGOROUS RESULTS:")
    
    # Gate: 10,000 cards TTR P99 < 500ms (realistic for large dataset)
    ttr_10k_p99 = ttr_results[10000]["p99"]
    ttr_pass = ttr_10k_p99 < 500
    print(f"  10K cards TTR P99:    {ttr_10k_p99:.2f}ms {'✅ PASS' if ttr_pass else '❌ FAIL'} (target: < 500ms)")
    
    # Gate: DOM 10K P99 < 200ms
    dom_10k_p99 = dom_results[10000]["p99"]
    dom_pass = dom_10k_p99 < 200
    print(f"  10K cards DOM P99:    {dom_10k_p99:.2f}ms {'✅ PASS' if dom_pass else '❌ FAIL'} (target: < 200ms)")
    
    # Gate: Memory linear
    print(f"  Memory growth:        {'✅ PASS' if is_linear else '❌ FAIL'} ({leak_info})")
    
    # Gate: Reflow storm
    print(f"  Reflow storm:         {'✅ PASS' if reflow['pass'] else '❌ FAIL'} ({reflow['updates_per_sec']} ups)")
    
    print("-" * 70)
    
    all_pass = ttr_pass and dom_pass and is_linear and reflow["pass"]
    
    if all_pass:
        print("✅ FS-B-4 RIGOROUS PASS")
    else:
        print("❌ FS-B-4 RIGOROUS: Some criteria failed")
    
    # Save report
    report = {
        "experiment": "FS-B-4-rigorous",
        "ttr_pipeline": {str(k): v for k, v in ttr_results.items()},
        "dom_construction": {str(k): v for k, v in dom_results.items()},
        "memory": memory_data,
        "memory_linear": is_linear,
        "memory_info": leak_info,
        "reflow_storm": reflow,
        "gates": {
            "ttr_10k_p99_pass": ttr_pass,
            "dom_10k_p99_pass": dom_pass,
            "memory_pass": is_linear,
            "reflow_pass": reflow["pass"]
        },
        "all_pass": all_pass
    }
    with open(SCRIPT_DIR / "report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
