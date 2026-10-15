# -*- coding: utf-8 -*-
"""
aisec show -- show case information.
Usage:
    aisec show              # list all case IDs
    aisec show PI-001       # show full information of PI-001
"""
from ..core.registry import CASE_LIB

def add_show_parser(sub):
    p = sub.add_parser("show", help="show case info (list all IDs if no argument)")
    p.add_argument("case_id", nargs="?", default=None,
                   help="case ID, e.g. PI-001. If omitted, list all IDs.")


def _list_all_cases():
    """List all case IDs and their L3 subcategories."""
    if not CASE_LIB:
        print("No cases found.")
        return 0

    # Sort by ID
    ids = sorted(
        CASE_LIB.keys(),
        key=lambda x: int(x[3:]) if x.startswith("PI-") and x[3:].isdigit() else 9999,
    )

    print("All cases (%d total):" % len(ids))
    print()
    for cid in ids:
        case = CASE_LIB[cid]
        level = case.get("level", "")
        sub3 = case.get("sub3", "")
        print("  %s  [%s]  %s" % (cid, level, sub3))
    print()
    print("Show details of one case:")
    print("  aisec show PI-001")
    return 0


def handle_show(args):
    cid = args.case_id

    # No argument -> list all
    if cid is None:
        return _list_all_cases()

    # With argument -> show details
    cid = cid.strip()

    if cid not in CASE_LIB:
        print("Unknown case: %s" % cid)
        print()
        print("Available case IDs:")
        ids = sorted(
            CASE_LIB.keys(),
            key=lambda x: int(x[3:]) if x.startswith("PI-") and x[3:].isdigit() else 9999,
        )
        for i in ids:
            print("  %s" % i)
        return 1

    case = CASE_LIB[cid]

    print("Case ID      : %s" % case.get("id", cid))
    print("Category L1  : %s" % case.get("cat", ""))
    print("Category L2  : %s" % case.get("sub", ""))
    print("Category L3  : %s" % case.get("sub3", ""))
    print("Level        : %s" % case.get("level", ""))
    print("OWASP        : %s" % case.get("owasp", ""))
    print("Preconditions: %s" % case.get("pre", ""))
    print("Expected     : %s" % case.get("expect", ""))
    print("Defense      : %s" % case.get("defense", ""))
    print("Note         : %s" % case.get("note", ""))

    print()
    print("Test steps:")
    steps = case.get("steps", [])
    if not steps:
        print("  (none)")
    else:
        for i, s in enumerate(steps, 1):
            print("  %d. %s" % (i, s))

    return 0