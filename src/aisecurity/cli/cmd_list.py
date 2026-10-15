# -*- coding: utf-8 -*-
"""aisec list -- list categories and cases."""
from ..core.registry import CATEGORY_REGISTRY, CASE_LIB

def add_list_parser(sub):
    p = sub.add_parser("list", help="list categories / cases")
    p.add_argument("--category", "-c", default=None,
                   help="only list cases in the given category")
    p.add_argument("--cases-only", action="store_true",
                   help="only output case IDs (for scripting)")
    p.add_argument("--all", "-a", action="store_true",
                   help="expand all cases under every category")

def handle_list(args):
    # Only output case IDs
    if args.cases_only:
        if args.category:
            for cid in CATEGORY_REGISTRY.get(args.category, {}).get("cases", {}):
                print(cid)
        else:
            for cid in CASE_LIB:
                print(cid)
        return 0

    # Show cases in one category
    if args.category:
        info = CATEGORY_REGISTRY.get(args.category)
        if not info:
            print("Unknown category: %s" % args.category)
            return 1
        print("%s %s (%d cases)" % (info["icon"], info["name"], len(info["cases"])))
        for cid in info["cases"]:
            case = info["cases"][cid]
            print("  %s  [%s]  %s" % (cid, case.get("level", "?"), case.get("sub3", "")))
        return 0

    # Default: list all categories
    print("Loaded %d categories, %d cases\n"
          % (len(CATEGORY_REGISTRY), len(CASE_LIB)))

    for name, info in CATEGORY_REGISTRY.items():
        print("  %s %s (%d cases)"
              % (info["icon"], name, len(info["cases"])))

        # If --all is set, expand all cases
        if args.all:
            for cid in info["cases"]:
                case = info["cases"][cid]
                print("        %s  [%s]  %s"
                      % (cid, case.get("level", "?"), case.get("sub3", "")))

    return 0