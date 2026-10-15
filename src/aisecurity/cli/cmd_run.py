# -*- coding: utf-8 -*-
"""aisec run -- execute cases against a target."""
import json
import sys

from ..core.registry import CASE_LIB, CATEGORIES
from ..runner.runner import Runner
from ..evaluators import build_evaluators

def add_run_parser(sub):
    p = sub.add_parser("run", help="execute cases against a target")
    p.add_argument("--case", "-c", default=None, help="single case ID, e.g. PI-001")
    p.add_argument("--category", "-C", default=None, help="run by category")
    p.add_argument("--all", action="store_true", help="run all cases")
    p.add_argument("--target", default="openai",
                   choices=["openai"], help="target type (currently only openai-compatible)")
    p.add_argument("--endpoint", required=True,
                   help="target API endpoint, e.g. https://api.openai.com")
    p.add_argument("--model", required=True, help="model name")
    p.add_argument("--api-key", default="", help="API key")
    p.add_argument("--system-prompt", default=None, help="extra system prompt")
    p.add_argument("--eval", default="marker,regex", help="evaluators, comma-separated")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument("--output", "-o", default=None, help="write result to file")


def handle_run(args):
    from ..targets.openai_compat import OpenAITarget

    target = OpenAITarget(
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
        system_prompt=args.system_prompt,
    )
    evaluators = build_evaluators(args.eval)
    runner = Runner(target, evaluators)

    if args.case:
        if args.case not in CASE_LIB:
            print("Unknown case: %s" % args.case)
            return 1
        results = runner.run_case(args.case)
    elif args.category:
        if args.category not in CATEGORIES:
            print("Unknown category: %s" % args.category)
            return 1
        results = runner.run_category(args.category)
    elif args.all:
        results = runner.run_all()
    else:
        print("Please specify one of --case / --category / --all")
        return 1

    if args.json or args.output:
        data = [r.to_dict() for r in results]
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print("Result written to: %s (%d entries)" % (args.output, len(results)))
        else:
            print(text)
    else:
        total = len(results)
        ok = sum(1 for r in results if r.success)
        err = sum(1 for r in results if r.error)
        print("Done: %d payloads; hits %d; errors %d" % (total, ok, err))
        for r in results:
            tag = "[OK]" if r.success else ("[!]" if r.error else ".")
            detail = ""
            if r.eval_results:
                detail = " | ".join(er.detail for er in r.eval_results)
            if r.error:
                detail = r.error
            print("  %s %s  %s" % (tag, r.case_id, detail[:80]))

    return 0