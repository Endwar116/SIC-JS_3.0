#!/usr/bin/env python3
"""
FS-B-2 RIGOROUS: Concurrent Load + Latency Percentiles + Chaos Engineering
===========================================================================
- 100 concurrent connections hitting /stream simultaneously
- Measure P50, P95, P99 TTFB
- Chaos: randomly close connections mid-stream, verify server doesn't crash
- Statistical: 1000 individual TTFB measurements for distribution analysis
"""

import time
import json
import socket
import sys
import os
import statistics
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = Path(__file__).parent
SERVER_DIR = Path(__file__).parent.parent.parent / "FS-B-2"
PORT = 8090
HOST = "localhost"


def start_server():
    """Start the streaming server."""
    os.system(f"fuser -k {PORT}/tcp 2>/dev/null")
    time.sleep(0.3)
    server = subprocess.Popen(
        [sys.executable, str(SERVER_DIR / "server.py"), "--port", str(PORT), "--rate", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(SERVER_DIR)
    )
    time.sleep(2)
    if server.poll() is not None:
        raise RuntimeError("Server failed to start")
    return server


def measure_single_ttfb():
    """Measure TTFB for a single request using raw socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((HOST, PORT))
        request = f"GET /stream HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
        start = time.perf_counter_ns()
        sock.sendall(request.encode())
        
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            buf += chunk
        
        ttfb_ns = time.perf_counter_ns() - start
        ttfb_ms = ttfb_ns / 1_000_000
        
        # Read remaining body
        while True:
            data = sock.recv(65536)
            if not data:
                break
        
        return ttfb_ms
    except Exception:
        return None
    finally:
        sock.close()


def chaos_disconnect():
    """Connect, send request, then abruptly close mid-stream."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((HOST, PORT))
        request = f"GET /stream HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        # Read just a tiny bit then slam the connection
        sock.recv(100)
        time.sleep(0.001)
        sock.close()
        return "disconnected"
    except Exception as e:
        return f"error: {e}"
    finally:
        try:
            sock.close()
        except:
            pass


def run_benchmark():
    print("=" * 70)
    print("FS-B-2 RIGOROUS: Concurrent Load + Percentiles + Chaos")
    print("=" * 70)
    print()
    
    # Start server
    print("[INIT] Starting server...")
    server = start_server()
    
    try:
        # Phase 1: 1000 sequential TTFB measurements for statistical distribution
        print("[1/3] Measuring 1000 sequential TTFB values...")
        ttfb_values = []
        for i in range(1000):
            ttfb = measure_single_ttfb()
            if ttfb is not None:
                ttfb_values.append(ttfb)
        
        if len(ttfb_values) < 900:
            print(f"  ERROR: Only {len(ttfb_values)}/1000 successful")
            sys.exit(1)
        
        ttfb_values.sort()
        p50 = ttfb_values[len(ttfb_values) // 2]
        p95 = ttfb_values[int(len(ttfb_values) * 0.95)]
        p99 = ttfb_values[int(len(ttfb_values) * 0.99)]
        mean = statistics.mean(ttfb_values)
        stdev = statistics.stdev(ttfb_values)
        cv = stdev / mean if mean > 0 else 0  # Coefficient of variation
        
        print(f"       Successful: {len(ttfb_values)}/1000")
        print(f"       P50:  {p50:.3f} ms")
        print(f"       P95:  {p95:.3f} ms")
        print(f"       P99:  {p99:.3f} ms")
        print(f"       Mean: {mean:.3f} ms | StdDev: {stdev:.3f} ms | CV: {cv:.3f}")
        
        # Phase 2: 100 concurrent connections
        print("[2/3] Launching 100 concurrent connections...")
        concurrent_ttfbs = []
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(measure_single_ttfb) for _ in range(100)]
            for f in as_completed(futures):
                result = f.result()
                if result is not None:
                    concurrent_ttfbs.append(result)
        
        concurrent_ttfbs.sort()
        if concurrent_ttfbs:
            c_p50 = concurrent_ttfbs[len(concurrent_ttfbs) // 2]
            c_p95 = concurrent_ttfbs[int(len(concurrent_ttfbs) * 0.95)]
            c_p99 = concurrent_ttfbs[int(len(concurrent_ttfbs) * 0.99)]
        else:
            c_p50 = c_p95 = c_p99 = float('inf')
        
        print(f"       Successful: {len(concurrent_ttfbs)}/100")
        print(f"       Concurrent P50: {c_p50:.3f} ms")
        print(f"       Concurrent P95: {c_p95:.3f} ms")
        print(f"       Concurrent P99: {c_p99:.3f} ms")
        
        # Phase 3: Chaos engineering - 50 abrupt disconnections
        print("[3/3] Chaos: 50 abrupt mid-stream disconnections...")
        chaos_results = []
        for _ in range(50):
            r = chaos_disconnect()
            chaos_results.append(r)
        
        disconnected = sum(1 for r in chaos_results if r == "disconnected")
        errors = sum(1 for r in chaos_results if r.startswith("error"))
        
        # Verify server still alive after chaos
        time.sleep(0.5)
        post_chaos_ttfb = measure_single_ttfb()
        server_survived = post_chaos_ttfb is not None
        
        print(f"       Disconnected: {disconnected}/50")
        print(f"       Errors: {errors}/50")
        print(f"       Server survived chaos: {'✅' if server_survived else '❌'}")
        if server_survived:
            print(f"       Post-chaos TTFB: {post_chaos_ttfb:.3f} ms")
        
        # Summary
        print()
        print("-" * 70)
        print("RIGOROUS RESULTS:")
        print(f"  Sequential (1000 runs):")
        print(f"    P50={p50:.3f}ms  P95={p95:.3f}ms  P99={p99:.3f}ms")
        print(f"    Mean={mean:.3f}ms  StdDev={stdev:.3f}ms  CV={cv:.3f}")
        p99_pass = p99 < 16
        print(f"    P99 < 16ms: {'✅ PASS' if p99_pass else '❌ FAIL'}")
        print(f"  Concurrent (100 connections):")
        print(f"    P50={c_p50:.3f}ms  P95={c_p95:.3f}ms  P99={c_p99:.3f}ms")
        c_p99_pass = c_p99 < 50  # More lenient for concurrent
        print(f"    Concurrent P99 < 50ms: {'✅ PASS' if c_p99_pass else '❌ FAIL'}")
        print(f"  Chaos Engineering:")
        print(f"    Server survived: {'✅ PASS' if server_survived else '❌ FAIL'}")
        print("-" * 70)
        
        all_pass = p99_pass and c_p99_pass and server_survived
        
        if all_pass:
            print("✅ FS-B-2 RIGOROUS PASS")
        else:
            print("❌ FS-B-2 RIGOROUS: Some criteria failed")
        
        # Save report
        report = {
            "experiment": "FS-B-2-rigorous",
            "sequential": {
                "count": len(ttfb_values),
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "p99_ms": round(p99, 3),
                "mean_ms": round(mean, 3),
                "stdev_ms": round(stdev, 3),
                "cv": round(cv, 3),
                "p99_pass": p99_pass
            },
            "concurrent": {
                "count": len(concurrent_ttfbs),
                "p50_ms": round(c_p50, 3),
                "p95_ms": round(c_p95, 3),
                "p99_ms": round(c_p99, 3),
                "p99_pass": c_p99_pass
            },
            "chaos": {
                "disconnections": disconnected,
                "server_survived": server_survived,
                "post_chaos_ttfb_ms": round(post_chaos_ttfb, 3) if post_chaos_ttfb else None
            },
            "all_pass": all_pass
        }
        with open(SCRIPT_DIR / "report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        sys.exit(0 if all_pass else 1)
    
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    run_benchmark()
