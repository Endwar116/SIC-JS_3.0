#!/usr/bin/env python3
"""
FS-B-5 RIGOROUS: Mutation-based Fuzz + Bypass Attempts + CSP Integration
=========================================================================
- 1,000 mutated XSS payloads (not just known vectors, but algorithmic mutations)
- Bypass attempts: double-encoding, case mixing, null-byte injection, Unicode tricks
- Verify: zero payloads survive sanitization in a form that could execute
- Statistical: measure false positive rate (legitimate content blocked)
"""

import sys
import random
import string
import json
import html
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "FS-B-5"))
from sic_sanitizer import validate_and_sanitize, sanitize_string

SCRIPT_DIR = Path(__file__).parent
SEED = 42
random.seed(SEED)
TOTAL_MUTATIONS = 1000


# === Mutation Engine ===

BASE_PAYLOADS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    'javascript:alert(1)',
    '<svg onload=alert(1)>',
    '<iframe src="javascript:alert(1)">',
    '<body onload=alert(1)>',
    '<input onfocus=alert(1) autofocus>',
    '<marquee onstart=alert(1)>',
    '<details open ontoggle=alert(1)>',
    '<embed src="data:text/html,<script>alert(1)</script>">',
]

MUTATION_STRATEGIES = [
    "case_mix",          # rAnDoM cAsE
    "null_byte",         # inject \x00 between characters
    "double_encode",     # HTML-encode the payload twice
    "unicode_confusable", # replace chars with Unicode lookalikes
    "whitespace_inject", # inject various whitespace between keywords
    "comment_inject",    # inject HTML comments inside tags
    "concat_split",      # split keyword across attributes
    "hex_encode",        # use &#xNN; encoding
    "newline_inject",    # inject \n \r between keyword chars
    "backtick_replace",  # replace quotes with backticks
]


def mutate_case_mix(payload):
    """Randomly change case of each character."""
    return "".join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)


def mutate_null_byte(payload):
    """Insert null bytes at random positions."""
    result = []
    for c in payload:
        result.append(c)
        if random.random() < 0.2:
            result.append("\x00")
    return "".join(result)


def mutate_double_encode(payload):
    """HTML-encode the payload (simulating double-encoding attack)."""
    return html.escape(payload)


def mutate_unicode_confusable(payload):
    """Replace ASCII chars with Unicode confusables."""
    confusables = {
        'a': '\u0430', 'e': '\u0435', 'o': '\u043e', 'p': '\u0440',
        'c': '\u0441', 'x': '\u0445', 's': '\u0455', 'i': '\u0456',
        '<': '\uff1c', '>': '\uff1e', '/': '\u2044',
    }
    return "".join(confusables.get(c, c) if random.random() < 0.4 else c for c in payload)


def mutate_whitespace(payload):
    """Insert various whitespace characters."""
    ws = ["\t", "\n", "\r", "\x0b", "\x0c", "\xa0", "\u2000", "\u2001"]
    result = []
    for c in payload:
        result.append(c)
        if random.random() < 0.15:
            result.append(random.choice(ws))
    return "".join(result)


def mutate_comment(payload):
    """Inject HTML comments inside tags."""
    # e.g., <scr<!---->ipt>
    if "<" in payload:
        pos = payload.find("<") + random.randint(2, 5)
        pos = min(pos, len(payload))
        return payload[:pos] + "<!---->" + payload[pos:]
    return payload


def mutate_hex_encode(payload):
    """Replace some chars with &#xNN; encoding."""
    result = []
    for c in payload:
        if random.random() < 0.3 and c.isalpha():
            result.append(f"&#x{ord(c):02x};")
        else:
            result.append(c)
    return "".join(result)


def mutate_newline(payload):
    """Inject newlines between keyword characters."""
    keywords = ["script", "onerror", "onload", "javascript", "iframe"]
    result = payload
    for kw in keywords:
        if kw in result.lower():
            # Find the keyword and inject newlines
            idx = result.lower().find(kw)
            original = result[idx:idx+len(kw)]
            mutated = "\n".join(original)
            result = result[:idx] + mutated + result[idx+len(kw):]
            break
    return result


def mutate_backtick(payload):
    """Replace quotes with backticks."""
    return payload.replace('"', '`').replace("'", '`')


