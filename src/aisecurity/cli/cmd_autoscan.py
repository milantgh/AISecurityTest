# -*- coding: utf-8 -*-
"""
aisec autoscan -- automated scanning.

Usage:
    aisec autoscan list
    aisec autoscan list-transforms
    aisec autoscan history [--limit N] [--target T] [--model M]
    aisec autoscan report [scan_id] [--format markdown|json|html] [-o file]
    aisec autoscan run --endpoint URL --model MODEL --api-key KEY
                       [--profile NAME] [--case IDS]
                       [--transform LIST | --transform-all]
                       [--lang LIST]
                       [--eval marker,regex,judge]
                       [--judge-endpoint URL] [--judge-model NAME]
                       [--judge-api-key KEY]
                       [-v|-vv|-vvv]
                       [--format markdown|json|html] [-o file]

The LLM-as-Judge evaluator is OPTIONAL. It is only enabled when
--judge-endpoint is provided AND "judge" is listed in --eval. Without it,
the tool behaves exactly as before (marker + regex only).
"""
import sys
import json
from ..targets.openai_compat import OpenAITarget
from ..evaluators import build_evaluators
from ..core.registry import CASE_LIB
from ..autotest import AutoScanner
from ..autotest.schedule import list_profiles
from ..autotest.strategy import list_strategies
from ..autotest.report import to_json, to_markdown, to_html
from ..autotest import storage


def add_autoscan_parser(sub):
    p = sub.add_parser("autoscan", help="automated scan (YAML-driven, multi-turn supported)")
    sp = p.add_subparsers(dest="as_cmd")

    # ---- list ----
    sp.add_parser("list", help="list available profiles and strategies")

    # ---- list-transforms ----
    sp.add_parser("list-transforms", help="list all available payload transforms")

    # ---- history ----
    h = sp.add_parser("history", help="list scan history")
    h.add_argument("--limit", "-n", type=int, default=20,
                   help="show the last N entries (default 20)")
    h.add_argument("--target", default=None, help="filter by target")
    h.add_argument("--model", default=None, help="filter by model")

    # ---- report ----
    r = sp.add_parser("report", help="generate a report from a historical scan")
    r.add_argument("scan_id", nargs="?", default=None,
                   help="scan ID; omit to use the most recent scan")
    r.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "json", "html"])
    r.add_argument("--output", "-o", default=None,
                   help="output file; omit to print to stdout")

    # ---- run ----
    g = sp.add_parser("run", help="execute a scan")
    g.add_argument("--endpoint", required=True,
                   help="OpenAI-compatible API base URL, e.g. https://api.deepseek.com "
                        "(do not include /v1; it is appended automatically)")
    g.add_argument("--model", required=True, help="model name")
    g.add_argument("--api-key", default="", help="API key for the target")
    g.add_argument("--system-prompt", default=None, help="target system prompt")
    g.add_argument("--timeout", type=int, default=60, help="per-request timeout in seconds")

    # Case selection
    g.add_argument("--profile", default=None, help="which profile to use")
    g.add_argument("--case", default=None, help="filter by case ID, comma-separated")
    g.add_argument("--category", default=None, help="filter by category name")
    g.add_argument("--owasp", default=None, help="filter by OWASP ID")
    g.add_argument("--level", default=None, help="filter by risk level")
    g.add_argument("--probes", default=None,
                   help="run probes instead of (or in addition to) YAML cases, "
                        "comma-separated probe names. Use 'all' to run every probe. "
                        "List available probes with: aisec probes list")

    # Variant expansion
    g.add_argument("--transform", "-t", default=None,
                   help="transform list, comma-separated (raw,base64,hex,zero_width,"
                        "case_mix,similar,html,code,chatml_sys,chatml_ast,llama_inst,unicode); "
                        "omit to apply no transform")
    g.add_argument("--transform-all", action="store_true",
                   help="use all 12 transforms (cartesian product expansion)")
    g.add_argument("--lang", default=None,
                   help="language list, comma-separated (zh,en,sw,is,ha,mi,cy); "
                        "omit to use Chinese only")

    # Multi-turn
    g.add_argument("--multi-turn", default=None, help="multi-turn strategy name")
    g.add_argument("--max-turns", type=int, default=5, help="max turns for multi-turn")

    # Execution control
    g.add_argument("--rate", type=float, default=0.5,
                   help="minimum interval between requests in seconds")
    g.add_argument("--eval", default="marker,regex",
                   help="evaluators, comma-separated "
                        "(marker,regex,judge,unicode_tags,multilingual). "
                        "The judge evaluator is only built when --judge-endpoint is also set.")
    g.add_argument("--stop-on-error", action="store_true",
                   help="stop immediately on the first error")

    # Optional LLM-as-Judge second detection line.
    # Leave --judge-endpoint unset to keep the original marker+regex behavior.
    g.add_argument("--judge-endpoint", default=None,
                   help="Optional: OpenAI-compatible base URL for LLM-as-Judge "
                        "(do not include /v1). Omit to disable the judge evaluator.")
    g.add_argument("--judge-model", default="gpt-4o-mini",
                   help="Judge model name (only used with --judge-endpoint)")
    g.add_argument("--judge-api-key", default="",
                   help="Judge API key (only used with --judge-endpoint)")
    g.add_argument("--judge-timeout", type=int, default=30,
                   help="Judge per-request timeout in seconds")

    # Verbosity
    g.add_argument("-v", "--verbose", action="count", default=0,
                   help="verbosity: -v case-level / -vv payload-level / -vvv full response")

    # Output
    g.add_argument("--output", "-o", default=None, help="report output file")
    g.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "json", "html"],
                   help="report format")
    return p


