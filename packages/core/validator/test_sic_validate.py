#!/usr/bin/env python3
"""
Test Suite for sic_validate.py
EXP FS-B-1: 8 test cases as specified in the experiment brief.
"""

import subprocess
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VALIDATE_SCRIPT = SCRIPT_DIR / "sic_validate.py"
FIXTURES_DIR = SCRIPT_DIR / "fixtures"

# Test case definitions: (fixture_file, expected_status, description)
TEST_CASES = [
    ("T1_v2_no_task.json", "PASS", "v2.0 無 task → PASS"),
    ("T2_v3_valid_task.json", "PASS", "v3.0 有 task，所有欄位合法 → PASS"),
    ("T3_null_action_warn.json", "WARN", "current_action: null → PASS + WARN: semantic_rupture"),
    ("T4_v2_with_task_reject.json", "FAIL", "v2.0 有 task → FAIL（正確拒絕）"),
    ("T5_empty_deliverable.json", "FAIL", "task.deliverable 空字串 → FAIL"),
    ("T6_prefix_format.json", "PASS", "FS-B-1 前綴格式 → PASS"),
    ("T7_invalid_status.json", "FAIL", "task.status 不在五狀態 → FAIL"),
    ("T8_created_round_exceeds.json", "FAIL", "task.created_round > round → FAIL"),
]


def run_test(fixture_file: str, expected_status: str, description: str) -> bool:
    """Run a single test case and return True if passed."""
    filepath = FIXTURES_DIR / fixture_file
    
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(filepath)],
        capture_output=True,
        text=True
    )
    
    try:
        output = json.loads(result.stdout)
        actual_status = output.get("status", "UNKNOWN")
    except json.JSONDecodeError:
        print(f"  ❌ FAILED TO PARSE OUTPUT: {result.stdout[:200]}")
        return False
    
    passed = actual_status == expected_status
    icon = "✅" if passed else "❌"
    print(f"  {icon} {fixture_file}: expected={expected_status}, actual={actual_status}")
    
    if not passed:
        print(f"     Description: {description}")
        print(f"     Output: {json.dumps(output, indent=2, ensure_ascii=False)[:300]}")
    
    # Additional check for T3: must have semantic_rupture warning
    if fixture_file == "T3_null_action_warn.json" and passed:
        warnings = output.get("warnings", [])
        has_rupture = any(w.get("type") == "semantic_rupture" for w in warnings)
        if not has_rupture:
            print(f"  ❌ T3 PASS but missing semantic_rupture warning!")
            return False
    
    return passed


def main():
    print("=" * 60)
    print("SIC-JS v3.0 Validator CLI - Test Suite")
    print("EXP FS-B-1 | 8 Test Cases")
    print("=" * 60)
    print()
    
    total = len(TEST_CASES)
    passed = 0
    
    for fixture_file, expected_status, description in TEST_CASES:
        if run_test(fixture_file, expected_status, description):
            passed += 1
    
    print()
    print("-" * 60)
    print(f"TOTAL: {total}  PASS: {passed}  FAIL: {total - passed}")
    print("-" * 60)
    
    if passed == total:
        print("🎉 EXP FS-B-1 COMPLETE: All 8/8 test cases passed!")
        sys.exit(0)
    else:
        print(f"⚠️  EXP FS-B-1 INCOMPLETE: {passed}/{total} passed")
        sys.exit(1)


if __name__ == "__main__":
    main()
