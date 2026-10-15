# Contributing

Thank you for wanting to contribute to AISecurityTest! There's only one thing
you need to understand to contribute: writing test cases in YAML files.

## Three Ways to Contribute

### 1. Add a Test Case (Easiest — Recommended for First-Time Contributors)

Workflow:

Step 1. Check existing category names (avoid duplicates):

    aisec categories

Step 2. Get the next available ID:

    aisec next-id

Step 3. Check your category name is unique:

    aisec check-name "My New Category"

Step 4. Look at `src/aisecurity/data/cases/_template.yaml`

Step 5. Find the matching category file (e.g., `direct_injection.yaml`)

Step 6. Add a new case under `cases:`, copying the fields from the template

Step 7. Run `aisec validate` locally — you're good once you see
        "✅ All cases validated"

Step 8. Submit a PR

Case ID Rules:

- Format: `PI-XXX`, globally unique
- Always use the next available ID — run `aisec next-id` to check
- Do NOT reserve ranges or skip numbers
- Do NOT reuse IDs from existing cases

Risk Level: Must be one of `严重` / `高` / `中-高` / `中` / `低`
(Critical / High / Medium-High / Medium / Low)

### 2. Add a New Category

1. Run `aisec categories` to see existing category names
2. Run `aisec next-id` to get the next available ID
3. Run `aisec check-name "Your Name"` to confirm no conflict
4. Copy `src/aisecurity/data/cases/_template.yaml` to `your_category_name.yaml`
5. Fill in the `meta` section (`name` must be globally unique,
   `order` controls the sidebar order)
6. Add cases under `cases:`, using the ID from step 2
7. Submit a PR once `aisec validate` passes

### 3. Add a Target Adapter (Requires Python)

See `src/aisecurity/targets/openai_compat.py` and implement the `send()`
method of the `Target` abstract class.

---

## Naming Convention

Both the file name and the category name use the same suffix.

| Suffix | Scenario | File name | Category name |
|---|---|---|---|
| (none) | Chinese default | `direct_injection.yaml` | `直接提示注入` |
| `_en` | English | `direct_injection_en.yaml` | `直接提示注入 EN` |
| `_ja` | Japanese | `direct_injection_ja.yaml` | `直接提示注入 JA` |
| `_v2` | Content revision | `direct_injection_v2.yaml` | `直接提示注入 v2` |
| `_financial` | Financial industry | `direct_injection_financial.yaml` | `直接提示注入（金融）` |
| `_2025q4` | Time batch | `direct_injection_2025q4.yaml` | `直接提示注入 2025Q4` |

Why: files with the same prefix are grouped together in the directory
listing, and category names with the same prefix are grouped together
in the sidebar. Users immediately recognize that they belong to the
same logical category.

Category names must be globally unique. If two files use the same
`meta.name`, the second is rejected at load time. Example output:

    $ aisec validate
    ...
    ⚠ 发现问题：
      - [my_file.yaml] 分类名 '直接提示注入' 已被 direct_injection.yaml 占用，本文件跳过。
        请改一个唯一的分类名（如 '直接提示注入 EN' / '直接提示注入 v2' / '直接提示注入（金融）'）。
        跑 `aisec categories` 查看已有分类名。

Fix it by renaming your category.

---

## Hard Rules

- ❌ Do NOT include malicious code, real PII, or real secrets in case files
- ❌ Do NOT duplicate existing case IDs
- ❌ Do NOT duplicate existing category names
- ✅ The "defense" section of a case must be practically actionable
- ✅ Cite sources when referencing external material (OWASP / MITRE ATLAS / papers, etc.)

## Pre-PR Checklist

Run:

    aisec validate

Expected output:

    已加载 N 个类别，M 条用例。
    ...
    ✅ 全部用例校验通过。

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
For security vulnerabilities, do NOT open a public issue — see `SECURITY.md`.