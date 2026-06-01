#!/usr/bin/env python3
"""Run server + benchmark for FS-B-4."""
import subprocess, time, sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8083

os.system(f"fuser -k {PORT}/tcp 2>/dev/null")
time.sleep(0.5)

server = subprocess.Popen(
    [sys.executable, os.path.join(SCRIPT_DIR, "server.py")],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=SCRIPT_DIR
)
time.sleep(1)

if server.poll() is not None:
    print("ERROR: Server failed to start")
    sys.exit(1)

result = subprocess.run(
    [sys.executable, os.path.join(SCRIPT_DIR, "benchmark.py")],
    capture_output=True, text=True, cwd=SCRIPT_DIR
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:300])

server.terminate()
server.wait(timeout=5)
sys.exit(result.returncode)
