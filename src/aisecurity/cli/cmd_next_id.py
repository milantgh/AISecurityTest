# -*- coding: utf-8 -*-
"""
aisec next-id -- show the next available case ID.
For contributors: run this before adding a new case to get the next ID
and avoid conflicts with existing cases.
"""
from ..core.registry import CASE_LIB, CATEGORY_REGISTRY

def add_next_id_parser(sub):
    sub.add_parser("next-id", help="show the next available case ID")


def _extract_max_num():
    """Extract the largest number from all case IDs."""
    max_num = 0
    for cid in CASE_LIB:
        if not cid.startswith("PI-"):
            continue
        try:
            n = int(cid[3:])
        except ValueError:
            continue
        if n > max_num:
            max_num = n
    return max_num


def handle_next_id(args):
    if not CASE_LIB:
        print("No cases found. Start with PI-001.")
        return 0

    max_num = _extract_max_num()
    if max_num == 0:
        print("No cases found. Start with PI-001.")
        return 0

    next_num = max_num + 1
    if next_num < 1000:
        next_id = "PI-%03d" % next_num
    else:
        next_id = "PI-%d" % next_num

    print("Current max ID   : PI-%03d" % max_num)
    print("Next available ID: %s" % next_id)
    print()

    if CATEGORY_REGISTRY:
        print("Existing category names (avoid these for new categories):\n")
        for n in CATEGORY_REGISTRY.keys():
            print("   %s" % n)
        print()
        print("[Full list: aisec categories]")
        print()

    print("Steps to add a new case:\n")
    print("  1. Copy src/aisecurity/data/cases/_template.yaml")
    print("  2. Change id to %s" % next_id)
    print("  3. Pick a unique category name (check with aisec check-name)")
    print("  4. Add a case to the matching category file")
    print("  5. Run aisec validate to check")
    return 0