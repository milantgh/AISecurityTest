# -*- coding: utf-8 -*-
"""
aisec transform -- text transforms.
Usage:
    aisec transform "ignore safety rules" -m base64
    aisec transform "ignore safety rules" -m zero-width
    aisec transform "ignore safety rules" -m similar
    aisec transform --list  #list all methods
"""
from ..engine import transforms as T

# Method name -> function (with aliases)
METHODS = {
    "zero-width": T.add_zw,
    "zw": T.add_zw,
    "base64": T.to_b64,
    "b64": T.to_b64,
    "hex": T.to_hex,
    "unicode": T.to_uni,
    "uni": T.to_uni,
    "case": T.case_mix,
    "similar": T.similar,
    "html": T.wrap_html,
    "code": T.wrap_code,
    "chatml-sys": T.chatml_sys,
    "chatml-ast": T.chatml_ast,
    "llama": T.llama_inst,
    "strip": T.strip_ws,
    "collapse": T.collapse_ws,
    "trim": T.trim_lines,
}


def add_transform_parser(sub):
    p = sub.add_parser("transform", help="text transforms")
    p.add_argument("text", nargs="?", default=None,
                   help="the text to transform")
    p.add_argument("--method", "-m", default=None,
                   help="transform method (base64 / zero-width / similar / ...)")
    p.add_argument("--list", "-l", action="store_true",
                   help="list all available methods")


def handle_transform(args):
    if args.list:
        print("Available transform methods:")
        print()
        # Deduplicate (drop aliases)
        seen = set()
        for name, fn in METHODS.items():
            if id(fn) in seen:
                continue
            seen.add(id(fn))
            print("  %-15s" % name)
        print()
        print("Usage: aisec transform \"text\" -m <method>")
        return 0

    if not args.text:
        print("Please provide the text to transform.")
        print("Example: aisec transform \"ignore safety rules\" -m base64")
        return 1

    if not args.method:
        print("Please specify a transform method (-m).")
        print("Run `aisec transform --list` to see all methods.")
        return 1

    method = args.method.strip().lower()
    if method not in METHODS:
        print("Unknown method: %s" % method)
        print()
        print("Available methods:")
        seen = set()
        for name, fn in METHODS.items():
            if id(fn) in seen:
                continue
            seen.add(id(fn))
            print("  %s" % name)
        return 1

    fn = METHODS[method]
    result = fn(args.text)
    print(result)
    return 0