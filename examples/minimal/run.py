#!/usr/bin/env python3
"""
SIC-JS v3.0 Minimal Example
============================
Demonstrates the two valid forms of SIC-JS records:
1. v2.0 record (no task)
2. v3.0 record (with task)

Both are validated against the official schema.
"""

import json
import sys
from pathlib import Path

# Add validator to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "core" / "validator"))

from sic_validate import validate_record, load_schema

# --- v2.0 Record (no task) ---
v2_record = {
    "sic_version": "2.0",
    "round": 1,
    "entity": {"name": "Example Agent", "model": "GPT-4"},
    "state": {
        "context": "Demonstrating v2.0 format",
        "current_action": "Running minimal example",
        "pending": []
    },
    "relation": {"user": "Developer"},
    "event": {
        "timestamp": "2026-06-01T00:00:00Z",
        "description": "Minimal example execution",
        "trigger": "demo"
    },
    "intent": {
        "user_intent": "Learn SIC-JS format",
        "system_intent": "Demonstrate valid v2.0 record",
        "core_question": "Is this record valid?"
    }
}

# --- v3.0 Record (with task) ---
v3_record = {
    "sic_version": "3.0",
    "round": 1,
    "entity": {"name": "Example Agent", "model": "GPT-4"},
    "state": {
        "context": "Demonstrating v3.0 format with task primitive",
        "current_action": "Running minimal example",
        "pending": []
    },
    "relation": {"user": "Developer"},
    "event": {
        "timestamp": "2026-06-01T00:00:00Z",
        "description": "Minimal example execution",
        "trigger": "demo"
    },
    "intent": {
        "user_intent": "Learn SIC-JS v3.0 task primitive",
        "system_intent": "Demonstrate valid v3.0 record with task",
        "core_question": "Is this record valid?"
    },
    "task": {
        "id": "A-1",
        "title": "Learn SIC-JS",
        "deliverable": "Understand the six primitives",
        "status": "in_progress",
        "created_round": 1,
        "owner": "Developer",
        "priority": "P2"
    }
}


def main():
    schema = load_schema()
    
    print("=" * 50)
    print("SIC-JS v3.0 Minimal Example")
    print("=" * 50)
    print()
    
    # Validate v2.0
    result = validate_record(v2_record, schema)
    status = result["status"]
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} v2.0 no task: {status}")
    
    # Validate v3.0
    result = validate_record(v3_record, schema)
    status = result["status"]
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} v3.0 with task: {status}")
    
    print()
    print("Both records are valid SIC-JS records.")
    print("See packages/core/schema/sic-js-schema-v3.0.json for the full schema.")


if __name__ == "__main__":
    main()
