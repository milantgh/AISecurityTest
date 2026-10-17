# -*- coding: utf-8 -*-
"""
Example 1: generate payloads.
Run: python examples/01_generate_payload.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from aisecurity.core.registry import CASE_LIB, CATEGORIES
from aisecurity.engine.payload import gen_by_case
from aisecurity.engine.compose import gen_three, PRESETS


def main():
    print("=" * 60)
    print("1. Generate payloads per case")
    print("=" * 60)
    case_id = "PI-001"
    for i, p in enumerate(gen_by_case(case_id), 1):
        print("[%d] %s" % (i, p))
        print()

    print("=" * 60)
    print("2. Three-layer composed payloads")
    print("=" * 60)
    # PRESETS keys are "marker" / "leak_system_prompt" / "role_hijack".
    # The old example used the Chinese label "回执标记", which is not a key
    # and raises KeyError. Use "marker" instead.
    payload = PRESETS["marker"]
    for i, p in enumerate(gen_three(3, payload), 1):
        print("[%d] %s" % (i, p))
        print()

    print("=" * 60)
    print("3. Iterate over all categories")
    print("=" * 60)
    for cat, ids in CATEGORIES.items():
        print("%s: %d cases" % (cat, len(ids)))
    print("Total: %d cases" % len(CASE_LIB))


if __name__ == "__main__":
    main()