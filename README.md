# SIC-JS v3.0

**Semantic Integrity Control — JSON State Protocol**

An open protocol for AI agent semantic state persistence, verification, and cross-session continuity.

---

## What is SIC-JS?

SIC-JS (Semantic Integrity Control — JSON State) is a protocol that allows AI agents to maintain semantic integrity across sessions, models, and platforms. It defines a JSON-based state record format with six primitives that capture the complete cognitive state of an AI agent at any given moment.

### The Six Primitives

| Primitive | Layer | Purpose |
|-----------|-------|---------|
| `entity` | is | Who is speaking |
| `state` | is | What is happening now |
| `relation` | is | Who is being spoken to |
| `event` | was | What triggered this moment |
| `intent` | is | Why this action is being taken |
| `task` | ought | What must be delivered (v3.0) |

### Why?

When an AI agent's session ends, all context is lost. SIC-JS solves this by providing a structured, verifiable record that any subsequent agent (regardless of model or platform) can load to resume work with full semantic continuity.

## Quick Start

```bash
# Clone
git clone https://github.com/Endwar116/SIC-JS_3.0.git
cd SIC-JS_3.0

# Validate a record
pip install jsonschema>=4.22.0
python3 packages/core/validator/sic_validate.py packages/core/validator/fixtures/T2_v3_valid_task.json

# Run the full test suite
bash integration_test.sh
```

## Repository Structure

```
SIC-JS_3.0/
├── spec/                          ← Protocol specifications
│   ├── SICJS_30_技術原始記載檔.md    ← Authoritative protocol document
│   ├── SIC_JS_RENDERING_SPEC_v1.1.md ← Rendering specification (RC)
│   └── CHANGELOG.md
├── packages/
│   ├── core/
│   │   ├── schema/                ← JSON Schema (source of truth)
│   │   ├── validator/             ← CLI validator + 8 test fixtures
│   │   └── persistence/           ← SQLite task ledger
│   ├── server/                    ← NDJSON streaming server (asyncio)
│   └── developer-sdk/             ← Web Components + Sanitizer
├── experiments/                   ← Engineering validation data
│   ├── FS-B-{1..5}/             ← Happy-path experiments
│   └── rigorous/FS-B-{1..5}/   ← Adversarial/fuzz experiments
├── docs/                          ← Documentation
│   ├── quickstart.md
│   ├── schema-reference.md
│   └── commercial-numbers.md
├── examples/                      ← Runnable examples
│   ├── minimal/
│   ├── task-lifecycle/
│   └── streaming-dashboard/
├── integration_test.sh            ← One-command full test suite
├── requirements.txt               ← Python dependencies
├── CONTRIBUTING.md
└── LICENSE                        ← MIT
```

## Key Design Decisions

**Frozen Constraints** — Certain fields are marked `[FROZEN]` and cannot be changed in any future version of the protocol. This ensures backward compatibility and allows `task.id` to serve as a stable DOM key for O(1) rendering.

**Five-State Machine** — Task status is restricted to exactly five values: `{pending, in_progress, completed, dismissed, archived}`. `completed` and `dismissed` are terminal states requiring bilateral confirmation.

**Backward Compatibility** — A valid v2.0 record (without `task`) remains valid under v3.0 validation. The protocol only adds, never removes.

## Performance Characteristics

| Metric | Value | Measurement |
|--------|-------|-------------|
| Schema validation overhead | 0.097ms P50 | FS-B-2 rigorous |
| XSS penetration rate | 0% (1,000 mutations) | FS-B-5 rigorous |
| Memory growth (10K cards) | 1.07x (linear) | FS-B-4 rigorous |
| Validator throughput | 220 records/sec | FS-B-1 fuzz |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)

## Authors

- **安安 (Anan)** — Protocol architect, Runtime Director
- **德德 (Dede)** — Technical review, Engineering validation
- **咩咩 (Manus)** — Implementation, Experimentation

---

> *"SIC-JS is not a tool. It is a protocol for semantic continuity in the age of multi-agent AI."*
