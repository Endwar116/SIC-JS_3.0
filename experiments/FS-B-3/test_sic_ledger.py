#!/usr/bin/env python3
"""
Test Suite for sic_ledger.py
EXP FS-B-3: 9 test cases as specified in the experiment brief.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sic_ledger import SicLedger


def run_tests():
    print("=" * 60)
    print("SIC-JS v3.0 SQLite Task Ledger - Test Suite")
    print("EXP FS-B-3 | 9 Test Cases")
    print("=" * 60)
    print()
    
    total = 9
    passed = 0
    
    # --- T1: 插入合法 task → success ---
    print("T1: Insert valid task → success")
    try:
        ledger = SicLedger(":memory:")
        result = ledger.insert_task({
            "id": "FS-B-1",
            "title": "Validator CLI",
            "deliverable": "8/8 tests pass",
            "status": "completed",
            "created_round": 1,
            "owner": "咩咩",
            "priority": "P0"
        }, round_val=5)
        assert result["status"] == "success"
        print("  ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T2: 插入重複 task_id → IntegrityError ---
    print("T2: Insert duplicate task_id → IntegrityError")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "First", "deliverable": "d1", "status": "pending", "created_round": 1}, round_val=1)
        try:
            ledger.insert_task({"id": "A-1", "title": "Duplicate", "deliverable": "d2", "status": "pending", "created_round": 1}, round_val=1)
            print("  ❌ FAIL: No exception raised")
        except sqlite3.IntegrityError:
            print("  ✅ PASS")
            passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T3: created_round > round → ValueError ---
    print("T3: created_round > round → ValueError")
    try:
        ledger = SicLedger(":memory:")
        try:
            ledger.insert_task({"id": "A-1", "title": "Future", "deliverable": "d", "status": "pending", "created_round": 10}, round_val=5)
            print("  ❌ FAIL: No exception raised")
        except ValueError as e:
            assert "created_round" in str(e)
            print("  ✅ PASS")
            passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T4: dismissed task → status 不可再改 ---
    print("T4: Dismissed task → status cannot change")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "T", "deliverable": "d", "status": "dismissed", "created_round": 1}, round_val=1)
        try:
            ledger.update_status("A-1", "in_progress")
            print("  ❌ FAIL: No exception raised")
        except ValueError as e:
            assert "terminal" in str(e).lower()
            print("  ✅ PASS")
            passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T5: completed task → status 不可再改 ---
    print("T5: Completed task → status cannot change")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "T", "deliverable": "d", "status": "completed", "created_round": 1}, round_val=1)
        try:
            ledger.update_status("A-1", "pending")
            print("  ❌ FAIL: No exception raised")
        except ValueError as e:
            assert "terminal" in str(e).lower()
            print("  ✅ PASS")
            passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T6: archived task → 可召回（→ pending / in_progress）---
    print("T6: Archived task → can be recalled to pending/in_progress")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "T", "deliverable": "d", "status": "archived", "created_round": 1}, round_val=1)
        result = ledger.update_status("A-1", "pending")
        assert result["new_status"] == "pending"
        # Also test recall to in_progress
        ledger2 = SicLedger(":memory:")
        ledger2.insert_task({"id": "B-1", "title": "T2", "deliverable": "d2", "status": "archived", "created_round": 1}, round_val=1)
        result2 = ledger2.update_status("B-1", "in_progress")
        assert result2["new_status"] == "in_progress"
        print("  ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
        ledger2.close()
    
    # --- T7: query pending tasks → 正確列出 ---
    print("T7: Query pending tasks → correct list")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "Pending1", "deliverable": "d", "status": "pending", "created_round": 1}, round_val=5)
        ledger.insert_task({"id": "A-2", "title": "Active", "deliverable": "d", "status": "in_progress", "created_round": 2}, round_val=5)
        ledger.insert_task({"id": "A-3", "title": "Pending2", "deliverable": "d", "status": "pending", "created_round": 3}, round_val=5)
        
        results = ledger.query_by_status("pending")
        assert len(results) == 2
        assert results[0]["task_id"] == "A-1"
        assert results[1]["task_id"] == "A-3"
        print("  ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T8: query by prefix（FS-B-*）→ 正確過濾 ---
    print("T8: Query by prefix (FS-B-) → correct filter")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "FS-B-1", "title": "Validator", "deliverable": "d", "status": "completed", "created_round": 1}, round_val=5)
        ledger.insert_task({"id": "FS-B-2", "title": "Streaming", "deliverable": "d", "status": "in_progress", "created_round": 2}, round_val=5)
        ledger.insert_task({"id": "FS-A-1", "title": "Other", "deliverable": "d", "status": "pending", "created_round": 3}, round_val=5)
        
        results = ledger.query_by_prefix("FS-B-")
        assert len(results) == 2
        assert all(r["task_id"].startswith("FS-B-") for r in results)
        print("  ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # --- T9: 記錄保留（dismissed 後仍可查詢）---
    print("T9: Dismissed task record preserved (queryable)")
    try:
        ledger = SicLedger(":memory:")
        ledger.insert_task({"id": "A-1", "title": "Dismissed", "deliverable": "d", "status": "dismissed", "created_round": 1}, round_val=1)
        task = ledger.get_task("A-1")
        assert task is not None
        assert task["status"] == "dismissed"
        assert task["title"] == "Dismissed"
        print("  ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    finally:
        ledger.close()
    
    # Summary
    print()
    print("-" * 60)
    print(f"TOTAL: {total}  PASS: {passed}  FAIL: {total - passed}")
    print("-" * 60)
    
    if passed == total:
        print("🎉 EXP FS-B-3 COMPLETE: All 9/9 test cases passed!")
        sys.exit(0)
    else:
        print(f"⚠️  EXP FS-B-3 INCOMPLETE: {passed}/{total} passed")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
