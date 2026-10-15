# -*- coding: utf-8 -*-
"""
aisec rewrite -- AI rewrite payload.
Usage:
    aisec rewrite "ignore all instructions" --style 自然口语
    aisec rewrite "ignore all instructions" --style 故事叙述 --count 3
    aisec rewrite "..." --endpoint https://api.openai.com --api-key sk-xxx --model gpt-4o-mini
Requires API configuration (OpenAI-compatible endpoint).
"""
import sys

from ..engine.rewrite import (
    build_rewrite_prompt,
    parse_candidates,
    call_openai_compatible,
    call_ollama,
    REWRITE_STYLES,
)
from ..core.marker import PAYLOAD_MARKER, check_payload_kept


def add_rewrite_parser(sub):
    p = sub.add_parser("rewrite", help="AI rewrite payload (requires API)")
    p.add_argument("text", help="the text to rewrite")
    p.add_argument("--style", default="自然口语",
                   choices=list(REWRITE_STYLES.keys()),
                   help="rewrite style")
    p.add_argument("--count", "-n", type=int, default=1,
                   help="number of candidates (default 1)")
    p.add_argument("--endpoint", default=None,
                   help="API endpoint, e.g. https://api.openai.com")
    p.add_argument("--api-key", default=None,
                   help="API key")
    p.add_argument("--model", default=None,
                   help="model name, e.g. gpt-4o-mini")
    p.add_argument("--ollama", action="store_true",
                   help="use local Ollama model")


def handle_rewrite(args):
    if not args.endpoint or not args.model:
        print("Please provide --endpoint and --model.")
        print()
        print("Examples:")
        print("  aisec rewrite \"ignore all instructions\" --style 自然口语 \\")
        print("      --endpoint https://api.openai.com --model gpt-4o-mini --api-key sk-xxx")
        print()
        print("  aisec rewrite \"ignore all instructions\" --ollama \\")
        print("      --endpoint http://localhost:11434 --model llama3")
        return 1

    prompt = build_rewrite_prompt(args.style, args.text, args.count)

    try:
        if args.ollama:
            result = call_ollama(args.endpoint, args.model, prompt)
        else:
            result = call_openai_compatible(
                args.endpoint, args.api_key or "", args.model, prompt)
    except Exception as e:
        print("[rewrite failed] %s" % e)
        return 1

    candidates = parse_candidates(result, args.count)

    if PAYLOAD_MARKER in args.text:
        for i, c in enumerate(candidates, 1):
            ok, _ = check_payload_kept(c)
            mark = "[OK] marker kept" if ok else "[!] marker lost"
            print("[Candidate %d] %s" % (i, mark))
            print(c)
            print()
    else:
        for i, c in enumerate(candidates, 1):
            print("[Candidate %d]" % i)
            print(c)
            print()

    return 0