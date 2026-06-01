#!/usr/bin/env python3
"""
SIC-JS NDJSON Streaming Server (Warm Cache)
EXP FS-B-2: HTTP server that streams SIC-JS rounds via NDJSON.

Key optimization: Schema + data pre-loaded at startup (warm cache).
TTFB target: < 16ms on localhost.
"""

import json
import time
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse

SCRIPT_DIR = Path(__file__).parent
NDJSON_FILE = SCRIPT_DIR / "load_test_data.ndjson"

sys.path.insert(0, str(SCRIPT_DIR))
from sic_validate import load_schema, validate_record

# === PRE-LOAD AT STARTUP (warm cache) ===
print("[INIT] Pre-loading schema and data...")
_SCHEMA = load_schema()

_VALID_RECORDS = []
with open(NDJSON_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                record = json.loads(line)
                validation = validate_record(record, _SCHEMA)
                if validation["status"] != "FAIL":
                    _VALID_RECORDS.append(record)
            except json.JSONDecodeError:
                continue

# Pre-serialize to bytes for zero-copy streaming
_PREBUILT_LINES = []
for record in _VALID_RECORDS:
    _PREBUILT_LINES.append((json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))

_PREBUILT_BODY = b"".join(_PREBUILT_LINES)
print(f"[INIT] Ready: {len(_VALID_RECORDS)} records, {len(_PREBUILT_BODY)} bytes pre-built")


class StreamingHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == "/stream":
            self.handle_stream()
        elif self.path == "/":
            self.handle_index()
        elif self.path == "/health":
            self.handle_health()
        else:
            self.send_error(404)
    
    def handle_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def handle_index(self):
        index_path = SCRIPT_DIR / "index.html"
        if index_path.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(index_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def handle_stream(self):
        """Stream pre-validated NDJSON from warm cache."""
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(_PREBUILT_BODY)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        # Write pre-built body in one shot (minimum TTFB)
        try:
            self.wfile.write(_PREBUILT_BODY)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def run_server(port=8082, rate=60):
    server = HTTPServer(("0.0.0.0", port), StreamingHandler)
    server.stream_rate = rate
    print(f"[SERVER] Listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--rate", type=int, default=0)
    args = parser.parse_args()
    run_server(port=args.port, rate=args.rate)
