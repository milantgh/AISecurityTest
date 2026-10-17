# -*- coding: utf-8 -*-
"""
aisec gen -- generate case payloads.
Usage:
    aisec gen PI-001              # generate payloads for PI-001
    aisec gen --all               # generate payloads for all cases (skips manual-only)
    aisec gen PI-001 --count 3    # add 3 three-layer composed payloads
    aisec gen PI-001 --raw        # only payloads, no title (for scripting)

Long payload handling
---------------------
PI-023 builds an 8000-character filler at runtime. Printing it in full floods
the terminal. Non-raw mode truncates payloads longer than 200 characters.
--raw mode prints payloads verbatim because it is meant for scripting.
"""
from ..core.registry import CASE_LIB
from ..engine.payload import gen_by_case
from ..engine.compose import gen_three, PRESETS

# Truncate long payloads in non-raw mode so a single case cannot flood the
# terminal. --raw mode is unaffected.
MAX_PREVIEW = 200


def add_gen_parser(sub):
    p = sub.add_parser("gen", help="generate case payloads")
    p.add_argument("case_id", nargs="?", default=None,
                   help="case ID, e.g. PI-001. Omit only if --all is set.")
    p.add_argument("--all", "-a", action="store_true",
                   help="generate payloads for all auto-runnable cases "
                        "(manual_only cases are skipped)")
    p.add_argument("--count", "-n", type=int, default=0,
                   help="add N three-layer composed payloads (0 = original only)")
    p.add_argument("--preset", default="marker",
                   choices=list(PRESETS.keys()),
                   help="preset payload for three-layer composition "
                        "(valid: %s)" % ", ".join(PRESETS.keys()))
    p.add_argument("--raw", action="store_true",
                   help="only output payloads, no title (for scripting)")


def _sorted_case_ids():
    """Sort by numeric ID: PI-001 -> PI-002 -> ... -> PI-040."""
    return sorted(
        CASE_LIB.keys(),
        key=lambda x: int(x[3:]) if x.startswith("PI-") and x[3:].isdigit() else 9999,
    )


def _preview(p):
    """Shorten a payload for display. --raw callers should not use this."""
    if len(p) <= MAX_PREVIEW:
        return p
    return "%s... [truncated, %d chars total]" % (p[:MAX_PREVIEW], len(p))


def _print_payloads(cid, raw=False, count=0, preset="marker"):
    """Print payloads for one case."""
    payloads = gen_by_case(cid)

    if count > 0:
        if preset not in PRESETS:
            # Defensive: argparse choices should have caught this already,
            # but guard against programmatic callers.
            print("[!] Unknown preset %r. Valid presets: %s"
                  % (preset, ", ".join(PRESETS.keys())))
            return
        compose_payloads = gen_three(count, PRESETS[preset])
        payloads = payloads + compose_payloads

    if raw:
        for p in payloads:
            print(p)
    else:
        case = CASE_LIB[cid]
        print("[%s] %s" % (cid, case.get("sub3", "")))
        print("-" * 60)
        for i, p in enumerate(payloads, 1):
            print("%d. %s" % (i, _preview(p)))
        print()


def handle_gen(args):
    if args.all:
        skipped = 0
        for cid in _sorted_case_ids():
            case = CASE_LIB[cid]
            if case.get("manual_only"):
                skipped += 1
                continue
            _print_payloads(cid, raw=args.raw, count=0, preset=args.preset)
        if skipped and not args.raw:
            print("[!] Skipped %d manual_only case(s). Run `aisec gen <id>` "
                  "explicitly to see them." % skipped)
        return 0

    if not args.case_id:
        print("Please specify a case ID, or use --all to generate all.")
        print("Example: aisec gen PI-001")
        return 1

    cid = args.case_id.strip()
    if cid not in CASE_LIB:
        print("Unknown case: %s" % cid)
        print()
        print("Available case IDs:")
        for i in _sorted_case_ids():
            print("  %s" % i)
        return 1

    if CASE_LIB[cid].get("manual_only") and not args.raw:
        print("[%s] is a manual-only case. It needs a human-run environment "
              "(file upload, browser, RAG, etc.)." % cid)
        print("Its payloads are shown below for reference, but `aisec autoscan` "
              "will skip it.")
        print()

    _print_payloads(cid, raw=args.raw, count=args.count, preset=args.preset)
    return 0