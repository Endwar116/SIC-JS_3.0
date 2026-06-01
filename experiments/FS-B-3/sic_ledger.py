#!/usr/bin/env python3
"""
SIC-JS v3.0 SQLite Task Ledger
EXP FS-B-3: Persistent layer for task management with FROZEN constraints.

Features:
- task_id uniqueness enforced at DB level (UNIQUE constraint)
- created_round immutability (application-level check)
- Status state machine: completed/dismissed → terminal (no further changes)
- archived → can be recalled to pending/in_progress
- Query by prefix pattern

Alignment:
- Schema: sic-js-schema-v3.0.json
- Spec: SICJS_30_技術原始記載檔 §1.6 (task_id FROZEN)
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import Optional, List, Dict

TASK_ID_PATTERN = re.compile(r"^([A-Z]+-)?[A-Z]{1,2}-[1-9][0-9]{0,2}$")
VALID_STATUSES = {"pending", "in_progress", "completed", "dismissed", "archived"}
TERMINAL_STATUSES = {"completed", "dismissed"}


class SicLedger:
    """SQLite-backed persistent task ledger for SIC-JS v3.0."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read/write performance
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self._lock = __import__('threading').Lock()
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                deliverable TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_round INTEGER NOT NULL,
                owner TEXT,
                priority TEXT DEFAULT 'P2',
                time_horizon TEXT,
                inserted_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_prefix ON tasks(task_id);
        """)
        self.conn.commit()
    
    def insert_task(self, task: Dict, round_val: int) -> Dict:
        """
        Insert a new task into the ledger.
        
        Raises:
            ValueError: if task_id format invalid or created_round > round
            sqlite3.IntegrityError: if task_id already exists (uniqueness enforced)
        """
        task_id = task.get("id", "")
        title = task.get("title", "")
        deliverable = task.get("deliverable", "")
        status = task.get("status", "pending")
        created_round = task.get("created_round", 0)
        owner = task.get("owner")
        priority = task.get("priority", "P2")
        time_horizon = task.get("time_horizon")
        
        # Validation: task_id format
        if not TASK_ID_PATTERN.match(task_id):
            raise ValueError(f"Invalid task_id format: '{task_id}'. Must match {TASK_ID_PATTERN.pattern}")
        
        # Validation: status
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: '{status}'. Must be one of {VALID_STATUSES}")
        
        # Validation: created_round <= round (cross-field constraint)
        if created_round > round_val:
            raise ValueError(
                f"created_round ({created_round}) > round ({round_val}). "
                f"Ref: x-validator-notes.cross_field_constraints[0]"
            )
        
        # Insert (uniqueness enforced by PRIMARY KEY)
        with self._lock:
            self.conn.execute(
                """INSERT INTO tasks (task_id, title, deliverable, status, created_round, owner, priority, time_horizon)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, title, deliverable, status, created_round, owner, priority, time_horizon)
            )
            self.conn.commit()
        
        return {"status": "success", "task_id": task_id}
    
    def update_status(self, task_id: str, new_status: str) -> Dict:
        """
        Update task status with state machine enforcement.
        
        Rules:
        - completed → TERMINAL (no further changes)
        - dismissed → TERMINAL (no further changes)
        - archived → can be recalled to pending/in_progress
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: '{new_status}'")
        
        # Get current status
        with self._lock:
            row = self.conn.execute(
                "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            
            if row is None:
                raise ValueError(f"Task not found: '{task_id}'")
            
            current_status = row["status"]
            
            # Terminal state check
            if current_status in TERMINAL_STATUSES:
                raise ValueError(
                    f"Task '{task_id}' is in terminal status '{current_status}'. "
                    f"Cannot change to '{new_status}'. Ref: PTGR C4 (completed/dismissed are final)."
                )
            
            # Archived recall: only to pending or in_progress
            if current_status == "archived" and new_status not in {"pending", "in_progress"}:
                raise ValueError(
                    f"Archived task can only be recalled to 'pending' or 'in_progress', not '{new_status}'."
                )
            
            self.conn.execute(
                "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE task_id = ?",
                (new_status, task_id)
            )
            self.conn.commit()
        
        return {"status": "success", "task_id": task_id, "old_status": current_status, "new_status": new_status}
    
    def query_by_status(self, status: str) -> List[Dict]:
        """Query tasks by status."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_round", (status,)
            ).fetchall()
            return [dict(r) for r in rows]
    
    def query_by_prefix(self, prefix: str) -> List[Dict]:
        """Query tasks by ID prefix pattern (e.g., 'FS-B-')."""
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE task_id LIKE ? ORDER BY task_id", (f"{prefix}%",)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a single task by ID."""
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def close(self):
        """Close database connection."""
        self.conn.close()
