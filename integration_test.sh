#!/usr/bin/env bash
# =============================================================================
# SIC-JS v3.0 Integration Test Suite
# =============================================================================
# Usage: bash integration_test.sh
# Expected: All tests PASS
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TOTAL=0
PASS=0
FAIL=0

run_test() {
    local name="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    echo -n "  [$TOTAL] $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL"
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================================"
echo "SIC-JS v3.0 Integration Test Suite"
echo "============================================================"
echo ""

# --- Module 1: Schema Validation ---
echo "[Module 1] Schema & Validator (packages/core/validator)"
run_test "Schema file exists" "test -f packages/core/schema/sic-js-schema-v3.0.json"
run_test "Validator 8/8 test cases" "python3 packages/core/validator/test_sic_validate.py"
echo ""

# --- Module 2: Persistence ---
echo "[Module 2] SQLite Ledger (packages/core/persistence)"
run_test "Ledger 9/9 test cases" "python3 packages/core/persistence/test_sic_ledger.py"
echo ""

# --- Module 3: Security ---
echo "[Module 3] Enterprise Security (packages/developer-sdk)"
run_test "XSS Sanitizer 10/10 blocked" "python3 packages/developer-sdk/test_sic_sanitizer.py"
echo ""

# --- Module 4: Examples ---
echo "[Module 4] Examples"
run_test "Minimal example runs" "python3 examples/minimal/run.py"
run_test "Task lifecycle example runs" "python3 examples/task-lifecycle/run.py"
echo ""

# --- Module 5: File Integrity ---
echo "[Module 5] File Integrity"
run_test "README.md exists" "test -f README.md"
run_test "LICENSE exists" "test -f LICENSE"
run_test "CONTRIBUTING.md exists" "test -f CONTRIBUTING.md"
run_test "Rendering spec exists" "test -f spec/SIC_JS_RENDERING_SPEC_v1.1.md"
run_test "Protocol spec exists" "test -f spec/SICJS_30_技術原始記載檔.md"
run_test "Web Components exists" "test -f packages/developer-sdk/components.js"
echo ""

# --- Summary ---
echo "============================================================"
echo "TOTAL: $TOTAL  PASS: $PASS  FAIL: $FAIL"
echo "============================================================"

if [ $FAIL -eq 0 ]; then
    echo "✅ All Integration Tests PASS"
    exit 0
else
    echo "❌ Some tests FAILED"
    exit 1
fi
