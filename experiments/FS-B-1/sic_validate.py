#!/usr/bin/env python3
"""
SIC-JS v3.0 Validator CLI
==========================
EXP FS-B-1: 把 sic-js-schema-v3.0.json 包成可以在 terminal 用的驗證工具。

Usage:
    python3 sic_validate.py <json_file_path>
    python3 sic_validate.py --batch <dir_path>

Output:
    PASS / FAIL / WARN + 錯誤訊息（JSON 格式）

Alignment:
    - Schema: sic-js-schema-v3.0.json (SHA256: d9835f7f...)
    - Spec: SICJS_30_技術原始記載檔_完整自足_File_2026_5_31.md
"""

import json
import sys
import os
from pathlib import Path

# --- Schema Loading ---
SCRIPT_DIR = Path(__file__).parent
SCHEMA_PATH = SCRIPT_DIR / "sic-js-schema-v3.0.json"

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip3 install jsonschema")
    sys.exit(1)


def load_schema():
    """Load the official SIC-JS v3.0 JSON Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_record(record: dict, schema: dict) -> dict:
    """
    Validate a single SIC-JS record against the schema.
    
    Returns:
        {
            "status": "PASS" | "FAIL" | "WARN",
            "errors": [...],
            "warnings": [...]
        }
    """
    result = {
        "status": "PASS",
        "errors": [],
        "warnings": []
    }
    
    # --- Layer 1: JSON Schema Validation ---
    try:
        validate(instance=record, schema=schema)
    except ValidationError as e:
        result["status"] = "FAIL"
        result["errors"].append({
            "type": "schema_validation",
            "path": list(e.absolute_path),
            "message": e.message
        })
        return result  # Early return on schema failure
    
    # --- Layer 2: Cross-field Constraints (x-validator-notes) ---
    
    # Constraint 1: task.created_round MUST be <= round
    if "task" in record and record["task"] is not None:
        task = record["task"]
        round_val = record.get("round", 0)
        created_round = task.get("created_round", 0)
        
        if created_round > round_val:
            result["status"] = "FAIL"
            result["errors"].append({
                "type": "cross_field_constraint",
                "constraint": "task.created_round <= round",
                "actual": f"created_round={created_round}, round={round_val}",
                "message": f"task.created_round ({created_round}) > round ({round_val}). Ref: x-validator-notes.cross_field_constraints[0]"
            })
            return result
    
    # Constraint 2: sic_version '2.0' with task → REJECT
    sic_version = record.get("sic_version", "")
    if sic_version == "2.0" and "task" in record and record["task"] is not None:
        result["status"] = "FAIL"
        result["errors"].append({
            "type": "forward_compatibility",
            "constraint": "sic_version '2.0' with task → REJECT",
            "message": "v2.0 records MUST NOT contain task field. Ref: x-validator-notes.forward_compatibility[2]"
        })
        return result
    
    # --- Layer 3: Semantic Warnings ---
    
    # Warning: current_action null → semantic_rupture
    state = record.get("state", {})
    if state and state.get("current_action") is None:
        result["warnings"].append({
            "type": "semantic_rupture",
            "field": "state.current_action",
            "message": "current_action is null → semantic_rupture detected. Ref: x-validator-notes.cross_field_constraints[2]"
        })
        if result["status"] == "PASS":
            result["status"] = "WARN"
    
    return result


def validate_file(filepath: str) -> dict:
    """Validate a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            record = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "file": filepath,
            "status": "FAIL",
            "errors": [{"type": "json_parse", "message": str(e)}],
            "warnings": []
        }
    except FileNotFoundError:
        return {
            "file": filepath,
            "status": "FAIL",
            "errors": [{"type": "file_not_found", "message": f"File not found: {filepath}"}],
            "warnings": []
        }
    
    schema = load_schema()
    result = validate_record(record, schema)
    result["file"] = filepath
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sic_validate.py <json_file_path>")
        print("       python3 sic_validate.py --batch <dir_path>")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Usage: python3 sic_validate.py --batch <dir_path>")
            sys.exit(1)
        dir_path = Path(sys.argv[2])
        results = []
        for f in sorted(dir_path.glob("*.json")):
            r = validate_file(str(f))
            results.append(r)
            status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(r["status"], "?")
            print(f"{status_icon} {r['status']}: {f.name}")
            if r["errors"]:
                for err in r["errors"]:
                    print(f"   ERROR: {err['message']}")
            if r["warnings"]:
                for warn in r["warnings"]:
                    print(f"   WARN: {warn['message']}")
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        warned = sum(1 for r in results if r["status"] == "WARN")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        print(f"\n--- SUMMARY ---")
        print(f"TOTAL: {total}  PASS: {passed}  WARN: {warned}  FAIL: {failed}")
    else:
        filepath = sys.argv[1]
        result = validate_file(filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Exit code
        if result["status"] == "FAIL":
            sys.exit(1)
        elif result["status"] == "WARN":
            sys.exit(0)  # WARN is not failure
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
