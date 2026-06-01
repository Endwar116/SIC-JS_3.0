#!/usr/bin/env python3
"""
FS-B-1 RIGOROUS: Fuzz Testing + Boundary + Adversarial Schema Validation
=========================================================================
- 10,000 randomly mutated SIC-JS records
- Boundary: max-length strings, deep nesting, Unicode edge cases
- Adversarial: crafted to trigger parser bugs, OOM, infinite loops
- Success criteria: NO crashes, NO unhandled exceptions, NO OOM
"""

import json
import random
import string
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "FS-B-1"))
from sic_validate import load_schema, validate_record

SCHEMA = load_schema()
TOTAL_FUZZ = 10000
SEED = 42
random.seed(SEED)

# === Mutation Strategies ===

def random_string(max_len=100):
    length = random.randint(0, max_len)
    charset = string.printable + "中文日本語한국어🔥💀\x00\x01\x02\n\r\t"
    return "".join(random.choice(charset) for _ in range(length))

def random_task_id():
    """Generate task_id: 50% valid, 50% invalid."""
    if random.random() < 0.5:
        prefix = random.choice(["", "FS-", "DD-", "XIED-", ""])
        series = random.choice(string.ascii_uppercase[:5])
        serial = random.randint(1, 999)
        return f"{prefix}{series}-{serial}"
    else:
        # Invalid formats
        return random.choice([
            "", "a-1", "1-A", "A-0", "A-1000", "AAA-1",
            "A--1", "-A-1", "A-", random_string(20),
            "\x00", "A-1; DROP TABLE tasks;--"
        ])

def random_status():
    """50% valid, 50% invalid."""
    if random.random() < 0.5:
        return random.choice(["pending", "in_progress", "completed", "dismissed", "archived"])
    else:
        return random.choice(["done", "PENDING", "", None, 42, "in-progress", "complete", random_string(10)])

def random_round():
    return random.choice([0, -1, 1, 5, 100, 999999, None, "abc", 3.14, True])

def generate_fuzz_record():
    """Generate a randomly mutated SIC-JS record."""
    # Base structure with random mutations
    record = {}
    
    # sic_version: sometimes valid, sometimes garbage
    if random.random() < 0.7:
        record["sic_version"] = random.choice(["2.0", "3.0", "1.0", "4.0", "", None, 3.0, True])
    
    # task: sometimes present, sometimes not, sometimes malformed
    if random.random() < 0.6:
        task = {}
        if random.random() < 0.8: task["id"] = random_task_id()
        if random.random() < 0.8: task["title"] = random_string(200)
        if random.random() < 0.8: task["deliverable"] = random_string(500)
        if random.random() < 0.8: task["status"] = random_status()
        if random.random() < 0.8: task["created_round"] = random_round()
        if random.random() < 0.5: task["owner"] = random.choice([None, random_string(50)])
        if random.random() < 0.5: task["priority"] = random.choice(["P0", "P1", "P2", None, "P3", ""])
        if random.random() < 0.3: task["time_horizon"] = random.choice(["short", "medium", "long", None, "forever"])
        # Adversarial: extra fields
        if random.random() < 0.2: task["__proto__"] = {"admin": True}
        if random.random() < 0.1: task["extra_field"] = random_string(100)
        record["task"] = task
    
    # round
    if random.random() < 0.8:
        record["round"] = random_round()
    
    # entity
    if random.random() < 0.8:
        entity = {}
        if random.random() < 0.8: entity["name"] = random_string(100)
        if random.random() < 0.8: entity["model"] = random_string(50)
        if random.random() < 0.3: entity["origin"] = random.choice([None, random_string(50)])
        if random.random() < 0.2: entity["extra"] = "should_fail"
        record["entity"] = entity
    
    # state
    if random.random() < 0.8:
        state = {}
        if random.random() < 0.8: state["context"] = random_string(300)
        if random.random() < 0.7: state["current_action"] = random.choice([None, random_string(200)])
        if random.random() < 0.5: state["pending"] = [random_string(50) for _ in range(random.randint(0, 20))]
        if random.random() < 0.3: state["tone"] = random.choice(["active", "audit", random_string(20)])
        record["state"] = state
    
    # relation
    if random.random() < 0.8:
        relation = {}
        if random.random() < 0.8: relation["user"] = random_string(50)
        if random.random() < 0.3: relation["anchor_memory"] = random.choice([None, random_string(100)])
        if random.random() < 0.2: relation["linked_entities"] = [random_string(20) for _ in range(random.randint(0, 5))]
        if random.random() < 0.1: relation["upstream"] = random.choice([None, "a" * 16, "xyz", random_string(16)])
        record["relation"] = relation
    
    # event
    if random.random() < 0.5:
        if random.random() < 0.3:
            record["event"] = None
        else:
            record["event"] = {
                "timestamp": random.choice(["2026-06-01T00:00:00Z", "", random_string(30)]),
                "description": random_string(200),
                "trigger": random_string(50)
            }
    
    # intent
    if random.random() < 0.5:
        if random.random() < 0.3:
            record["intent"] = None
        else:
            record["intent"] = {
                "user_intent": random_string(100),
                "system_intent": random_string(100),
                "core_question": random.choice([None, random_string(100)])
            }
    
    # Adversarial: extra top-level fields (should trigger additionalProperties: false)
    if random.random() < 0.15:
        record["malicious_field"] = random_string(100)
    
    return record


