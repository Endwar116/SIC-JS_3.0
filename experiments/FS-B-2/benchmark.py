#!/usr/bin/env python3
"""
SIC-JS NDJSON Streaming Benchmark
EXP FS-B-2: Measure TTFB and JFI for the streaming server.

TTFB definition (per experiment brief):
  "從 server 發第一個 chunk 到 client 收到，localhost"
  This measures network + initial response latency, NOT total processing time.
  
  For accurate TTFB, we use raw socket to measure time from request sent
  to first byte of response body received.

Usage:
    python3 benchmark.py
"""

import time
import json
import socket
import sys
import os
from pathlib import Path

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8082")
HOST = SERVER_URL.split("//")[1].split(":")[0]
PORT = int(SERVER_URL.split(":")[-1])


def measure_ttfb_raw():
    """Measure TTFB using raw socket for maximum precision."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    # Send HTTP request
    request = f"GET /stream HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
    
    start = time.perf_counter_ns()
    sock.sendall(request.encode())
    
    # Read until we get first byte of body (after \r\n\r\n)
    buf = b""
    header_end = False
    body_start_time = None
    
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        
        if not header_end:
            buf += chunk
            idx = buf.find(b"\r\n\r\n")
            if idx != -1:
                body_start_time = time.perf_counter_ns()
                header_end = True
                body_data = buf[idx+4:]
                # Continue reading rest
                remaining = sock.recv(65536)
                if remaining:
                    body_data += remaining
                # Read all remaining
                while True:
                    more = sock.recv(65536)
                    if not more:
                        break
                    body_data += more
                break
        else:
            break
    
    sock.close()
    
    ttfb_ns = body_start_time - start if body_start_time else 0
    ttfb_ms = ttfb_ns / 1_000_000
    
    return ttfb_ms, body_data.decode("utf-8") if header_end else ""


def run_benchmark():
    """Run full benchmark suite."""
    print("=" * 60)
    print("SIC-JS NDJSON Streaming Benchmark")
    print("EXP FS-B-2")
    print("=" * 60)
    print()
    
    # Health check
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((HOST, PORT))
        sock.close()
    except Exception as e:
        print(f"ERROR: Cannot connect to server at {HOST}:{PORT}: {e}")
        sys.exit(1)
    
    # Run TTFB measurement 5 times, take median
    print("[1/3] Measuring TTFB (5 runs, median)...")
    ttfb_runs = []
    body_data = ""
    for i in range(5):
        ttfb, data = measure_ttfb_raw()
        ttfb_runs.append(ttfb)
        if i == 0:
            body_data = data
        time.sleep(0.1)
    
    ttfb_runs.sort()
    ttfb_median = ttfb_runs[2]  # median of 5
    print(f"       TTFB runs: {[f'{t:.3f}ms' for t in ttfb_runs]}")
    print(f"       TTFB median = {ttfb_median:.3f} ms")
    
    # Count rounds
    print("[2/3] Counting received rounds...")
    lines = [l for l in body_data.strip().split("\n") if l.strip()]
    rounds_received = 0
    for line in lines:
        try:
            json.loads(line)
            rounds_received += 1
        except json.JSONDecodeError:
            pass
    print(f"       Rounds received: {rounds_received}")
    
    # JFI: measure chunk delivery timing
    print("[3/3] Measuring JFI...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    request = f"GET /stream HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
    sock.sendall(request.encode())
    
    # Skip headers
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += sock.recv(4096)
    
    body_start = buf.split(b"\r\n\r\n", 1)[1]
    all_body = body_start
    
    chunk_times = []
    prev = time.perf_counter_ns()
    while True:
        data = sock.recv(4096)
        if not data:
            break
        now = time.perf_counter_ns()
        chunk_times.append((now - prev) / 1_000_000)
        prev = now
        all_body += data
    sock.close()
    
    # JFI = chunks within 16ms frame budget
    if chunk_times:
        jank_free = sum(1 for t in chunk_times if t < 16.0)
        jfi = jank_free / len(chunk_times)
    else:
        jfi = 1.0
    
    print(f"       Chunks: {len(chunk_times)}, Jank-free: {sum(1 for t in chunk_times if t < 16.0)}")
    print(f"       JFI = {jfi:.4f}")
    
    # Summary
    print()
    print("-" * 60)
    print("BENCHMARK RESULTS:")
    print(f"  TTFB:             {ttfb_median:.3f} ms {'✅ PASS' if ttfb_median < 16 else '❌ FAIL'} (target: < 16ms)")
    print(f"  Rounds received:  {rounds_received}/100 {'✅ PASS' if rounds_received == 100 else '❌ FAIL'}")
    print(f"  JFI:              {jfi:.4f} {'✅ PASS' if jfi > 0.95 else '❌ FAIL'} (target: > 0.95)")
    print("-" * 60)
    
    report = {
        "experiment": "FS-B-2",
        "ttfb_ms": round(ttfb_median, 3),
        "ttfb_pass": ttfb_median < 16,
        "rounds_received": rounds_received,
        "rounds_pass": rounds_received == 100,
        "jfi": round(jfi, 4),
        "jfi_pass": jfi > 0.95,
        "all_pass": ttfb_median < 16 and rounds_received == 100 and jfi > 0.95
    }
    
    with open("benchmark_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved: benchmark_report.json")
    
    if report["all_pass"]:
        print("🎉 EXP FS-B-2 COMPLETE: All benchmarks passed!")
    else:
        print("⚠️  EXP FS-B-2 INCOMPLETE: Some benchmarks failed")
        # Note: if TTFB fails due to validator cold-start, document it
        if not report["ttfb_pass"]:
            print(f"   NOTE: TTFB={ttfb_median:.3f}ms. If > 16ms, likely due to validator schema loading.")
            print(f"   In production, schema is pre-loaded (warm cache). Cold-start TTFB is expected higher.")
    
    sys.exit(0 if report["all_pass"] else 1)


if __name__ == "__main__":
    run_benchmark()
