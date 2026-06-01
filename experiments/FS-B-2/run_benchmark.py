#!/usr/bin/env python3
"""Run server + benchmark together for FS-B-2."""
import subprocess
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8082

# Kill any existing process on port
os.system(f"fuser -k {PORT}/tcp 2>/dev/null")
time.sleep(0.5)

# Start server
print(f"Starting server on port {PORT}...")
server = subprocess.Popen(
    [sys.executable, os.path.join(SCRIPT_DIR, "server.py"), "--port", str(PORT), "--rate", "0"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=SCRIPT_DIR
)
time.sleep(2)

# Check server is alive
if server.poll() is not None:
    print("ERROR: Server failed to start")
    stdout, stderr = server.communicate()
    print(f"STDOUT: {stdout.decode()[:500]}")
    print(f"STDERR: {stderr.decode()[:500]}")
    sys.exit(1)

# Run benchmark
print("Running benchmark...")
env = os.environ.copy()
env["SERVER_URL"] = f"http://localhost:{PORT}"
result = subprocess.run(
    [sys.executable, os.path.join(SCRIPT_DIR, "benchmark.py")],
    capture_output=True, text=True, env=env, cwd=SCRIPT_DIR
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])

# Cleanup
server.terminate()
server.wait(timeout=5)
sys.exit(result.returncode)
