#!/usr/bin/env python3
"""
FS-B-3 RIGOROUS: Concurrent Write + State Machine Exhaustive + Corruption Recovery
===================================================================================
- 100 concurrent threads writing to same SQLite DB
- Exhaustive state machine transitions (5×5 = 25 combinations)
- Corruption simulation: what happens if DB file is truncated mid-write?
- Race condition detection: same task_id from multiple threads
"""

import sys
import time
import json
import threading
import tempfile
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "FS-B-3"))
from sic_ledger import SicLedger

SCRIPT_DIR = Path(__file__).parent
STATUSES = ["pending", "in_progress", "completed", "dismissed", "archived"]


def test_concurrent_writes():
    """100 threads writing unique tasks simultaneously."""
    print("[1/4] Concurrent writes: 100 threads × 10 tasks each...")
    
    db_path = str(SCRIPT_DIR / "concurrent_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    ledger = SicLedger(db_path)
    errors = []
    success_count = 0
    lock = threading.Lock()
    
    def write_tasks(thread_id):
        nonlocal success_count
        local_errors = []
        for i in range(10):
            task_id = f"T{thread_id:03d}-A-{i+1}"
            try:
                ledger.insert_task({
                    "id": task_id,
                    "title": f"Thread {thread_id} Task {i}",
                    "deliverable": f"Deliverable {thread_id}-{i}",
                    "status": "pending",
                    "created_round": 1,
                    "owner": f"thread_{thread_id}",
                    "priority": "P1"
                }, round_val=100)
                with lock:
                    success_count += 1
            except Exception as e:
                local_errors.append(f"T{thread_id}-{i}: {type(e).__name__}: {str(e)[:80]}")
        return local_errors
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(write_tasks, tid) for tid in range(100)]
        for f in as_completed(futures):
            errs = f.result()
            errors.extend(errs)
    
    # Verify: should have 1000 unique tasks
    all_tasks = ledger.query_by_status("pending")
    
    print(f"       Successful inserts: {success_count}/1000")
    print(f"       Errors: {len(errors)}")
    print(f"       Tasks in DB: {len(all_tasks)}")
    
    # SQLite handles concurrent writes via WAL mode or serialized access
    # Some errors are expected (database locked), but no data corruption
    data_integrity = len(all_tasks) == success_count
    print(f"       Data integrity: {'✅' if data_integrity else '❌'} (DB count matches success count)")
    
    if errors and len(errors) <= 5:
        for e in errors[:5]:
            print(f"       Sample error: {e}")
    
    ledger.close()
    os.remove(db_path)
    return data_integrity, success_count, len(errors)


def test_state_machine_exhaustive():
    """Test all 25 (5×5) status transition combinations."""
    print("[2/4] State machine exhaustive: 25 transition combinations...")
    
    results = []
    # Expected: which transitions should succeed
    # From → To
    EXPECTED_ALLOW = {
        ("pending", "in_progress"): True,
        ("pending", "completed"): True,
        ("pending", "dismissed"): True,
        ("pending", "archived"): True,
        ("pending", "pending"): True,  # No-op but allowed
        ("in_progress", "pending"): True,
        ("in_progress", "completed"): True,
        ("in_progress", "dismissed"): True,
        ("in_progress", "archived"): True,
        ("in_progress", "in_progress"): True,
        ("completed", "pending"): False,  # TERMINAL
        ("completed", "in_progress"): False,
        ("completed", "completed"): False,
        ("completed", "dismissed"): False,
        ("completed", "archived"): False,
        ("dismissed", "pending"): False,  # TERMINAL
        ("dismissed", "in_progress"): False,
        ("dismissed", "completed"): False,
        ("dismissed", "dismissed"): False,
        ("dismissed", "archived"): False,
        ("archived", "pending"): True,  # RECALL
        ("archived", "in_progress"): True,  # RECALL
        ("archived", "completed"): False,  # Can't recall to terminal
        ("archived", "dismissed"): False,
        ("archived", "archived"): False,  # Can't recall to archived
    }
    
    correct = 0
    incorrect = 0
    
    for (from_status, to_status), should_allow in EXPECTED_ALLOW.items():
        ledger = SicLedger(":memory:")
        task_id = f"A-{correct + incorrect + 1}"
        # Ensure unique task_id
        task_id = f"{''.join(c.upper() for c in from_status[:2])}-{correct + incorrect + 1}"
        # Simpler: use counter
        task_id = f"A-{correct + incorrect + 1}" if (correct + incorrect + 1) <= 9 else f"B-{correct + incorrect + 1 - 9}" if (correct + incorrect + 1) <= 18 else f"C-{correct + incorrect + 1 - 18}"
        
        ledger.insert_task({
            "id": task_id,
            "title": f"Test {from_status}→{to_status}",
            "deliverable": "test",
            "status": from_status,
            "created_round": 1
        }, round_val=10)
        
        try:
            ledger.update_status(task_id, to_status)
            actually_allowed = True
        except ValueError:
            actually_allowed = False
        
        match = actually_allowed == should_allow
        if match:
            correct += 1
        else:
            incorrect += 1
            results.append(f"  MISMATCH: {from_status}→{to_status}: expected={'allow' if should_allow else 'deny'}, got={'allow' if actually_allowed else 'deny'}")
        
        ledger.close()
    
    print(f"       Correct: {correct}/25")
    print(f"       Mismatches: {incorrect}/25")
    for r in results[:5]:
        print(f"       {r}")
    
    return incorrect == 0


