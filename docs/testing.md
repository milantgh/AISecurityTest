# Testing Guide

This document explains the testing system of this project:
`tests/` directory structure, pytest working principle, common commands,
and how to add new tests.

---

## 1. What is pytest

pytest is Python's testing framework. Its purpose:

```
You write code  →  Code may break  →  pytest detects it automatically
```

**Without pytest**:

- You change one line and don't know if it affects other parts
- You have to manually open the app and click through every feature

**With pytest**:

- You change code, run one command
- In 3 seconds it tells you: "32 checks passed" or "Check #7 failed"

---

## 2. tests/ Directory Structure

The `tests/` directory looks like this — each file's purpose is clear at a glance:

```
tests/
├── __init__.py                      makes tests a Python package (empty file)
├── conftest.py                      pytest global config
│                                    · adds src/ to sys.path
│                                    · allows running tests without installing
├── test_registry.py                 tests "case library loading"
│                                    · can all categories and cases load?
│                                    · are case IDs unique? are fields complete?
├── test_marker.py                   tests "marker mechanism"
│                                    · can <<AIST_OK>> be recognized?
│                                    · case variations, empty string edge cases
├── test_transforms.py               tests "text transform functions"
│                                    · is Base64 reversible?
│                                    · are zero-width characters really inserted?
├── test_evaluators.py               tests "evaluators"
│                                    · marker hit/miss decisions
│                                    · regex catches phone numbers, ID cards, API keys
└── test_runner_integration.py       tests "end-to-end pipeline"
                                     · generate → send → evaluate → decide
                                     · uses fake Target, no network
```

### Responsibility of Each File

| File | What it tests | Corresponding source |
|---|---|---|
| `test_registry.py` | case loading, validation, deduplication | `src/aisecurity/core/registry.py` |
| `test_marker.py` | `<<AIST_OK>>` recognition | `src/aisecurity/core/marker.py` |
| `test_transforms.py` | correctness of text transforms | `src/aisecurity/engine/transforms.py` |
| `test_evaluators.py` | marker / regex evaluator decisions | `src/aisecurity/evaluators/` |
| `test_runner_integration.py` | end-to-end pipeline | `src/aisecurity/runner/` |

### Why Each Module Has Its Own Test File

- **Easy lookup**: if a module breaks, you know exactly which test file to check
- **Onboarding**: the fastest way to learn how a module works is to read its test file
- **PR review**: contributors modifying module A run `test_A.py`, not the full suite

---

## 3. How pytest Works

### 3.1 Full Pipeline

When you run `python -m pytest tests/ -v`, pytest does this:

```
① Discovery
   └─ Scan directory, find all test_*.py files

② Collection
   └─ In each file, find all test_* functions

③ Execution
   └─ Call each function, run its asserts
      (assert passes → PASS; fails → FAIL)

④ Reporting
   └─ Summarize: how many passed, how many failed, elapsed time
```

### 3.2 A Simple Example

```python
# tests/test_example.py

def test_addition():
    assert 1 + 1 == 2          # passes

def test_base64_roundtrip():
    src = "hello world"
    enc = to_b64(src)
    dec = base64.b64decode(enc).decode("utf-8")
    assert dec == src          # passes

def test_will_fail():
    assert 1 + 1 == 3          # fails
```

After running `pytest`:

```
tests/test_example.py::test_addition PASSED
tests/test_example.py::test_base64_roundtrip PASSED
tests/test_example.py::test_will_fail FAILED
```

### 3.3 The Core Mechanism: assert

`assert` is pytest's soul. It does one thing: **check if a condition is true**.

```python
assert condition              # true → PASS
assert condition, "message"   # false → FAIL, prints the message
```

**Real example** (from `tests/test_marker.py`):

```python
def test_exact_marker():
    ok, found = check_payload_kept("prefix <<AIST_OK>> suffix")
    assert ok
    assert found == "<<AIST_OK>>"
```

If you break `check_payload_kept()` (e.g., mess up case sensitivity),
this test fails immediately:

```
FAILED tests/test_marker.py::test_exact_marker
AssertionError: assert False
```

**You know where the problem is within 5 seconds.**

### 3.4 Naming Conventions

pytest discovers tests via file and function name prefixes:

**Files**:
- ✅ `test_registry.py`
- ❌ `registry_test.py` (will not be discovered)

**Functions**:
- ✅ `def test_exact_marker():`
- ❌ `def check_exact_marker():` (will not be called)

---

## 4. Common Commands

### 4.1 Run all tests

```bash
python -m pytest tests/ -v
```

**Expected**: all tests pass (currently 32 tests)

### 4.2 Run a single file

