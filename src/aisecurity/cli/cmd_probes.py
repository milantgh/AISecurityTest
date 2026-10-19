# -*- coding: utf-8 -*-
"""
aisec probes -- list and inspect attack probes.

Usage:
    aisec probes list
    aisec probes show NAME
    aisec probes run NAME --endpoint URL --model MODEL --api-key KEY
                          [--eval marker,regex]
                          [--format markdown|json] [-o file]
"""
import sys
import json
from ..probes import list_probes, get_probe, get_probe_info
from ..targets.openai_compat import OpenAITarget
from ..evaluators import build_evaluators
from ..runner.runner import Runner
from ..runner.result import CaseResult


def add_probes_parser(sub):
    p = sub.add_parser("probes", help="list and run attack probes")
    sp = p.add_subparsers(dest="probe_cmd")

    # ---- list ----
    sp.add_parser("list", help="list all available probes")

    # ---- show ----
    s = sp.add_parser("show", help="show details of a probe")
    s.add_argument("name", help="probe name")

    # ---- run ----
    r = sp.add_parser("run", help="run one or more probes against a target")
    r.add_argument("names", help="probe names, comma-separated (or 'all')")
    r.add_argument("--endpoint", required=True,
                   help="OpenAI-compatible API base URL")
    r.add_argument("--model", required=True, help="model name")
    r.add_argument("--api-key", default="", help="API key")
    r.add_argument("--eval", default="marker,regex",
                   help="evaluators: marker,regex,judge,unicode_tags,multilingual")
    r.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "json"])
    r.add_argument("--output", "-o", default=None, help="output file")
    return p


def handle_probes(args):
    if args.probe_cmd == "list":
        return _handle_list()
    if args.probe_cmd == "show":
        return _handle_show(args)
    if args.probe_cmd == "run":
        return _handle_run(args)
    print("Please specify: list / show NAME / run NAME ...")
    return 1


def _handle_list():
    names = list_probes()
    if not names:
        print("No probes found.")
        return 0
    print("Available probes (%d):" % len(names))
    print("-" * 80)
    for name in names:
        info = get_probe_info(name)
        if info:
            print("  %-14s %s" % (name, info["description"]))
            print("  %-14s   owasp=%s  level=%s  detectors=%s" % (
                "", ",".join(info["owasp"]), info["level"],
                ",".join(info["detectors"])))
    print()
    print("Run a probe:")
    print("  aisec probes run dan --endpoint https://api.deepseek.com "
          "--model deepseek-chat --api-key sk-xxx")
    print("  aisec probes run all --endpoint ... --model ... --api-key ...")
    return 0


def _handle_show(args):
    info = get_probe_info(args.name)
    if info is None:
        print("Probe not found: %s" % args.name)
        print("Available: %s" % ", ".join(list_probes()))
        return 1
    probe = get_probe(args.name)
    payloads = probe.generate()
    print("Probe        : %s" % info["name"])
    print("Description  : %s" % info["description"])
    print("OWASP        : %s" % ", ".join(info["owasp"]))
    print("Level        : %s" % info["level"])
    print("Detectors    : %s" % ", ".join(info["detectors"]))
    print("Payload count: %d" % len(payloads))
    print()
    print("Sample payloads:")
    for i, p in enumerate(payloads[:3], 1):
        print("  %d. %s" % (i, p[:100]))
    if len(payloads) > 3:
        print("  ... (%d more)" % (len(payloads) - 3))
    return 0


def _handle_run(args):
    if args.names == "all":
        names = list_probes()
    else:
        names = [n.strip() for n in args.names.split(",") if n.strip()]

    evaluators = build_evaluators(args.eval)
    target = OpenAITarget(
        endpoint=args.endpoint, model=args.model, api_key=args.api_key)
    runner = Runner(target=target, evaluators=evaluators)

    all_results = []
    for name in names:
        probe = get_probe(name)
        if probe is None:
            print("[probes] Unknown probe: %s (skipped)" % name)
            continue
        payloads = probe.generate()
        print("[probes] Running %s (%d payloads)..." % (name, len(payloads)))
        sys.stdout.flush()
        results = runner.run_probe(name)
        hits = sum(1 for r in results if r.success)
        print("[probes] %s: %d/%d hits" % (name, hits, len(results)))
        all_results.extend(results)

    if not all_results:
        print("No results.")
        return 1

    # Output
    if args.format == "json":
        text = json.dumps([r.to_dict() for r in all_results],
                          ensure_ascii=False, indent=2)
    else:
        lines = ["# Probe Scan Report", ""]
        for r in all_results:
            status = "HIT" if r.success else "miss"
            lines.append("## %s [%s]" % (r.case_id, status))
            lines.append("**Payload:** %s" % (r.payload[:120]))
            if r.error:
                lines.append("**Error:** %s" % r.error)
            else:
                lines.append("**Response:** %s" % (r.response_text[:200]))
                for ev in r.eval_results:
                    lines.append("  - %s: %s" % (ev.name, ev.hit))
            lines.append("")
        text = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("[probes] Report written to: %s" % args.output)
    else:
        print(text)

    total_hits = sum(1 for r in all_results if r.success)
    return 2 if total_hits > 0 else 0