def handle_autoscan(args):
    if args.as_cmd == "list":
        return _handle_list()
    if args.as_cmd == "list-transforms":
        return _handle_list_transforms()
    if args.as_cmd == "history":
        return _handle_history(args)
    if args.as_cmd == "report":
        return _handle_report(args)
    if args.as_cmd == "run":
        return _handle_run(args)
    print("Please specify a subcommand: list / list-transforms / history / report / run")
    return 1


# ---------- list ----------
def _handle_list():
    print("Scan profiles:")
    for p in list_profiles():
        print("  %s" % p)
    print()
    print("Multi-turn strategies:")
    for s in list_strategies():
        print("  %s" % s)
    print()
    print("Usage example:")
    print("  aisec autoscan run --endpoint https://api.deepseek.com \\")
    print("      --model deepseek-chat --api-key sk-xxx \\")
    print("      --profile text_only --transform-all --lang zh,en -v")
    print()
    print("With optional LLM-as-Judge as a second detection line:")
    print("  aisec autoscan run --endpoint https://api.deepseek.com \\")
    print("      --model deepseek-chat --api-key sk-xxx --profile quick \\")
    print("      --eval marker,regex,judge \\")
    print("      --judge-endpoint https://api.openai.com \\")
    print("      --judge-model gpt-4o-mini --judge-api-key sk-yyy")
    return 0


# ---------- list-transforms ----------
def _handle_list_transforms():
    from ..autotest.expand import list_transforms
    print("Available payload transforms:")
    for t in list_transforms():
        print("  %-14s %s" % (t["name"], t["desc"]))
    print()
    print("Usage:")
    print("  --transform base64,zero_width      apply only the listed transforms")
    print("  --transform-all                    apply all 12 transforms")
    print("  --lang zh,en,sw                    stack multiple languages")
    return 0


# ---------- history ----------
def _handle_history(args):
    rows = storage.list_scans(limit=args.limit, target=args.target, model=args.model)
    if not rows:
        print("No scan history.")
        return 0
    print("%-24s %-42s %-22s %-6s %-6s %s" % (
        "SCAN ID", "TARGET", "MODEL", "HITS", "TOTAL", "STARTED"))
    print("-" * 130)
    for r in rows:
        print("%-24s %-42s %-22s %-6d %-6d %s" % (
            r["scan_id"],
            (r["target"] or "")[:42],
            (r["model"] or "")[:22],
            r["hits"] or 0,
            r["total_payloads"] or 0,
            r["started_at"] or "",
        ))
    print()
    s = storage.stats()
    print("Total: %d scans · %d payloads · %d hits · overall hit rate %.2f%%" % (
        s["total_scans"], s["total_payloads"], s["total_hits"],
        s["overall_hit_rate"] * 100))
    return 0