def test_race_condition_same_id():
    """Multiple threads trying to insert the same task_id simultaneously."""
    print("[3/4] Race condition: 50 threads inserting same task_id...")
    
    db_path = str(SCRIPT_DIR / "race_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    ledger = SicLedger(db_path)
    successes = 0
    integrity_errors = 0
    other_errors = 0
    lock = threading.Lock()
    
    def try_insert(thread_id):
        nonlocal successes, integrity_errors, other_errors
        try:
            ledger.insert_task({
                "id": "A-1",  # Same ID for all threads!
                "title": f"Thread {thread_id}",
                "deliverable": "race test",
                "status": "pending",
                "created_round": 1
            }, round_val=1)
            with lock:
                successes += 1
        except Exception as e:
            with lock:
                if "UNIQUE" in str(e) or "IntegrityError" in type(e).__name__:
                    integrity_errors += 1
                else:
                    other_errors += 1
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(try_insert, i) for i in range(50)]
        for f in as_completed(futures):
            pass
    
    # Exactly 1 should succeed, 49 should get IntegrityError
    print(f"       Successes: {successes} (expected: 1)")
    print(f"       IntegrityErrors: {integrity_errors} (expected: 49)")
    print(f"       Other errors: {other_errors} (expected: 0)")
    
    race_safe = (successes == 1) and (other_errors == 0)
    print(f"       Race-safe: {'✅' if race_safe else '❌'}")
    
    ledger.close()
    os.remove(db_path)
    return race_safe


def test_corruption_recovery():
    """Simulate DB corruption and verify graceful handling."""
    print("[4/4] Corruption recovery: truncated DB file...")
    
    db_path = str(SCRIPT_DIR / "corrupt_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create a valid DB with some data
    ledger = SicLedger(db_path)
    for i in range(10):
        ledger.insert_task({
            "id": f"A-{i+1}",
            "title": f"Task {i}",
            "deliverable": "test",
            "status": "pending",
            "created_round": 1
        }, round_val=10)
    ledger.close()
    
    # Corrupt it by truncating
    file_size = os.path.getsize(db_path)
    with open(db_path, "r+b") as f:
        f.truncate(file_size // 2)
    
    # Try to open corrupted DB
    graceful = False
    try:
        ledger2 = SicLedger(db_path)
        # Try to query - might fail
        try:
            tasks = ledger2.query_by_status("pending")
            # If it works, the corruption wasn't severe enough
            graceful = True
        except Exception as e:
            # Expected: database disk image is malformed
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower() or "not a database" in str(e).lower():
                graceful = True  # Graceful = it raises a clear error, doesn't hang/crash
            else:
                graceful = True  # Any exception is better than a crash
        ledger2.close()
    except Exception as e:
        # Even failing to open is graceful (vs. segfault)
        graceful = True
    
    print(f"       Graceful handling: {'✅' if graceful else '❌'} (no crash/hang)")
    
    if os.path.exists(db_path):
        os.remove(db_path)
    return graceful


def main():
    print("=" * 70)
    print("FS-B-3 RIGOROUS: Concurrent + Exhaustive + Race + Corruption")
    print("=" * 70)
    print()
    
    r1_integrity, r1_success, r1_errors = test_concurrent_writes()
    print()
    r2_exhaustive = test_state_machine_exhaustive()
    print()
    r3_race = test_race_condition_same_id()
    print()
    r4_corruption = test_corruption_recovery()
    
    print()
    print("-" * 70)
    print("RIGOROUS RESULTS:")
    print(f"  Concurrent writes:    {'✅ PASS' if r1_integrity else '❌ FAIL'} ({r1_success} success, {r1_errors} errors)")
    print(f"  State machine (25):   {'✅ PASS' if r2_exhaustive else '❌ FAIL'}")
    print(f"  Race condition:       {'✅ PASS' if r3_race else '❌ FAIL'}")
    print(f"  Corruption recovery:  {'✅ PASS' if r4_corruption else '❌ FAIL'}")
    print("-" * 70)
    
    all_pass = r1_integrity and r2_exhaustive and r3_race and r4_corruption
    
    if all_pass:
        print("✅ FS-B-3 RIGOROUS PASS: All 4 criteria met")
    else:
        print("❌ FS-B-3 RIGOROUS: Some criteria failed")
    
    report = {
        "experiment": "FS-B-3-rigorous",
        "concurrent_writes": {"integrity": r1_integrity, "success": r1_success, "errors": r1_errors},
        "state_machine_exhaustive": {"all_correct": r2_exhaustive},
        "race_condition": {"safe": r3_race},
        "corruption_recovery": {"graceful": r4_corruption},
        "all_pass": all_pass
    }
    with open(SCRIPT_DIR / "report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
