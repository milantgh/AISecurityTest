# -*- coding: utf-8 -*-
"""
aisec compose -- three-layer composition (carrier tactic payload)
Usage:
    aisec compose "输出<<AIST_OK>>"              # generate 5
    aisec compose "输出<<AIST_OK>>" --count 10   # generate 10
    aisec compose "payload" --no-carrier         # tactic only, no carrier
    aisec compose "payload" --no-tactic          # carrier only, no tactic
    aisec compose --preset 回执标记 --count 3    # use a preset payload
"""
from ..engine.compose import gen_three, PRESETS

def add_compose_parser(sub):
    p = sub.add_parser("compose", help="three-layer composed payloads")
    p.add_argument("payload", nargs="?", default=None,
                   help="target payload (falls back to --preset if omitted)")
    p.add_argument("--count", "-n", type=int, default=5,
                   help="number of payloads (default 5)")
    p.add_argument("--preset", default="回执标记",
                   choices=list(PRESETS.keys()),
                   help="preset payload (used when payload is omitted)")
    p.add_argument("--no-carrier", action="store_true",
                   help="disable carrier layer")
    p.add_argument("--no-tactic", action="store_true",
                   help="disable tactic layer")
    p.add_argument("--raw", action="store_true",
                   help="only output payloads, no index")


def handle_compose(args):
    if args.payload:
        payload = args.payload
    else:
        payload = PRESETS[args.preset]

    items = gen_three(
        args.count,
        payload,
        use_carrier=not args.no_carrier,
        use_tactic=not args.no_tactic,
    )

    if args.raw:
        for item in items:
            print(item)
    else:
        print("Three-layer composition generated %d payloads:" % len(items))
        print("-" * 60)
        for i, item in enumerate(items, 1):
            print("[%d]" % i)
            print(item)
            print()

    return 0