# ---------- report ----------
def _handle_report(args):
    scan_id = args.scan_id
    if not scan_id:
        rows = storage.list_scans(limit=1)
        if not rows:
            print("No scan history.")
            return 1
        scan_id = rows[0]["scan_id"]
        print("Using the most recent scan: %s" % scan_id)

    result = storage.load(scan_id)
    if result is None:
        print("Scan not found: %s" % scan_id)
        return 1

    if args.format == "json":
        text = to_json(result)
    elif args.format == "html":
        text = to_html(result)
    else:
        text = to_markdown(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("Report written to: %s" % args.output)
    else:
        print(text)
    return 0


# ---------- run ----------
def _handle_run(args):
    from ..autotest.expand import parse_transform_list, parse_lang_list, count_variants

    target = OpenAITarget(
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
        system_prompt=args.system_prompt,
        timeout=args.timeout,
    )

    # Build the optional judge config. It is None unless the user explicitly
    # passed --judge-endpoint. When None, build_evaluators() silently skips
    # any "judge" entry in --eval, preserving the original behavior.
    judge_config = None
    if getattr(args, "judge_endpoint", None):
        judge_config = {
            "endpoint": args.judge_endpoint,
            "model": args.judge_model,
            "api_key": args.judge_api_key,
            "timeout": args.judge_timeout,
        }

    evaluators = build_evaluators(args.eval, judge_config=judge_config)
    evaluator_names = [getattr(e, "name", type(e).__name__) for e in evaluators]
    if not evaluators:
        print("[autoscan] Warning: no evaluators built from --eval %r. "
              "Check the names and, for judge, whether --judge-endpoint is set."
              % args.eval)
    else:
        print("[autoscan] Evaluators: %s" % ", ".join(evaluator_names))
    sys.stdout.flush()

    # Parse transforms and languages
    if args.transform_all:
        from ..autotest.expand import TRANSFORMS
        transforms = list(TRANSFORMS.keys())
    elif args.transform:
        transforms = parse_transform_list(args.transform)
    else:
        transforms = None

    languages = parse_lang_list(args.lang) if args.lang else None

    # -v count mapped to log_level
    log_level = min(3, 1 + args.verbose)

    scanner = AutoScanner(
        target=target,
        evaluators=evaluators,
        rate_limit_sec=args.rate,
        stop_on_error=args.stop_on_error,
        verbose=bool(args.verbose),
        log_level=log_level,
    )

    # Warn about estimated variant count
    if transforms or languages:
        est = count_variants(transforms or ["raw"], languages or ["zh"])
        print("[autoscan] Each payload will expand into %d variants" % est)
        sys.stdout.flush()

    # Warn early for non-streaming output formats
    if args.format in ("html", "json") and not args.output:
        print("[autoscan] Scanning... (report will be printed once after the scan)")
    elif args.format in ("html", "json") and args.output:
        print("[autoscan] Scanning; report will be written to %s ..." % args.output)
    sys.stdout.flush()

    try:
        if args.multi_turn:
            case_id = (args.case.split(",")[0] if args.case else "PI-002")
            result = scanner.scan_multi_turn(
                args.multi_turn, case_id=case_id, max_turns=args.max_turns
            )
        elif args.probes:
            # Run attack probes instead of (or in addition to) YAML cases.
            if args.probes.strip().lower() == "all":
                probe_names = ["all"]
            else:
                probe_names = [n.strip() for n in args.probes.split(",") if n.strip()]
            print("[autoscan] Running %d probe(s)..." % len(probe_names))
            sys.stdout.flush()
            result = scanner.scan_probes(
                probe_names, transforms=transforms, languages=languages
            )
        elif args.profile:
            result = scanner.scan_profile(
                args.profile, transforms=transforms, languages=languages
            )
        else:
            case_ids = _resolve_case_ids(args)
            if not case_ids:
                print("No matching cases.")
                print("Use --profile / --case / --category / --owasp / --level to select.")
                return 1
            result = scanner.scan(case_ids, transforms=transforms,
                                   languages=languages)
    except Exception as e:
        print("[autoscan] Execution failed: %s" % e)
        return 1

    # Report output
    if args.format == "json":
        text = to_json(result)
    elif args.format == "html":
        text = to_html(result)
    else:
        text = to_markdown(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("[autoscan] Report written to: %s" % args.output)
    else:
        if args.format == "markdown":
            print(text)
        else:
            print("[autoscan] Report format %s requires --output" % args.format)

    return 2 if result.hits > 0 else 0


# ---------- helpers ----------
def _resolve_case_ids(args):
    ids = []
    if args.case:
        ids = [c.strip() for c in args.case.split(",") if c.strip()]
    elif args.category:
        for cid, case in CASE_LIB.items():
            if case.get("cat") == args.category:
                ids.append(cid)
    elif args.owasp:
        for cid, case in CASE_LIB.items():
            if args.owasp in case.get("owasp", ""):
                ids.append(cid)
    elif args.level:
        for cid, case in CASE_LIB.items():
            if case.get("level") == args.level:
                ids.append(cid)
    return ids