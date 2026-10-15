# -*- coding: utf-8 -*-
"""aisec validate -- used by CI, validates all cases."""
import sys
from ..core.registry import CATEGORY_REGISTRY, CASE_LIB, LOAD_ERRORS

def add_validate_parser(sub):
    sub.add_parser("validate", help="validate all cases")


def handle_validate(args):
    print("Loaded %d categories, %d cases:\n"
          % (len(CATEGORY_REGISTRY), len(CASE_LIB)))
    for name, info in CATEGORY_REGISTRY.items():
        print("  %s %s (%d cases) <- %s"
              % (info["icon"], name,
                 len(info["cases"]), info["source"]))

    if LOAD_ERRORS:
        print("\n[!] Issues found:")
        for e in LOAD_ERRORS:
            print("  -", e)
        return 1

    print("\nAll cases validated.")
    return 0