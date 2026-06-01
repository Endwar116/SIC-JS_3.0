#!/usr/bin/env python3
"""
SIC-JS NDJSON Streaming Server — ASYNC VERSION (uvicorn + FastAPI)
EXP FS-B-2 RIGOROUS FIX: Replace http.server with async I/O.

Problem identified: Python http.server is single-threaded.
100 concurrent connections queue up → P99 = 512ms.

Fix: uvicorn (uvloop) + FastAPI + StreamingResponse.
Expected: 100 concurrent P99 < 5ms.
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import asyncio

SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent.parent / "FS-B-2"
NDJSON_FILE = PARENT_DIR / "load_test_data.ndjson"

sys.path.insert(0, str(PARENT_DIR))
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
_PREBUILT_BODY = b"".join(
    (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    for record in _VALID_RECORDS
)
print(f"[INIT] Ready: {len(_VALID_RECORDS)} records, {len(_PREBUILT_BODY)} bytes pre-built")

app = FastAPI(title="SIC-JS NDJSON Streaming Server (Async)")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "records": len(_VALID_RECORDS)})


@app.get("/stream")
async def stream():
    """Stream pre-validated NDJSON from warm cache — async, zero-copy."""
    return StreamingResponse(
        iter([_PREBUILT_BODY]),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/")
async def index():
    index_path = PARENT_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>SIC-JS Streaming Server (Async)</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server_async:app",
        host="0.0.0.0",
        port=8082,
        log_level="warning",
        loop="asyncio"
    )
