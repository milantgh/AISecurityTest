# -*- coding: utf-8 -*-
"""Tiny version-range helper for CVE rules.

Rule files express affected ranges as compact strings, e.g.::

    affected: "*"                 # every version
    affected: ">=0.1.32,<0.1.46"  # AND of comparisons
    affected: ">=1.2,<=2.0"

This module intentionally avoids extra dependencies (no ``packaging`` /
``semver``) so the toolkit stays installable with just PyYAML.
Missing components are treated as 0 (``1.2`` == ``1.2.0``).
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

_NUM_RE = re.compile(r"\d+")
_OP_RE = re.compile(r"^(>=|<=|==|!=|>|<|=)?\s*(.+)$")


def parse_version(text) -> Optional[Tuple[int, ...]]:
    """Return a numeric tuple for *text*, or None when unparseable."""
    if text is None:
        return None
    nums = _NUM_RE.findall(str(text).strip())
    if not nums:
        return None
    return tuple(int(n) for n in nums)


def _cmp(a: Tuple[int, ...], b: Tuple[int, ...]) -> int:
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return (a > b) - (a < b)


def version_in_range(version, spec) -> bool:
    """True when *version* satisfies *spec*.

    An unknown/empty *version* matches only the catch-all spec (``*``),
    so version-based rules never fire blindly.
    """
    if spec is None:
        return True
    spec = str(spec).strip()
    if spec in ("", "*", "all", "any"):
        return True

    ver = parse_version(version)
    if ver is None:
        return False

    for part in spec.split(","):
        part = part.strip()
        if not part or part == "*":
            continue
        m = _OP_RE.match(part)
        if not m:
            continue
        op = m.group(1) or "=="
        if op == "=":
            op = "=="
        want = parse_version(m.group(2))
        if want is None:
            continue
        c = _cmp(ver, want)
        ok = {
            ">=": c >= 0, "<=": c <= 0, ">": c > 0, "<": c < 0,
            "==": c == 0, "!=": c != 0,
        }[op]
        if not ok:
            return False
    return True
