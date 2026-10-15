# -*- coding: utf-8 -*-
"""
Core assertions: all cases must be valid.
This is the most important test in CI.
Any PR that adds a broken case will fail here.
"""
from aisecurity.core.registry import (
    CATEGORY_REGISTRY,
    CASE_LIB,
    LOAD_ERRORS,
)
from aisecurity.core.schema import validate_case


def test_no_load_errors():
    assert LOAD_ERRORS == [], "Errors found while loading cases:\n" + "\n".join(LOAD_ERRORS)


def test_has_categories():
    assert len(CATEGORY_REGISTRY) >= 1, "At least 1 category expected"


def test_has_cases():
    assert len(CASE_LIB) >= 1, "At least 1 case expected"


def test_all_cases_valid():
    """Validate each case; report all failures together."""
    bad = []
    for cid, case in CASE_LIB.items():
        errs = validate_case(case)
        if errs:
            bad.append("%s: %s" % (cid, "; ".join(errs)))
    assert not bad, "Invalid cases:\n" + "\n".join(bad)


def test_case_ids_unique_across_categories():
    seen = {}
    for name, info in CATEGORY_REGISTRY.items():
        for cid in info["cases"]:
            assert cid not in seen, \
                "Duplicate case ID '%s' in %s and %s" % (cid, seen.get(cid), name)
            seen[cid] = name


def test_category_order_is_int():
    for name, info in CATEGORY_REGISTRY.items():
        assert isinstance(info["order"], int), \
            "Category %s: order must be int, got %s" % (name, type(info["order"]))