```bash
python -m pytest tests/test_transforms.py -v
```

### 4.3 Run a single function

```bash
python -m pytest tests/test_transforms.py::test_base64_roundtrip -v
```

### 4.4 Stop on first failure

```bash
python -m pytest tests/ -x
```

### 4.5 Show per-test duration

```bash
python -m pytest tests/ --durations=10
```

### 4.6 Only run tests whose name contains a keyword

```bash
python -m pytest tests/ -k marker -v
```

### 4.7 Check test coverage

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src/aisecurity --cov-report=term-missing
```

**Example output**:

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
aisecurity/core/registry.py         80      5    94%
aisecurity/engine/transforms.py     40      2    95%
aisecurity/runner/runner.py         30      3    90%
```

**Higher Cover = more complete tests.** Open source projects aim for 70%+;
excellent projects target 90%+.

---

## 5. How to Add a New Test

Suppose you add a new feature: `src/aisecurity/engine/new_feature.py`.

### Step 1: Create the test file

```
tests/test_new_feature.py
```

### Step 2: Write the test

```python
# -*- coding: utf-8 -*-
"""Tests for the new_feature module."""
from aisecurity.engine.new_feature import my_function


def test_basic_case():
    """Basic functionality."""
    result = my_function("input")
    assert result == "expected"


def test_edge_case():
    """Edge case."""
    result = my_function("")
    assert result == ""


def test_error_case():
    """Error handling."""
    import pytest
    with pytest.raises(ValueError):
        my_function(None)
```

### Step 3: Run the test

```bash
python -m pytest tests/test_new_feature.py -v
```

### Step 4: Commit together

```bash
git add src/aisecurity/engine/new_feature.py tests/test_new_feature.py
git commit -m "feat: add new_feature with tests"
```

**Convention**: **new feature + new test, committed together.**

---

## 6. Testing and CI

The project has `.github/workflows/validate.yaml`:

```yaml
- name: Run tests
  run: |
    pip install pytest
    python -m pytest tests/ -v
```

On every push / PR:

1. GitHub pulls the code
2. Runs `pytest` automatically
3. Runs `aisec validate` automatically
4. Decides whether to allow the merge

**Result**:

- Green ✅ → merge allowed
- Red ❌ → blocked, tells you what's broken

**This is why "popular open source projects" all have tests and CI.**

---

## 7. Good Habits

### 7.1 After changing code → run pytest immediately

```bash
python -m pytest tests/ -q
```

`-q` is quiet mode, only shows the result.

**You know within 3 seconds whether you broke anything.**

### 7.2 Run the full test suite before committing

```bash
python -m pytest tests/ -v
```

**Green before you commit.**

### 7.3 New feature → new test

**Convention**: new feature file + new test file → committed together.

### 7.4 Watch coverage trends

If you add hundreds of lines of code without tests, coverage drops.
**Check coverage periodically; add tests when it drops.**

---

## 8. FAQ

### Q1: Tests are slow — what to do?

```bash
python -m pytest tests/ --durations=10     # find slow tests
pip install pytest-xdist                   # install parallel plugin
python -m pytest tests/ -n auto            # run in parallel
```

### Q2: "ModuleNotFoundError" when running tests

Check:

1. You're in the project root (not inside `tests/`)
2. `tests/conftest.py` exists (adds `src/` to the path)
3. You use `python -m pytest`, not `pytest`

### Q3: Tests can't reach external services

**Tests should never depend on external services.** Use fakes:

```python
class FakeTarget(Target):
    def send(self, payload, **kwargs):
        return TargetResponse(text="fixed response")
```

**All tests in this project run offline.**

### Q4: pytest can't find tests

- File name must be `test_*.py` or `*_test.py`
- Function name must start with `test_`
- If in a subdirectory, ensure it has `__init__.py`

---

## 9. One-Sentence Summary

> **pytest is your project's "automatic QA inspector".**
>
> It lets you change code freely, accept PRs freely, and come back
> six months later without fear.
>
> Projects without tests become unmaintainable in six months.
> Projects with tests only get bigger.

---

## 10. Related Files

| File | Purpose |
|---|---|
| `pyproject.toml` | configures pytest's `testpaths` and `pythonpath` |
| `tests/conftest.py` | adds `src/` to `sys.path` |
| `.github/workflows/validate.yaml` | CI auto-runs tests |
| `src/aisecurity/core/registry.py` | case registry (tested object) |

---

## 11. Further Reading

- [pytest official docs](https://docs.pytest.org/)
- [pytest-cov plugin](https://pytest-cov.readthedocs.io/)
- [Test-Driven Development (TDD)](https://en.wikipedia.org/wiki/Test-driven_development)