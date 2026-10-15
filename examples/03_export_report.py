# -*- coding: utf-8 -*-
"""
Example 3: export the case library as Markdown.
Run: python examples/03_export_report.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from aisecurity.core.registry import CATEGORY_REGISTRY


def to_markdown():
    lines = ["# AISecurityTest Case Library\n"]
    total = 0
    for name, info in CATEGORY_REGISTRY.items():
        n = len(info["cases"])
        total += n
        lines.append("## %s %s (%d cases)\n" % (info["icon"], name, n))
        lines.append("> %s\n" % info.get("desc", ""))
        lines.append("| Case ID | Category L3 | Level | OWASP |")
        lines.append("|---|---|---|---|")
        for cid, case in info["cases"].items():
            lines.append("| %s | %s | %s | %s |" % (
                cid, case.get("sub3", ""), case.get("level", ""), case.get("owasp", "")))
        lines.append("")
    lines.insert(1, "\nTotal: %d categories, %d cases.\n"
                 % (len(CATEGORY_REGISTRY), total))
    return "\n".join(lines)


def main():
    md = to_markdown()
    out = os.path.join(_HERE, "cases_export.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("Exported: %s" % out)
    print("Total %d characters" % len(md))


if __name__ == "__main__":
    main()