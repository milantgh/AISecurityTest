# AISecurityTest

> A lightweight, local-first **AI red-team payload toolkit** for OWASP LLM Top10 (2025),
> with a pluggable infrastructure vulnerability scanner.

AISecurityTest helps security researchers and developers generate, transform, and validate
adversarial payloads against LLM applications, RAG systems, and AI agents — **without
Docker, without a server, without a database.**

[Chinese](README_ZH.md) · [Architecture](docs/architecture.md) · [Testing](docs/testing.md) · [Contributing](CONTRIBUTING.md)

---

## What it does

- **57 curated test cases** covering OWASP LLM01–LLM10 (2025)
- **YAML-driven case library** — add new cases without writing Python
- **18 CLI commands** — browse, generate, transform, rewrite, run, export, scan
- **Text transform toolbox** — zero-width, Base64, hex, homoglyph, ChatML/Llama markers
- **Three-layer payload composer** — carrier × tactic × payload
- **Marker-based verification** — `<<AIST_OK>>` proves whether a payload survived rewriting
- **Pluggable targets** — OpenAI-compatible APIs
- **Built-in evaluators** — marker detection & regex-based PII detection
- **Vulnerability scanner** (`vuln`) — fingerprint + version + CVE matching, passive-first
- **Report export** — Markdown / JSON / Word / Excel / HTML
- **Defensive loading** — one broken YAML file never breaks the whole library
- **Contributor-friendly CLI** — `aisec categories`, `aisec next-id`, `aisec check-name`

---

## Quick start

### Install

```bash
pip install aisecurity-test
```

### Browse cases

```bash
aisec list                  # list all categories and cases
aisec categories            # list category names only
aisec show PI-001           # show one case in detail
aisec validate              # validate all cases
```

### Generate & run

```bash
aisec gen PI-001            # generate payloads for a case
aisec transform "hello" -m base64
aisec rewrite "your text"   # AI rewrite (requires API key)
aisec run PI-001 --target openai --api-key sk-xxx
```

### Vulnerability scan

```bash
aisec vuln list                               # list fingerprints & CVE rules
aisec vuln scan --target http://localhost:11434
aisec vuln scan --target http://localhost:11434 --active
aisec vuln scan --target http://localhost:11434 --format json -o result.json
```

### Export

```bash
aisec export --format markdown -o cases.md
aisec export --format html -o cases.html
aisec export --format docx -o cases.docx
aisec export --format xlsx -o cases.xlsx
```

---

## Vulnerability scanner (`vuln`)

The `vuln` command scans AI infrastructure components for known CVEs using a
**fingerprint → version check → CVE matching** flow.

- **Passive by default** — only version comparison, no attack payloads
- **Active mode** (`--active`) — sends confirmation requests for `mode: request` rules
- **YAML-driven rules** — add fingerprints and CVEs without writing Python
- **External rules** — set `AISecurityTest_RULES_PATH` to load community rules

Built-in fingerprints: Ollama, vLLM, ComfyUI.
Built-in CVE: CVE-2024-37032 (Ollama <0.1.34 path traversal RCE).

Exit code: `0` = no vulnerabilities, `2` = CRITICAL found — ready for CI/CD.

---

## Project layout

```
src/aisecurity/
├── cli/                  # 18 CLI commands
├── engine/               # payload generation & transformation
├── targets/              # target adapters (OpenAI-compatible)
├── evaluators/           # marker + regex evaluators
├── runner/               # end-to-end orchestration
├── vulnscan/             # fingerprint + CVE scan engine
├── recon/                # endpoint reconnaissance
├── probes/               # probe framework
└── data/
    ├── cases/            # 57 YAML test cases
    ├── fingerprints/     # component fingerprints
    ├── vuln/             # CVE rules
    ├── datasets/         # test datasets
    └── probes/           # probe definitions
```

---

## Development

```bash
git clone https://github.com/milantgh/AISecurityTest.git
cd AISecurityTest
pip install -e ".[dev]"
aisec list
aisec validate
python -m pytest tests/ -v
```

## Documentation

- `README.md` / `README_ZH.md` — bilingual
- `CONTRIBUTING.md` / `CONTRIBUTING_ZH.md` — bilingual
- `SECURITY.md` / `SECURITY_ZH.md` — bilingual
- `CHANGELOG.md` / `CHANGELOG_ZH.md` — bilingual

## License

MIT