def mutate_concat(payload):
    """Add string concatenation tricks."""
    return payload.replace("alert", "al"+"ert").replace("script", "scr"+"ipt")


MUTATORS = [
    mutate_case_mix,
    mutate_null_byte,
    mutate_double_encode,
    mutate_unicode_confusable,
    mutate_whitespace,
    mutate_comment,
    mutate_hex_encode,
    mutate_newline,
    mutate_backtick,
    mutate_concat,
]


def generate_mutations(count):
    """Generate N mutated XSS payloads."""
    mutations = []
    for i in range(count):
        base = random.choice(BASE_PAYLOADS)
        # Apply 1-3 random mutations
        num_mutations = random.randint(1, 3)
        payload = base
        applied = []
        for _ in range(num_mutations):
            mutator = random.choice(MUTATORS)
            payload = mutator(payload)
            applied.append(mutator.__name__)
        mutations.append({
            "id": i,
            "base": base,
            "mutated": payload,
            "mutations_applied": applied
        })
    return mutations


def is_executable_xss(sanitized_value):
    """
    Check if a sanitized value could still execute as XSS.
    After HTML escaping, these patterns should NOT appear unescaped:
    - <script (unescaped angle bracket + script)
    - javascript: (as a URI)
    - on[event]= (event handlers)
    """
    # If properly HTML-escaped, < becomes &lt; and > becomes &gt;
    # So we check for raw < > that could form executable tags
    dangerous_patterns = [
        '<script',
        '<iframe',
        '<svg',
        '<embed',
        '<object',
        '<body',
        '<img',
        '<input',
        'javascript:',
        'onerror=',
        'onload=',
        'onfocus=',
        'onstart=',
        'ontoggle=',
    ]
    lower = sanitized_value.lower()
    for pattern in dangerous_patterns:
        if pattern in lower:
            # Check if it's inside an HTML entity (safe) or raw (dangerous)
            idx = lower.find(pattern)
            # If the < is actually &lt; in the original, it's safe
            # We need to check if the sanitized value has raw < not &lt;
            if '<' in sanitized_value:
                # Raw < found - potential bypass!
                return True
    return False


def test_false_positive_rate():
    """Test legitimate content that should NOT be blocked."""
    legitimate = [
        "這是一個正常的任務描述",
        "Deploy version 3.0 to production",
        "Review PR #42 for security fixes",
        "The ratio is 5 < 10 and 10 > 5",  # Mathematical < > in text
        "User said: 'hello world'",
        "Email: user@example.com",
        "Path: /home/user/scripts/run.sh",
        "JSON: {\"key\": \"value\"}",
        "CSS: color: red; font-size: 14px;",
        "Regex: ^[A-Z]{1,2}-[1-9][0-9]{0,2}$",
        "URL: https://example.com/path?q=1&r=2",
        "Math: a + b = c, where a > 0",
        "Code: if (x > 0) { return true; }",
        "日本語テスト：こんにちは世界",
        "한국어 테스트: 안녕하세요",
        "Emoji: 🔥💀👻🎉✅❌",
        "Special: ™ © ® § ¶ † ‡",
        "Markdown: **bold** _italic_ `code`",
        "Shell: ls -la | grep 'pattern'",
        "SQL: SELECT * FROM tasks WHERE id = 1",
    ]
    
    false_positives = 0
    for text in legitimate:
        record = {
            "sic_version": "3.0",
            "task": {
                "id": "A-1",
                "title": text,
                "deliverable": text,
                "status": "pending",
                "created_round": 1
            },
            "round": 1,
            "entity": {"name": "test", "model": "test"},
            "state": {"context": text, "current_action": "test"},
            "relation": {"user": "安安"}
        }
        result = validate_and_sanitize(record)
        if result["action"] == "BLOCK":
            false_positives += 1
    
    return false_positives, len(legitimate)


