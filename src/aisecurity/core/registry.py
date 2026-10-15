# -*- coding: utf-8 -*-
"""
Case registry (defensive loading).
Loads cases from YAML files:src/aisecurity/data/cases/*.yaml
A broken file never affects other files.
All issues are collected in LOAD_ERRORS and visible via `aisec validate`.
"""
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Tuple
from .loader import discover_yaml_files, load_yaml
from .schema import validate_cases

# ---------- Paths ----------
_PKG_ROOT = Path(__file__).resolve().parent.parent
YAML_CASE_DIR = _PKG_ROOT / "data" / "cases"

# ---------- Global containers ----------
CATEGORY_REGISTRY: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
CASE_LIB: Dict[str, Dict[str, Any]] = {}
CATEGORIES: "OrderedDict[str, List[str]]" = OrderedDict()
CAT_META: "OrderedDict[str, Tuple[str, str]]" = OrderedDict()
LOAD_ERRORS: List[str] = []


# ---------- Load one YAML file ----------
def _load_yaml_file(path: Path) -> Tuple[Dict, Dict, List[str]]:
    """Returns (meta, cases, errors)."""
    errors: List[str] = []
    data, err = load_yaml(path)
    if err:
        return {}, {}, ["[%s] %s" % (path.name, err)]

    meta = data.get("meta")
    cases = data.get("cases")

    if not isinstance(meta, dict) or "name" not in meta:
        return {}, {}, ["[%s] missing valid meta.name" % path.name]
    if not isinstance(cases, dict) or not cases:
        return {}, {}, ["[%s] missing valid cases" % path.name]

    # Fill in the 'cat' field for every case (avoid repeating it in YAML).
    for cid, case in cases.items():
        if isinstance(case, dict):
            case.setdefault("cat", meta["name"])

    # Validate.
    case_errors = validate_cases(cases, path.name)
    if case_errors:
        errors.extend(case_errors)
        if len(case_errors) >= max(1, len(cases)):
            errors.append("[%s] too many bad cases, skipping whole file" % path.name)
            return {}, {}, errors

    return meta, cases, errors


# ---------- Aggregate ----------
def _load_all():
    registry: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    all_cases: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    seen_case_ids: Dict[str, str] = {}

    for path in discover_yaml_files(YAML_CASE_DIR):
        meta, cases, errs = _load_yaml_file(path)
        errors.extend(errs)
        if not meta or not cases:
            continue

        name = meta["name"]
        if name in registry:
            errors.append(
                "[%s] category name '%s' is already used by %s, skipping this file. "
                "Please choose a unique category name "
                "(e.g., '%s EN' / '%s v2' / '%s (industry)'). "
                "Run `aisec categories` to see existing category names."
                % (path.name, name, registry[name]["source"], name, name, name)
            )
            continue

        safe_cases = {}
        for cid, case in cases.items():
            if cid in seen_case_ids:
                errors.append(
                    "[%s] case ID '%s' already defined in %s, skipping this entry. "
                    "Please pick a new ID (run `aisec next-id`)."
                    % (path.name, cid, seen_case_ids[cid])
                )
                continue
            seen_case_ids[cid] = path.name
            safe_cases[cid] = case

        registry[name] = {
            "name": name,
            "icon": meta.get("icon", ""),
            "desc": meta.get("desc", ""),
            "order": int(meta.get("order", 999)),
            "owasp": meta.get("owasp", []),
            "contributors": meta.get("contributors", []),
            "source": path.name,
            "cases": safe_cases,
        }
        all_cases.update(safe_cases)

    registry = OrderedDict(
        sorted(registry.items(), key=lambda kv: (kv[1]["order"], kv[0]))
    )
    return registry, all_cases, errors


# ---------- Executed once at module import ----------
CATEGORY_REGISTRY, CASE_LIB, LOAD_ERRORS = _load_all()

CATEGORIES = OrderedDict(
    (name, list(info["cases"].keys()))
    for name, info in CATEGORY_REGISTRY.items()
)

CAT_META = OrderedDict(
    (name, (info["icon"], info["desc"]))
    for name, info in CATEGORY_REGISTRY.items()
)


# ---------- Query API ----------
def list_categories() -> List[str]:
    return list(CATEGORY_REGISTRY.keys())


def list_cases(category: str = None) -> List[str]:
    if category is None:
        return list(CASE_LIB.keys())
    return list(CATEGORIES.get(category, []))


def get_case(case_id: str) -> Dict[str, Any]:
    if case_id not in CASE_LIB:
        raise KeyError("Unknown case: %s" % case_id)
    return CASE_LIB[case_id]


def stats() -> Dict[str, int]:
    return {
        "categories": len(CATEGORY_REGISTRY),
        "cases": len(CASE_LIB),
        "errors": len(LOAD_ERRORS),
    }


# ---------- Self-check entry ----------
if __name__ == "__main__":
    print("Loaded %d categories, %d cases." % (len(CATEGORY_REGISTRY), len(CASE_LIB)))
    for name, info in CATEGORY_REGISTRY.items():
        print("  [%3d] %s %s (%d cases) <- %s"
              % (info["order"], info["icon"], name,
                 len(info["cases"]), info["source"]))
    if LOAD_ERRORS:
        print("\n[!] Issues found:")
        for e in LOAD_ERRORS:
            print("  -", e)
    else:
        print("\n[OK] All cases validated.")