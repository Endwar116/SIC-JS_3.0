# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.0.x   | Yes       |
| 2.0.x   | Security fixes only |
| < 2.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in SIC-JS, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please contact the maintainers directly via the repository's security advisory feature or email.

### What to include in your report

1. A description of the vulnerability
2. Steps to reproduce
3. The SIC-JS record (JSON) that triggers the vulnerability
4. Potential impact assessment
5. Suggested fix (if any)

### Response timeline

We aim to respond within 48 hours of receiving a security report. Critical vulnerabilities (especially XSS bypass in the sanitizer) will be prioritized.

## Security Architecture

SIC-JS v3.0 implements a defense-in-depth security model:

1. **Input Validation** — All records are validated against the JSON Schema before processing
2. **Sanitization** — The `sic_sanitizer.py` module strips all potentially dangerous content
3. **Shadow DOM Isolation** — Web Components use Closed Shadow DOM to prevent CSS/JS leakage
4. **Unidirectional Flow** — Data flows from SIC-JS record → DOM only, never DOM → record
5. **Terminal State Protection** — Completed/dismissed tasks cannot be modified (state machine enforcement)

## Known Limitations

- The Python `http.server` implementation is single-threaded and should not be used in production
- The sanitizer is designed for SIC-JS record content only; it does not sanitize arbitrary HTML
- SQLite persistence is suitable for single-node deployments; distributed systems require additional coordination
