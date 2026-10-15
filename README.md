# AISecurityTest

> A lightweight, local-first **AI red-team payload toolkit** for OWASP LLM Top10 (2025).

AISecurityTest helps security researchers and developers generate, transform, and validate
adversarial payloads against LLM applications, RAG systems, and AI agents — **without
Docker, without a server, without a database.**

[Chinese](README_ZH.md) · [Architecture](docs/architecture.md) · [Testing](docs/testing.md) · [Contributing](CONTRIBUTING.md)

---

## What it does

- **40 curated test cases** covering OWASP LLM01–LLM10 (2025)
- **YAML-driven case library** — add new cases without writing Python
- **13 CLI commands** — browse, generate, transform, rewrite, run, export
- **Text transform toolbox** — zero-width, Base64, hex, homoglyph, ChatML/Llama markers
- **Three-layer payload composer** — carrier × tactic × payload
- **Marker-based verification** — `<<AIST_OK>>` proves whether a payload survived rewriting
- **Pluggable targets** — OpenAI-compatible APIs
- **Built-in evaluators** — marker detection & regex-based PII detection
- **Report export** — Markdown / JSON / Word / Excel / HTML
- **Defensive loading** — one broken YAML file never breaks the whole library
- **Contributor-friendly CLI** — `aisec categories`, `aisec next-id`, `aisec check-name`

## Why not just use AI-Infra-Guard?

AISecurityTest is **not** a platform. It is a **payload toolkit**:

| | AISecurityTest | AI-Infra-Guard |
|---|---|---|
| Focus | Payload generation & transformation | Full-stack scanning platform |
| Deployment | `pip install` / local | Docker + Web UI |
| CVE scan | ✗ | ✓ (2000+ rules) |
| Case library | YAML, community-editable | Rule-based |
| Best for | Hands-on red team, prompt engineering | Enterprise scanning |

They complement each other.

---

## Quick start

### Install

```bash
pip install aisecurity-test