# Architecture

This document describes the internal structure of AISecurityTest.

## Layered Design

```
┌─────────────────────────────────────────────┐
│ cli/            ← command-line entry        │
├─────────────────────────────────────────────┤
│ runner/         ← orchestrator:             │
│                   case × target × eval      │
├─────────────────────────────────────────────┤
│ engine/ targets/ evaluators/                │
│                 ← capability layer,         │
│                   pure logic                │
├─────────────────────────────────────────────┤
│ core/ data/cases/  ← data layer,            │
│                      no side effects        │
└─────────────────────────────────────────────┘
```

**Rule**: arrows only point downward. `core/` and `engine/` never import `cli/`.

## Directory Layout

```
src/aisecurity/
├── __init__.py               public API & version
├── _version.py               version constants
│
├── core/                     data layer — no side effects
│   ├── __init__.py
│   ├── schema.py             case data structure & validation
│   ├── loader.py             YAML/module loading utilities
│   ├── registry.py           case registry (defensive loading)
│   ├── marker.py             <<AIST_OK>> marker mechanism
│   └── errors.py             unified exceptions
│
├── data/                     data files
│   └── cases/                15 YAML files, 40 cases
│       ├── _template.yaml    contribution template
│       ├── direct_injection.yaml
│       ├── indirect_injection.yaml
│       └── ...
│
├── engine/                   attack payload engine — pure functions
│   ├── __init__.py
│   ├── payload.py            per-case payload generation
│   ├── compose.py            three-layer composition
│   ├── transforms.py         text transform toolbox
│   ├── translate.py          low-resource language translation
│   └── rewrite.py            AI rewrite (OpenAI-compatible / Ollama)
│
├── targets/                  target adapters
│   ├── __init__.py
│   ├── base.py               Target abstract base class
│   └── openai_compat.py      OpenAI-compatible API adapter
│
├── evaluators/               attack-success evaluators
│   ├── __init__.py
│   ├── base.py               Evaluator abstract base class
│   ├── marker_eval.py        marker detection
│   └── regex_eval.py         regex-based PII detection
│
├── runner/                   orchestration
│   ├── __init__.py
│   ├── runner.py             case × target × evaluator
│   └── result.py             result object
│
└── cli/                      command-line interface — 13 commands
    ├── __init__.py
    ├── main.py               `aisec` entry point
    ├── cmd_list.py           aisec list
    ├── cmd_validate.py       aisec validate
    ├── cmd_run.py            aisec run
    ├── cmd_export.py         aisec export (md / json / html / docx / xlsx)
    ├── cmd_next_id.py        aisec next-id
    ├── cmd_categories.py     aisec categories
    ├── cmd_check_name.py     aisec check-name
    ├── cmd_show.py           aisec show
    ├── cmd_gen.py            aisec gen
    ├── cmd_compose.py        aisec compose
    ├── cmd_transform.py      aisec transform
    ├── cmd_rewrite.py        aisec rewrite
    └── cmd_pipeline.py       aisec pipeline
```

## Data Flow

```
YAML cases
   ↓ (core/registry: load + validate)
CASE_LIB
   ↓ (engine/payload: generate)
payloads: List[str]
   ↓ (targets/*: send)
responses: List[TargetResponse]
   ↓ (evaluators/*: judge)
EvalResults
   ↓ (cli/cmd_run or report/*)
output
```

## Extension Points

There are four extension points. Each maps to one type of contributor.

| Extension point | Directory / File | Audience |
|---|---|---|
| Add a case | `src/aisecurity/data/cases/*.yaml` | Security analysts |
| Add a target adapter | `src/aisecurity/targets/*.py` | Developers |
| Add an evaluator | `src/aisecurity/evaluators/*.py` | Security researchers |
| Add a text transform | `src/aisecurity/engine/transforms.py` | Red team engineers |

### Adding a Case (No Python Required)

1. Run `aisec categories` to see existing category names
2. Run `aisec next-id` to get the next available ID
3. Run `aisec check-name "Your Name"` to check for conflicts
4. Copy `data/cases/_template.yaml`
5. Find the matching category file (e.g., `direct_injection.yaml`)
6. Add a new case under `cases:` with the ID from step 2
7. Run `aisec validate` — you're good once you see "✅ All cases validated"
8. Submit a PR

### Adding a Target Adapter (Python Required)

1. Copy `targets/openai_compat.py`
2. Implement `send()` from the `Target` abstract base class
3. Register it in `cli/cmd_run.py` if you want it accessible via CLI

### Adding an Evaluator (Python Required)

1. Copy `evaluators/marker_eval.py`
2. Implement `evaluate(payload, response_text)` from the `Evaluator` base
3. Register it in `evaluators/__init__.py`'s `build_evaluators()`

## Case ID Naming

- Format: `PI-XXX`
- **Globally unique** — IDs are sequential, not per-category
- Run `aisec next-id` to get the next available ID
- Cross-file conflicts are rejected by the registry
- Current range: PI-001 ~ PI-040

## Category Naming

- **Globally unique** — duplicate `meta.name` is rejected at load time
- Use suffixes for variants: `_en`, `_ja`, `_v2`, `_financial`, ...
- File name and category name should share the same suffix
  (e.g., `direct_injection_en.yaml` ↔ `直接提示注入 EN`)

## Defensive Loading

The registry loads each YAML file independently:

- A syntax error / import error → that file is skipped, others still load
- A missing field → recorded in `LOAD_ERRORS`, visible via `aisec validate`
- Duplicate case ID / category name → kept the first, reported the conflict
- If more than half the cases in one file are broken → skip the whole file

**Result**: any broken file dropped into `data/cases/` will never prevent
the program from starting.

## CLI Commands (13 commands)

| Command | Purpose |
|---|---|
| `aisec list` | List categories and cases |
| `aisec validate` | Validate all cases (CI uses this) |
| `aisec run` | Run cases against a target |
| `aisec export` | Export cases (md / json / html / docx / xlsx) |
| `aisec next-id` | Show the next available case ID |
| `aisec categories` | List all category names (one per line) |
| `aisec check-name <name>` | Check if a category name is taken |
| `aisec show [case_id]` | Show case details (or list all IDs) |
| `aisec gen <case_id>` | Generate payloads for a case |
| `aisec compose <payload>` | Three-layer composition |
| `aisec transform <text> -m <method>` | Text transform |
| `aisec rewrite <text>` | AI rewrite (requires API) |
| `aisec pipeline <case_id>` | One-shot pipeline: generate → transform → verify |

## Why This Architecture

| Design choice | Reason |
|---|---|
| YAML-driven cases | Non-Python contributors can add cases |
| Defensive loading | One broken file never breaks the library |
| Layered modules | Pure logic separated from CLI, easy to test |
| CLI first | Scriptable, CI-friendly, testable |
| Pluggable targets | Add new LLM backends without touching core |
| Pluggable evaluators | Add new detection logic without touching runner |
| Marker mechanism | Attack success can be judged automatically |
| Globally sequential IDs | No conflict even across languages |

