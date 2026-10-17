# Contributing

Thank you for wanting to contribute to AISecurityTest! There is one thing you need to understand to contribute: writing test cases in YAML.

The case library is organized as **one directory per category, one `cases.yaml` per directory**. There are 8 categories today:

```
src/aisecurity/data/cases/
├── direct/cases.yaml
├── indirect/cases.yaml
├── encoded/cases.yaml
├── role_confusion/cases.yaml
├── tool_misuse/cases.yaml
├── data_exfiltration/cases.yaml
├── multi_language/cases.yaml
└── format_manipulation/cases.yaml
```

## Three Ways to Contribute

### 1. Add a Test Case (Easiest - Recommended for First-Time Contributors)

**You do NOT create a new file or a new directory for this.** You edit the `cases.yaml` of the directory that best matches your attack surface.

Workflow:

Step 1. Get the next available case ID:

    aisec next-id

Step 2. Pick a directory. See "Which directory?" below. If unsure, pick the closest one; the reviewer will move it if needed.

Step 3. Open `src/aisecurity/data/cases/<directory>/cases.yaml` and add a new entry under `cases:`. Copy the field layout from an existing case in the same file.

Step 4. Run `aisec validate` locally. You are good once you see "All cases validated".

Step 5. Submit a PR.

Case ID Rules:

- Format: `PI-XXX`, globally unique
- Always use the next available ID - run `aisec next-id`
- Do NOT reserve ranges or skip numbers
- Do NOT reuse IDs from existing cases

Risk Level: must be one of `严重` / `高` / `中-高` / `中` / `低`.

#### Required field layout

Every case uses the same field order so contributors always see the same shape:

```yaml
  PI-XXX:
    id: "PI-XXX"
    sub: "second-level category"
    sub3: "third-level category"
    pre: "preconditions"
    steps:
      - "human-readable step 1"
      - "human-readable step 2"
    payloads:
      - "the actual attack text sent to the model"
    expect: "what a correctly defended model should do"
    level: "高"
    defense: "actionable defense"
    owasp: "LLM01"
    note: "additional notes"
    source: "citation, or internal"
    manual_only: false
```

| Field | Meaning |
|---|---|
| `id` | `PI-XXX`, global unique |
| `sub` / `sub3` | second/third-level category |
| `pre` | preconditions |
| `steps` | **human-readable steps**, kept for readers. Not sent to the model |
| `payloads` | **the real payloads**, sent to the model verbatim. If the step heuristic misjudges your `steps`, you MUST use this field |
| `expect` | what a correctly defended model should do |
| `level` | `严重` / `高` / `中-高` / `中` / `低` |
| `defense` | actionable defense |
| `owasp` | OWASP LLM ID |
| `note` | additional notes |
| `source` | citation, or `internal` |
| `manual_only` | `true` if the case needs a human (file upload, browser, RAG); `false` if a plain API call can run it |

#### `steps` vs `payloads`

- `steps` is for humans. Write as much detail as you like.
- `payloads` is for the runner. Put **only** the real attack text here.
- If your `steps` contain lines that look like payloads but also contain human-readable prefixes (e.g. `场景1（...）：<im_start>...`), put the clean payload in `payloads` so the runner does not send the prefix.
- If a case is `manual_only: true`, `payloads` may be empty.

### 2. Add a New Category (Needs Discussion First)

**Default answer: no.** The 8 categories are stable. Creating a new directory requires an Issue first.

Only propose a new category when ALL of these hold:

1. None of the existing 8 directories can hold your case
2. The attack surface is backed by public research (paper, CVE, report)
3. You plan to contribute at least 5 cases, not one

Process:

1. Open an Issue titled `[New category] <attack surface name>`
2. Include: description, why the 8 existing directories are insufficient, citation, planned number of cases
3. Wait for a maintainer. If approved, the maintainer creates the directory and an empty `cases.yaml`, then you add your cases
4. PRs that create a new directory without a prior approved Issue will be closed

### 3. Add a Target Adapter (Requires Python)

See `src/aisecurity/targets/openai_compat.py` and implement the `send()` method of the `Target` abstract class.

---

## Which directory?

```
What does your case test?
├─ Directly ask the model to ignore/override instructions  -> direct/
├─ Injection via documents, web pages, emails, tool output -> indirect/
├─ Encoding: Base64, zero-width, Leetspeak, Unicode Tags   -> encoded/
├─ Roleplay, jailbreak persona, role confusion             -> role_confusion/
├─ Tool misuse, Agent overreach, MCP                       -> tool_misuse/
├─ Leak system prompt, history, or context                 -> data_exfiltration/
├─ Non-English or low-resource language bypass             -> multi_language/
├─ Markdown, HTML, Unicode, SVG rendering tricks           -> format_manipulation/
└─ Unsure                                                  -> see _template.yaml
```

---

## Hard Rules

- Do NOT include malicious code, real PII, or real secrets
- Do NOT include human-readable operation steps in `payloads`
- Do NOT duplicate existing case IDs
- Do NOT create a new directory without a prior approved Issue
- Every `defense` must be practically actionable
- Cite sources when referencing external material

## Pre-PR Checklist

Run:

    aisec validate

Expected output:

    Loaded 8 categories, N cases:
    ...
    All cases validated.

## Local Development

    git clone https://github.com/milantgh/AISecurityTest.git
    cd AISecurityTest
    pip install -e ".[dev]"
    aisec list
    aisec validate
    python -m pytest tests/ -v

## Code Style

Python code follows `ruff`, line length 100:

    pip install ruff
    ruff check src/

## Reporting Issues

Use GitHub Issues for bugs and feature requests.
For security vulnerabilities, do NOT open a public issue - see `SECURITY.md`.
