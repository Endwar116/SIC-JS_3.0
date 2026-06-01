#!/usr/bin/env python3
"""
SIC-JS Enterprise Security Sanitizer
EXP FS-B-5: Input sanitization layer for SIC-JS records before DOM rendering.

Architecture:
- Layer 1: JSON Schema validation (reuse FS-B-1 validator)
- Layer 2: String field sanitization (XSS prevention)
- Layer 3: Structural integrity (no prototype pollution, no __proto__)

Design principle: "Closed Shadow DOM + one-way semantic flow"
  - Data flows: SIC-JS JSON → Sanitizer → DOM (never reverse)
  - All string fields are HTML-escaped before rendering
  - No innerHTML; only textContent or setAttribute with sanitized values

Ref: Paper_11_Enterprise_Security_Architecture.md
"""

import re
import json
import html
from typing import Dict, List, Tuple

# === XSS Prevention Patterns ===
# These patterns detect common XSS vectors in string fields
XSS_PATTERNS = [
    (re.compile(r'<script\b', re.IGNORECASE), "script_tag"),
    (re.compile(r'javascript:', re.IGNORECASE), "javascript_uri"),
    (re.compile(r'on\w+\s*=', re.IGNORECASE), "event_handler"),
    (re.compile(r'<iframe\b', re.IGNORECASE), "iframe_injection"),
    (re.compile(r'<object\b', re.IGNORECASE), "object_tag"),
    (re.compile(r'<embed\b', re.IGNORECASE), "embed_tag"),
    (re.compile(r'<svg\b.*?onload', re.IGNORECASE | re.DOTALL), "svg_onload"),
    (re.compile(r'expression\s*\(', re.IGNORECASE), "css_expression"),
    (re.compile(r'url\s*\(\s*["\']?\s*javascript:', re.IGNORECASE), "css_javascript_url"),
    (re.compile(r'__proto__', re.IGNORECASE), "prototype_pollution"),
]

# Dangerous keys that should never appear in SIC-JS records
FORBIDDEN_KEYS = {"__proto__", "constructor", "prototype", "__defineGetter__", "__defineSetter__"}


class SanitizationResult:
    """Result of sanitization check."""
    
    def __init__(self):
        self.blocked: List[Dict] = []
        self.sanitized_record: Dict = {}
        self.is_safe: bool = True
    
    def add_block(self, field: str, vector_type: str, original_value: str):
        self.blocked.append({
            "field": field,
            "vector_type": vector_type,
            "original_value": original_value[:100]  # Truncate for safety
        })
        self.is_safe = False


def sanitize_string(value: str) -> Tuple[str, List[str]]:
    """
    Sanitize a string value for safe DOM rendering.
    Returns (sanitized_value, list_of_detected_vectors).
    """
    detected = []
    
    for pattern, vector_type in XSS_PATTERNS:
        if pattern.search(value):
            detected.append(vector_type)
    
    # HTML-escape the value regardless
    sanitized = html.escape(value, quote=True)
    
    return sanitized, detected


def check_forbidden_keys(obj: any, path: str = "") -> List[Dict]:
    """Recursively check for forbidden keys (prototype pollution prevention)."""
    findings = []
    
    if isinstance(obj, dict):
        for key in obj:
            if key in FORBIDDEN_KEYS:
                findings.append({
                    "field": f"{path}.{key}" if path else key,
                    "vector_type": "prototype_pollution",
                    "original_value": str(obj[key])[:100]
                })
            findings.extend(check_forbidden_keys(obj[key], f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            findings.extend(check_forbidden_keys(item, f"{path}[{i}]"))
    
    return findings


def sanitize_record(record: Dict) -> SanitizationResult:
    """
    Full sanitization pipeline for a SIC-JS record.
    
    Steps:
    1. Check for forbidden keys (prototype pollution)
    2. Scan all string fields for XSS vectors
    3. HTML-escape all string values
    4. Return sanitized record + block report
    """
    result = SanitizationResult()
    
    # Step 1: Forbidden keys check
    forbidden = check_forbidden_keys(record)
    for f in forbidden:
        result.add_block(f["field"], f["vector_type"], f["original_value"])
    
    # Step 2 & 3: Recursively sanitize all string fields
    result.sanitized_record = _deep_sanitize(record, result, "")
    
    return result


def _deep_sanitize(obj: any, result: SanitizationResult, path: str) -> any:
    """Recursively sanitize all string values in a nested structure."""
    if isinstance(obj, dict):
        sanitized = {}
        for key, value in obj.items():
            if key in FORBIDDEN_KEYS:
                continue  # Strip forbidden keys entirely
            new_path = f"{path}.{key}" if path else key
            sanitized[key] = _deep_sanitize(value, result, new_path)
        return sanitized
    elif isinstance(obj, list):
        return [_deep_sanitize(item, result, f"{path}[{i}]") for i, item in enumerate(obj)]
    elif isinstance(obj, str):
        sanitized_value, detected = sanitize_string(obj)
        for vector_type in detected:
            result.add_block(path, vector_type, obj)
        return sanitized_value
    else:
        return obj  # numbers, booleans, null pass through


def validate_and_sanitize(record: Dict) -> Dict:
    """
    Combined validation + sanitization endpoint.
    Returns a report suitable for logging/audit.
    """
    san_result = sanitize_record(record)
    
    return {
        "is_safe": san_result.is_safe,
        "blocked_count": len(san_result.blocked),
        "blocked_vectors": san_result.blocked,
        "sanitized_record": san_result.sanitized_record if san_result.is_safe else None,
        "action": "PASS" if san_result.is_safe else "BLOCK"
    }
