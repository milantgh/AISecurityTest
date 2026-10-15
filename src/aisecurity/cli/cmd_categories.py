# -*- coding: utf-8 -*-
"""
aisec categories -- list all category names, one per line.
For contributors: check existing category names before adding a new case,
to avoid name conflicts.
"""
from ..core.registry import CATEGORY_REGISTRY


def add_categories_parser(sub):
    p = sub.add_parser(
        "categories",
        help="list all category names")
    p.add_argument(
        "--detail", "-d", action="store_true",
        help="show detailed info (file name, case count)")
    p.add_argument(
        "--group", "-g", action="store_true",
        help="group by prefix")


def _prefix(name):
    """Extract the prefix of a category name for grouping.

    Rule: split at common suffix separators.
    """
    for sep in (" EN", " JA", " v", "（", "(", " 20"):
        if sep in name:
            return name.split(sep)[0]
    return name


def _print_grouped(names):
    """Print grouped by prefix."""
    groups = {}
    order = []
    for name in names:
        p = _prefix(name)
        if p not in groups:
            groups[p] = []
            order.append(p)
        groups[p].append(name)

    for prefix in order:
        items = groups[prefix]
        if len(items) > 1:
            print("[%s]" % prefix)
            for item in items:
                print("  %s" % item)
            print()
        else:
            print(items[0])


def handle_categories(args):
    if not CATEGORY_REGISTRY:
        print("No categories found.")
        return 0

    names = list(CATEGORY_REGISTRY.keys())

    if args.detail:
        for name in names:
            info = CATEGORY_REGISTRY[name]
            print("%s\t%s\t%d cases" % (
                name, info["source"], len(info["cases"])))
        return 0

    if args.group:
        _print_grouped(names)
        return 0

    for name in names:
        print(name)
    return 0