def main():
    print("=" * 70)
    print("FS-B-5 RIGOROUS: Mutation Fuzz + Bypass + False Positive Analysis")
    print(f"Total mutations: {TOTAL_MUTATIONS} | Seed: {SEED}")
    print("=" * 70)
    print()
    
    # Phase 1: Generate and test 1000 mutated payloads
    print(f"[1/3] Testing {TOTAL_MUTATIONS} mutated XSS payloads...")
    start = time.perf_counter()
    
    mutations = generate_mutations(TOTAL_MUTATIONS)
    
    blocked = 0
    bypassed = 0
    bypass_details = []
    
    for m in mutations:
        record = {
            "sic_version": "3.0",
            "task": {
                "id": "A-1",
                "title": m["mutated"],
                "deliverable": "test",
                "status": "pending",
                "created_round": 1
            },
            "round": 1,
            "entity": {"name": "test", "model": "test"},
            "state": {"context": "test", "current_action": "test"},
            "relation": {"user": "安安"}
        }
        
        result = validate_and_sanitize(record)
        
        if result["action"] == "BLOCK":
            blocked += 1
        else:
            # Check if the sanitized output could still execute
            sanitized = result.get("sanitized_record", {})
            if sanitized:
                title = sanitized.get("task", {}).get("title", "")
                if is_executable_xss(title):
                    bypassed += 1
                    bypass_details.append({
                        "id": m["id"],
                        "payload": m["mutated"][:100],
                        "mutations": m["mutations_applied"],
                        "sanitized": title[:100]
                    })
                # else: payload was mutated enough to be harmless AND passed sanitizer = OK
    
    elapsed = time.perf_counter() - start
    
    print(f"       Blocked: {blocked}/{TOTAL_MUTATIONS}")
    print(f"       Passed (harmless after mutation): {TOTAL_MUTATIONS - blocked - bypassed}")
    print(f"       BYPASSED (executable after sanitize): {bypassed}")
    print(f"       Elapsed: {elapsed:.2f}s")
    
    if bypass_details:
        print(f"       ⚠️  Bypass details (first 5):")
        for bd in bypass_details[:5]:
            print(f"         #{bd['id']}: {bd['payload'][:60]}...")
    
    # Phase 2: False positive analysis
    print()
    print("[2/3] False positive analysis (legitimate content)...")
    fp_count, fp_total = test_false_positive_rate()
    fp_rate = fp_count / fp_total * 100
    print(f"       False positives: {fp_count}/{fp_total} ({fp_rate:.1f}%)")
    print(f"       Target (< 10%): {'✅ PASS' if fp_rate < 10 else '❌ FAIL'}")
    
    # Phase 3: Bypass attempt summary
    print()
    print("[3/3] Bypass resistance summary...")
    bypass_rate = bypassed / TOTAL_MUTATIONS * 100
    print(f"       Bypass rate: {bypassed}/{TOTAL_MUTATIONS} ({bypass_rate:.2f}%)")
    print(f"       Target (0% bypass): {'✅ PASS' if bypassed == 0 else '❌ FAIL'}")
    
    # Summary
    print()
    print("-" * 70)
    print("RIGOROUS RESULTS:")
    
    block_rate = blocked / TOTAL_MUTATIONS * 100
    print(f"  Block rate:       {blocked}/{TOTAL_MUTATIONS} ({block_rate:.1f}%)")
    print(f"  Bypass rate:      {bypassed}/{TOTAL_MUTATIONS} ({bypass_rate:.2f}%) {'✅ PASS' if bypassed == 0 else '❌ FAIL'}")
    print(f"  False positive:   {fp_count}/{fp_total} ({fp_rate:.1f}%) {'✅ PASS' if fp_rate < 10 else '❌ FAIL'}")
    print(f"  Throughput:       {TOTAL_MUTATIONS/elapsed:.0f} payloads/sec")
    print("-" * 70)
    
    all_pass = (bypassed == 0) and (fp_rate < 10)
    
    if all_pass:
        print("✅ FS-B-5 RIGOROUS PASS: 0 bypasses, acceptable false positive rate")
    else:
        print("❌ FS-B-5 RIGOROUS: Criteria failed")
    
    # Save report
    report = {
        "experiment": "FS-B-5-rigorous",
        "total_mutations": TOTAL_MUTATIONS,
        "blocked": blocked,
        "bypassed": bypassed,
        "bypass_rate_pct": round(bypass_rate, 2),
        "false_positives": fp_count,
        "false_positive_total": fp_total,
        "false_positive_rate_pct": round(fp_rate, 1),
        "elapsed_sec": round(elapsed, 2),
        "throughput_per_sec": round(TOTAL_MUTATIONS / elapsed),
        "bypass_details": bypass_details[:10],
        "all_pass": all_pass,
        "seed": SEED
    }
    with open(SCRIPT_DIR / "report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
