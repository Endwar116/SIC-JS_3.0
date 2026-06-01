# Contributing to SIC-JS

Thank you for your interest in contributing to SIC-JS. This document outlines the guidelines for contributing to this project.

## Ground Rules

### Frozen Constraints

The following are `[FROZEN]` and **must not be modified** without explicit authorization from the protocol architects:

1. `task.id` format: `^[A-Z]{1,2}-[1-9][0-9]{0,2}$` (with optional prefix)
2. `task.status` enum: `{pending, in_progress, completed, dismissed, archived}`
3. `task.created_round` immutability: once set, never changes
4. `completed` three-condition requirement: deliverable + evidence + bilateral confirmation

If you believe a frozen constraint needs modification, open an issue with the `[FROZEN-CHANGE-REQUEST]` label and provide detailed justification.

### Schema Changes

The canonical schema is `packages/core/schema/sic-js-schema-v3.0.json`. Any proposed changes must:

1. Pass all existing 8 validator test cases
2. Pass all 9 ledger test cases
3. Not break backward compatibility with v2.0 records
4. Include new test fixtures demonstrating the change

## Development Workflow

### Setup

```bash
git clone https://github.com/Endwar116/SIC-JS_3.0.git
cd SIC-JS_3.0
pip install -r requirements.txt
bash integration_test.sh  # Ensure baseline passes
```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run `bash integration_test.sh` — all tests must pass
4. Commit with a descriptive message
5. Open a Pull Request

### Commit Message Format

```
[module] Brief description

- Detailed change 1
- Detailed change 2

Ref: FS-B-X (if related to an experiment)
```

### Test Requirements

Every new feature must include:
- At least one positive test case (expected PASS)
- At least one negative test case (expected FAIL)
- Performance measurement if the change affects the rendering pipeline

## Code Style

- Python: Follow PEP 8, use type hints
- JavaScript: Vanilla ES6+, no build tools required
- Documentation: Markdown, bilingual (English + Traditional Chinese) where applicable

## Reporting Issues

When reporting issues, please include:
- SIC-JS version (`sic_version` field value)
- The full JSON record that caused the issue
- Expected vs. actual behavior
- Environment (OS, Python version, browser if applicable)

## Security

If you discover a security vulnerability (especially XSS bypass), please do NOT open a public issue. Instead, contact the maintainers directly.
