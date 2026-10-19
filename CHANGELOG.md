# Changelog

This project follows [Semantic Versioning](https://semver.org/).

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Planned

- Multi-modal sample generation (PNG / WAV / PDF / CSV)
- MCP malicious manifest templates + audit checklist
- Ollama / HTTP Webhook target adapters
- Tkinter GUI (lightweight, system-language aware)
- Web UI (FastAPI + Vue)
- Multi-language case library (i18n)

---

## [1.1.0] - 2025-10-20

### Added

- **Vulnerability scanner** (`vulnscan/` module + `aisec vuln` CLI)
  - Two-phase flow: fingerprinting → version check → CVE matching
  - Passive by default; `--active` enables confirmation requests
  - YAML-driven rules: `data/fingerprints/` + `data/vuln/`
  - External rules via `AISecurityTest_RULES_PATH`
  - Built-in fingerprints: Ollama, vLLM, ComfyUI
  - Built-in CVE: CVE-2024-37032 (Ollama <0.1.34 path traversal RCE)
  - Exit codes: 0 = clean, 2 = CRITICAL found (CI/CD ready)

- **Probe framework** (`probes/` module)
  - Pluggable security probes for LLM endpoints

- **Jailbreak dataset** (`jailbreak_dataset/`)
  - 400+ sampled prompts across 14 harm categories

### Changed

- CLI command count: 13 → 18
- Test cases: 40 → 57
- `pyproject.toml`: package-data includes `fingerprints/` and `vuln/`
- `reportlab>=3.6.13` upper bound removed for Python 3.12 compatibility

### Fixed

- Package data missing subdirectory YAML files

---

## [1.0.0] - 2025-10-11

First official release.

### Added

- **Case Library**: 40 curated cases covering OWASP LLM01–LLM10 (2025)
  - LLM01 Prompt Injection (direct / indirect / multimodal / agent chain /
    encoding obfuscation / gradual jailbreak)
  - LLM02 Sensitive Information Disclosure
  - LLM03 Supply Chain
  - LLM04 Data and Model Poisoning
  - LLM05 Improper Output Handling
  - LLM06 Excessive Agency
  - LLM07 System Prompt Leakage
  - LLM08 Vector and Embedding Weaknesses
  - LLM09 Misinformation
  - LLM10 Unbounded Consumption

- **YAML-driven case library**
  - 15 category files, one file per category
  - Community can contribute new cases at zero cost
  - Defensive loading: one broken file never breaks the whole library

- **Payload engine** (`engine/`)
  - Per-case payload generation
  - Three-layer composition: carrier × tactic × payload
  - Text transform toolbox: zero-width, Base64, Hex, Unicode escape,
    case mixing, homoglyph substitution, HTML comments, code blocks,
    ChatML/Llama marker injection
  - Low-resource language translation: Swahili, Icelandic, Hausa,
    Maori, Welsh
  - AI rewrite: OpenAI-compatible API / Ollama

- **Marker mechanism**
  - `<<AIST_OK>>` to verify whether payloads survive rewriting/transformation

- **Target adapters** (`targets/`)
  - `Target` abstract base class
  - `OpenAITarget`: OpenAI-compatible APIs

- **Evaluators** (`evaluators/`)
  - `MarkerEvaluator`: marker detection
  - `RegexEvaluator`: phone numbers, ID cards, emails, API keys,
    bank card numbers, and more

- **Runner** (`runner/`)
  - End-to-end orchestration: case × target × evaluator

- **CLI** (`cli/`) — **13 commands**
  - `aisec list` — list categories / cases
  - `aisec validate` — validate all cases
  - `aisec run` — run cases against a target
  - `aisec export` — export cases (markdown / json / html / docx / xlsx)
  - `aisec next-id` — show the next available case ID
  - `aisec categories` — list all category names (one per line)
  - `aisec check-name <name>` — check if a category name is taken
  - `aisec show [case_id]` — show case details (or list all IDs)
  - `aisec gen <case_id>` — generate payloads for a case
  - `aisec compose <payload>` — three-layer composition
  - `aisec transform <text> -m <method>` — text transform
  - `aisec rewrite <text>` — AI rewrite (requires API)
  - `aisec pipeline <case_id>` — one-shot pipeline: generate → transform → verify

- **Tests**
  - 32 tests, all passing
  - Unit tests + integration tests

- **CI**
  - GitHub Actions auto-validation (Python 3.8 / 3.10 / 3.12)

### Documentation

- `README.md` / `README_ZH.md` — bilingual
- `CONTRIBUTING.md` / `CONTRIBUTING_ZH.md` — bilingual
- `SECURITY.md` / `SECURITY_ZH.md` — bilingual
- `CHANGELOG.md` / `CHANGELOG_ZH.md` — bilingual
- `docs/architecture.md` / `docs/architecture_ZH.md` — bilingual
- `docs/testing.md` / `docs/testing_ZH.md` — bilingual

### Known Limitations

- Multi-modal sample generation not yet supported (CLI)
- MCP malicious manifest templates not yet supported (CLI)
- Ollama / HTTP Webhook targets not yet supported (run)
- No GUI yet

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Links

- [Repository](https://github.com/milantgh/AISecurityTest)
- [Issues](https://github.com/milantgh/AISecurityTest/issues)
- [Releases](https://github.com/milantgh/AISecurityTest/releases)