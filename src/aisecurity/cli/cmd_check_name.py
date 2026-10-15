# -*- coding: utf-8 -*-
"""
aisec check-name -- check whether a category name is already taken.
For contributors: verify the name does not conflict before writing YAML.
"""
from ..core.registry import CATEGORY_REGISTRY

def add_check_name_parser(sub):
    p = sub.add_parser(
        "check-name",
        help="check whether a category name is already taken")
    p.add_argument("name", help="the category name to check")


def _suggest_alternatives(name):
    """Suggest available alternatives based on existing category names."""
    suggestions = [
        "%s_EN" % name,
        "%s_JA" % name,
        "%s_v2" % name,
        "%s(finance)" % name,
        "%s(energy)" % name,
        "%s(support)" % name,
    ]
    available = [s for s in suggestions if s not in CATEGORY_REGISTRY]
    return available


def handle_check_name(args):
    name = args.name.strip()

    if not name:
        print("ERROR: category name cannot be empty")
        return 1

    if name not in CATEGORY_REGISTRY:
        print("Available: '%s' is not taken" % name)
        return 0

    info = CATEGORY_REGISTRY[name]
    print("Conflict: category name '%s' is already taken" % name)
    print("Source file: %s" % info["source"])
    print()

    alts = _suggest_alternatives(name)
    if alts:
        print("Suggested naming patterns "
              "[conflict_name_suffix, conflict_name(suffix)]:\n")
        for a in alts:
            print("   %s" % a)
    print()
    print("List all existing category names:")
    print("   aisec categories")
    return 1