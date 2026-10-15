# Security Policy

## Project Scope

AISecurityTest is a **red-team testing toolkit** for **authorized** AI security testing.

All test cases, payload samples, and MCP malicious manifest templates in this project
are provided **for educational purposes and authorized testing only**.
Do not use for unauthorized attacks.

## Reporting a Vulnerability

If you discover a security vulnerability in **AISecurityTest itself**
(e.g., malicious YAML causing code execution, dependency vulnerabilities,
path traversal, arbitrary file write), **do NOT open a public GitHub Issue**.

Please report privately via **either** of these channels:

1. **GitHub Private Vulnerability Reporting** (preferred):
   Go to the "Security" tab of this repository, click "Report a vulnerability".

2. **Email**: `617707073@qq.com`
   Subject: `[SECURITY] AISecurityTest Vulnerability Report`
   Content: Description + reproduction steps + impact + suggested fix (if any)

We will:

- **Acknowledge** your report within **72 hours**
- **Assess** and provide an initial response within **7 days**
- **Release a fix** within **30 days** for confirmed vulnerabilities
  (depending on severity)
- **Credit** you in `CHANGELOG.md` after the fix is released
  (let us know if you prefer to remain anonymous)

## Supported Versions

| Version | Status |
|---|---|
| 1.0.x | ✅ Security updates |
| < 1.0 | ❌ No longer supported |

## Usage Notice

When using this project, you must confirm:

1. You have **written authorization** for the target system
2. Your testing scope **stays within the authorized boundary**
3. Your testing activity **complies with local laws and regulations**
4. You use **sanitized or test data** — never test production systems
   with real customer data

The project authors are not responsible for any misuse.

## About Case Files

- All test cases use **fictional** bank/customer data
- No real PII, real secrets, or real exploit code
- If you find a case containing real sensitive information, report it
  immediately via one of the channels above

## Dependency Security

The core dependency of this project is `PyYAML` only.

Optional dependencies (`pillow` / `python-docx` / `openpyxl` /
`reportlab` / `deep-translator`) are installed only when the
corresponding features are needed.

We recommend:

- Periodically run `pip install -U` to upgrade dependencies
- Use `pip-audit` or `safety` to check for dependency vulnerabilities
- Use virtual environments to isolate production deployments

## Acknowledgements

Thanks to all researchers who report security issues responsibly.