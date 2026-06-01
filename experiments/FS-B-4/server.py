#!/usr/bin/env python3
"""
SIC-JS Web Components Dashboard Server
EXP FS-B-4: Serves dashboard + 100 task records for TTR benchmark.
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = Path(__file__).parent
PORT = 8083

# Generate 100 diverse task records
STATUSES = ["pending", "in_progress", "completed", "dismissed", "archived"]
PRIORITIES = ["P0", "P1", "P2"]
OWNERS = ["咩咩", "德德", "扣德", "無限先生", "安安"]

RECORDS = []
for i in range(1, 101):
    prefix = ["FS", "DD", "XIED", "MM"][i % 4]
    series = ["A", "B", "C", "D", "E"][i % 5]
    serial = ((i - 1) % 9) + 1
    RECORDS.append({
        "sic_version": "3.0",
        "task": {
            "id": f"{prefix}-{series}-{serial}",
            "title": f"Task #{i}: {'Validator' if i%5==0 else 'Streaming' if i%5==1 else 'Ledger' if i%5==2 else 'Dashboard' if i%5==3 else 'Security'}",
            "deliverable": f"Deliverable for task {i}",
            "status": STATUSES[i % 5],
            "created_round": max(1, i - 10),
            "owner": OWNERS[i % 5],
            "priority": PRIORITIES[i % 3]
        },
        "round": i,
        "entity": {"name": OWNERS[i % 5], "model": "Manus"},
        "state": {
            "context": f"Context for round {i}",
            "current_action": f"Action {i}"
        },
        "relation": {"user": "安安"}
    })

RECORDS_JSON = json.dumps(RECORDS, ensure_ascii=False).encode("utf-8")

# Store benchmark reports
benchmark_reports = []


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == "/":
            self._serve_file("index.html", "text/html")
        elif self.path == "/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(RECORDS_JSON)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(RECORDS_JSON)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path == "/results":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(benchmark_reports).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == "/report":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                report = json.loads(body)
                benchmark_reports.append(report)
            except json.JSONDecodeError:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_error(404)
    
    def _serve_file(self, filename, content_type):
        filepath = SCRIPT_DIR / filename
        if filepath.exists():
            data = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"[SERVER] Dashboard on port {PORT}")
    server.serve_forever()