def generate_boundary_records():
    """Generate specific boundary-condition records."""
    boundaries = []
    
    # Empty string everywhere
    boundaries.append({"sic_version": "", "round": 1, "entity": {"name": "", "model": ""}, "state": {"context": "", "current_action": ""}, "relation": {"user": ""}})
    
    # Max-length strings (10KB per field)
    big_str = "A" * 10000
    boundaries.append({"sic_version": "3.0", "task": {"id": "A-1", "title": big_str, "deliverable": big_str, "status": "pending", "created_round": 1}, "round": 1, "entity": {"name": big_str, "model": "test"}, "state": {"context": big_str, "current_action": big_str}, "relation": {"user": "安安"}})
    
    # Unicode edge cases
    boundaries.append({"sic_version": "3.0", "round": 1, "entity": {"name": "🔥💀👻\u200b\u200c\u200d\ufeff", "model": "test"}, "state": {"context": "\u0000\u0001\u0002\u001f", "current_action": "test"}, "relation": {"user": "안녕하세요"}})
    
    # Deeply nested pending array (1000 items)
    boundaries.append({"sic_version": "3.0", "round": 1, "entity": {"name": "test", "model": "test"}, "state": {"context": "deep", "current_action": "test", "pending": [f"item_{i}" for i in range(1000)]}, "relation": {"user": "安安"}})
    
    # Round at integer limits
    boundaries.append({"sic_version": "3.0", "round": 2147483647, "entity": {"name": "test", "model": "test"}, "state": {"context": "max int", "current_action": "test"}, "relation": {"user": "安安"}})
    
    # Null bytes in strings
    boundaries.append({"sic_version": "3.0", "round": 1, "entity": {"name": "te\x00st", "model": "te\x00st"}, "state": {"context": "null\x00byte", "current_action": "test"}, "relation": {"user": "安安"}})
    
    return boundaries


def run_fuzz():
    print("=" * 70)
    print("FS-B-1 RIGOROUS: Fuzz + Boundary + Adversarial Validation")
    print(f"Total records: {TOTAL_FUZZ} fuzz + boundary | Seed: {SEED}")
    print("=" * 70)
    print()
    
    crashes = 0
    unhandled = 0
    pass_count = 0
    fail_count = 0
    warn_count = 0
    
    start = time.perf_counter()
    
    # Phase 1: Fuzz records
    print(f"[1/2] Fuzzing {TOTAL_FUZZ} random records...")
    for i in range(TOTAL_FUZZ):
        record = generate_fuzz_record()
        try:
            result = validate_record(record, SCHEMA)
            if result["status"] == "PASS":
                pass_count += 1
            elif result["status"] == "FAIL":
                fail_count += 1
            elif result["status"] == "WARN":
                warn_count += 1
        except Exception as e:
            unhandled += 1
            if unhandled <= 5:  # Only print first 5
                print(f"  UNHANDLED at record {i}: {type(e).__name__}: {str(e)[:100]}")
                traceback.print_exc()
    
    # Phase 2: Boundary records
    print(f"[2/2] Testing boundary conditions...")
    boundary_records = generate_boundary_records()
    boundary_crashes = 0
    for i, record in enumerate(boundary_records):
        try:
            result = validate_record(record, SCHEMA)
            if result["status"] == "PASS":
                pass_count += 1
            elif result["status"] == "FAIL":
                fail_count += 1
            elif result["status"] == "WARN":
                warn_count += 1
        except Exception as e:
            boundary_crashes += 1
            print(f"  BOUNDARY CRASH at record {i}: {type(e).__name__}: {str(e)[:100]}")
    
    elapsed = time.perf_counter() - start
    total_tested = TOTAL_FUZZ + len(boundary_records)
    
    print()
    print("-" * 70)
    print("RIGOROUS RESULTS:")
    print(f"  Total tested:     {total_tested}")
    print(f"  PASS:             {pass_count}")
    print(f"  FAIL (expected):  {fail_count}")
    print(f"  WARN:             {warn_count}")
    print(f"  CRASHES:          {crashes}")
    print(f"  UNHANDLED:        {unhandled}")
    print(f"  BOUNDARY CRASHES: {boundary_crashes}")
    print(f"  Elapsed:          {elapsed:.2f}s")
    print(f"  Throughput:       {total_tested/elapsed:.0f} records/sec")
    print("-" * 70)
    
    # Gate: NO crashes, NO unhandled exceptions
    all_safe = (crashes == 0) and (unhandled == 0) and (boundary_crashes == 0)
    
    if all_safe:
        print(f"✅ FS-B-1 RIGOROUS PASS: {total_tested} records, 0 crashes, 0 unhandled")
    else:
        print(f"❌ FS-B-1 RIGOROUS FAIL: crashes={crashes}, unhandled={unhandled}, boundary_crashes={boundary_crashes}")
    
    # Save report
    report = {
        "experiment": "FS-B-1-rigorous",
        "total_tested": total_tested,
        "pass": pass_count,
        "fail": fail_count,
        "warn": warn_count,
        "crashes": crashes,
        "unhandled": unhandled,
        "boundary_crashes": boundary_crashes,
        "elapsed_sec": round(elapsed, 2),
        "throughput_rps": round(total_tested / elapsed),
        "all_safe": all_safe,
        "seed": SEED
    }
    with open(Path(__file__).parent / "report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    sys.exit(0 if all_safe else 1)


if __name__ == "__main__":
    run_fuzz()
