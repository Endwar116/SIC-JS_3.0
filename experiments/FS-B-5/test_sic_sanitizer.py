#!/usr/bin/env python3
"""
Test Suite for sic_sanitizer.py
EXP FS-B-5: 10 XSS attack vectors, all must be BLOCKED.

Each test injects a known XSS payload into a SIC-JS record field
and verifies the sanitizer correctly detects and blocks it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sic_sanitizer import validate_and_sanitize


def make_record(field_path: str, payload: str) -> dict:
    """Create a SIC-JS record with a payload injected into the specified field."""
    record = {
        "sic_version": "3.0",
        "task": {
            "id": "A-1",
            "title": "Normal title",
            "deliverable": "Normal deliverable",
            "status": "pending",
            "created_round": 1,
            "owner": "test",
            "priority": "P2"
        },
        "round": 1,
        "entity": {"name": "test", "model": "test"},
        "state": {
            "context": "Normal context",
            "current_action": "Normal action"
        },
        "relation": {"user": "安安"}
    }
    
    # Inject payload into specified field
    parts = field_path.split(".")
    obj = record
    for part in parts[:-1]:
        obj = obj[part]
    obj[parts[-1]] = payload
    
    return record


# 10 XSS attack vectors from OWASP Top 10 + real-world exploits
XSS_VECTORS = [
    {
        "id": "XSS-01",
        "name": "Classic script tag injection",
        "field": "task.title",
        "payload": '<script>alert("XSS")</script>',
        "expected_vector": "script_tag"
    },
    {
        "id": "XSS-02",
        "name": "Event handler injection (onerror)",
        "field": "state.context",
        "payload": '<img src=x onerror=alert(1)>',
        "expected_vector": "event_handler"
    },
    {
        "id": "XSS-03",
        "name": "JavaScript URI in deliverable",
        "field": "task.deliverable",
        "payload": 'javascript:alert(document.cookie)',
        "expected_vector": "javascript_uri"
    },
    {
        "id": "XSS-04",
        "name": "SVG onload payload",
        "field": "entity.name",
        "payload": '<svg onload=alert(1)>',
        "expected_vector": "svg_onload"
    },
    {
        "id": "XSS-05",
        "name": "iframe injection",
        "field": "state.current_action",
        "payload": '<iframe src="https://evil.com/steal.js"></iframe>',
        "expected_vector": "iframe_injection"
    },
    {
        "id": "XSS-06",
        "name": "CSS expression (IE legacy)",
        "field": "task.title",
        "payload": 'background: expression(alert(1))',
        "expected_vector": "css_expression"
    },
    {
        "id": "XSS-07",
        "name": "Prototype pollution via __proto__",
        "field": "entity.name",
        "payload": '{"__proto__": {"isAdmin": true}}',
        "expected_vector": "prototype_pollution"
    },
    {
        "id": "XSS-08",
        "name": "Object tag injection",
        "field": "state.context",
        "payload": '<object data="data:text/html,<script>alert(1)</script>">',
        "expected_vector": "object_tag"
    },
    {
        "id": "XSS-09",
        "name": "Embed tag injection",
        "field": "task.deliverable",
        "payload": '<embed src="javascript:alert(1)">',
        "expected_vector": "embed_tag"
    },
    {
        "id": "XSS-10",
        "name": "Prototype pollution via __proto__ key in record",
        "field": "SPECIAL",  # Special handling: inject __proto__ as a key
        "payload": "__proto__",
        "expected_vector": "prototype_pollution"
    },
]


def run_tests():
    print("=" * 60)
    print("SIC-JS Enterprise Security Stack - XSS Test Suite")
    print("EXP FS-B-5 | 10 XSS Vectors, All Must Be BLOCKED")
    print("=" * 60)
    print()
    
    total = 10
    passed = 0
    
    for vector in XSS_VECTORS:
        vid = vector["id"]
        name = vector["name"]
        
        if vector["field"] == "SPECIAL":
            # XSS-10: Inject __proto__ as actual key
            record = {
                "sic_version": "3.0",
                "__proto__": {"isAdmin": True},
                "task": {
                    "id": "A-1",
                    "title": "Normal",
                    "deliverable": "Normal",
                    "status": "pending",
                    "created_round": 1,
                    "owner": None,
                    "priority": None
                },
                "round": 1,
                "entity": {"name": "test", "model": "test"},
                "state": {"context": "test", "current_action": "test"},
                "relation": {"user": "安安"}
            }
        else:
            record = make_record(vector["field"], vector["payload"])
        
        result = validate_and_sanitize(record)
        
        # Check: must be BLOCKED
        is_blocked = result["action"] == "BLOCK"
        
        # Check: correct vector type detected
        detected_types = [b["vector_type"] for b in result["blocked_vectors"]]
        correct_type = vector["expected_vector"] in detected_types
        
        test_pass = is_blocked and correct_type
        icon = "✅" if test_pass else "❌"
        
        print(f"  {icon} {vid}: {name}")
        if not test_pass:
            print(f"     Expected: BLOCK with '{vector['expected_vector']}'")
            print(f"     Got: action={result['action']}, vectors={detected_types}")
        
        if test_pass:
            passed += 1
    
    print()
    print("-" * 60)
    print(f"TOTAL: {total}  BLOCKED: {passed}  MISSED: {total - passed}")
    print("-" * 60)
    
    if passed == total:
        print("🎉 EXP FS-B-5 COMPLETE: All 10/10 XSS vectors blocked!")
        sys.exit(0)
    else:
        print(f"⚠️  EXP FS-B-5 INCOMPLETE: {passed}/{total} blocked")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
