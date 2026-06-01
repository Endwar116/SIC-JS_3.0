#!/usr/bin/env python3
"""
SIC-JS v3.0 Task Lifecycle Example
====================================
Demonstrates a complete task lifecycle:
  pending → in_progress → completed

Uses the SQLite ledger for persistence.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add packages to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "core" / "persistence"))

from sic_ledger import SicLedger


def main():
    print("=" * 50)
    print("SIC-JS v3.0 Task Lifecycle Example")
    print("=" * 50)
    print()
    
    # Use a temporary database
    db_path = tempfile.mktemp(suffix=".db")
    ledger = SicLedger(db_path)
    
    # 1. Create task (pending)
    task_data = {
        "id": "EX-A-1",
        "title": "Learn SIC-JS Task Lifecycle",
        "deliverable": "Understand pending → in_progress → completed flow",
        "status": "pending",
        "created_round": 1,
        "owner": "Developer",
        "priority": "P2"
    }
    result = ledger.insert_task(task_data, round_val=1)
    print(f"1. Task created: {result['task_id']}")
    print(f"   Status: pending")
    print()
    
    # 2. Start working (pending → in_progress)
    result = ledger.update_status("EX-A-1", "in_progress")
    print(f"2. Status transition: pending → in_progress")
    print(f"   Result: {result['status']}")
    print()
    
    # 3. PRE-EXECUTION CHECK (simulated)
    print("3. PRE-EXECUTION CHECK (PTGR C1~C5):")
    checks = [
        ("C1: Deliverable clearly defined", True),
        ("C2: Evidence criteria established", True),
        ("C3: No semantic rupture detected", True),
        ("C4: Bilateral confirmation possible", True),
        ("C5: Task within time horizon", True),
    ]
    all_pass = True
    for check_name, passed in checks:
        icon = "✅" if passed else "❌"
        print(f"   {icon} {check_name}")
        if not passed:
            all_pass = False
    
    if all_pass:
        print("   → All 5 conditions passed. Proceeding to completion.")
    print()
    
    # 4. Complete task (in_progress → completed)
    # In real usage, this requires bilateral confirmation (PTGR C4)
    result = ledger.update_status("EX-A-1", "completed")
    print(f"4. Status transition: in_progress → completed")
    print(f"   Result: {result['status']}")
    print(f"   (Bilateral confirmation simulated)")
    print()
    
    # 5. Verify terminal state (cannot change from completed)
    print("5. Terminal state verification:")
    try:
        ledger.update_status("EX-A-1", "in_progress")
        print("   ❌ ERROR: Should not be able to change from completed!")
    except ValueError as e:
        print(f"   ✅ Correctly blocked: {e}")
    print()
    
    # 6. Query by status
    pending = ledger.query_by_status("pending")
    completed = ledger.query_by_status("completed")
    print(f"6. Query results:")
    print(f"   Pending tasks: {len(pending)}")
    print(f"   Completed tasks: {len(completed)}")
    
    # Cleanup
    os.unlink(db_path)
    
    print()
    print("=" * 50)
    print("Lifecycle complete: pending → in_progress → completed (terminal)")
    print("=" * 50)


if __name__ == "__main__":
    main()
