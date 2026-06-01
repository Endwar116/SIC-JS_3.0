#!/usr/bin/env python3
"""Generate 100 standard SIC-JS v3.0 records as NDJSON for load testing."""

import json
from datetime import datetime, timedelta

BASE_TIME = datetime(2026, 6, 1, 0, 0, 0)
STATUSES = ["pending", "in_progress", "in_progress", "in_progress", "completed"]

records = []
for i in range(1, 101):
    ts = BASE_TIME + timedelta(seconds=i)
    status_idx = min(i // 20, 4)
    record = {
        "sic_version": "3.0",
        "task": {
            "id": "FS-B-2",
            "title": "NDJSON Streaming Server + Client",
            "deliverable": "server.py + index.html, 100 rounds at 60 rounds/min",
            "status": STATUSES[status_idx],
            "created_round": 1,
            "owner": "咩咩",
            "priority": "P0"
        },
        "round": i,
        "entity": {"name": "咩咩", "model": "Manus"},
        "state": {
            "context": f"Round {i}: Processing streaming data",
            "current_action": f"Executing step {i} of 100",
            "pending": [f"step_{i+1}"] if i < 100 else []
        },
        "relation": {"user": "安安"},
        "event": {
            "timestamp": ts.isoformat() + "Z",
            "description": f"Round {i} event: data processed",
            "trigger": "round_tick"
        },
        "intent": {
            "user_intent": "Stream 100 rounds for benchmark",
            "system_intent": f"Processing round {i}"
        }
    }
    records.append(record)

with open("load_test_data.ndjson", "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Generated {len(records)} records → load_test_data.ndjson")
