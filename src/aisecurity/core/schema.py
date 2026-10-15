# -*- coding: utf-8 -*-
"""
Case data structure and validation.
Cases loaded from YAML are represented uniformly as dict objects.
Required fields are listed in REQUIRED_FIELDS.
"""
from typing import Any, Dict, List

REQUIRED_FIELDS = (
    "id", "cat", "sub", "sub3", "pre",
    "steps", "expect", "level", "defense", "owasp", "note",
)

# Risk levels are stored in Chinese because existing YAML files use them.
VALID_LEVELS = {"严重", "高", "中-高", "中", "低"}


def validate_case(case: Dict[str, Any]) -> List[str]:
    """Validate one case. Returns a list of error messages (empty = valid)."""
    errs: List[str] = []
    if not isinstance(case, dict):
        return ["case must be a dict"]

    for f in REQUIRED_FIELDS:
        if f not in case:
            errs.append("missing field: %s" % f)
            continue
        if f == "steps":
            if not isinstance(case[f], list) or not case[f]:
                errs.append("steps must be a non-empty list[str]")
            elif not all(isinstance(s, str) for s in case[f]):
                errs.append("each item in steps must be str")
        elif not isinstance(case[f], str):
            errs.append("%s must be str" % f)

    if case.get("level") and case["level"] not in VALID_LEVELS:
        errs.append("invalid level: %s (valid: %s)"
                    % (case["level"], sorted(VALID_LEVELS)))

    if "id" in case and isinstance(case["id"], str):
        if not case["id"].startswith("PI-"):
            errs.append("case ID must start with 'PI-': %s" % case["id"])

    return errs


def validate_cases(cases: Dict[str, Dict[str, Any]], source: str = "") -> List[str]:
    """Validate a dict of cases. Returns a list of error messages with source prefix."""
    errs: List[str] = []
    if not isinstance(cases, dict):
        return ["[%s] cases must be dict[str, dict]" % source]

    for cid, case in cases.items():
        if not isinstance(case, dict):
            errs.append("[%s] %s: case must be a dict" % (source, cid))
            continue
        if case.get("id") != cid:
            errs.append("[%s] %s: id field ('%s') does not match key"
                        % (source, cid, case.get("id")))
        for e in validate_case(case):
            errs.append("[%s] %s: %s" % (source, cid, e))
    return errs