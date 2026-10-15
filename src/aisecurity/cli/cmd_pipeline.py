# -*- coding: utf-8 -*-
"""
aisec pipeline -- one-shot pipeline: generate -> rewrite -> transform -> verify.
Usage:
    aisec pipeline PI-001 --transform base64
    aisec pipeline PI-001 --transform zero-width --count 3
"""
from ..core.registry import CASE_LIB
from ..engine.payload import gen_by_case
from ..engine import transforms as T
from ..core.marker import check_payload_kept

TRANSFORM_MAP = {
    "base64": T.to_b64,
    "zero-width": T.add_zw,
    "zw": T.add_zw,
    "hex": T.to_hex,
    "unicode": T.to_uni,
    "case": T.case_mix,
    "similar": T.similar,
    "none": None,
}


def add_pipeline_parser(sub):
    p = sub.add_parser("pipeline",
                       help="one-shot pipeline: generate->rewrite->transform->verify")
    p.add_argument("case_id", help="case ID, e.g. PI-001")
    p.add_argument("--transform", "-t", default="none",
                   choices=list(TRANSFORM_MAP.keys()),
                   help="text transform method (default: none)")
    p.add_argument("--count", "-n", type=int, default=0,
                   help="limit number of payloads (0 = all)")
    p.add_argument("--show-original", action="store_true",
                   help="show the original payload before transform")


def handle_pipeline(args):
    cid = args.case_id.strip()
    if cid not in CASE_LIB:
        print("Unknown case: %s" % cid)
        return 1

    payloads = gen_by_case(cid)
    if args.count > 0:
        payloads = payloads[:args.count]

    fn = TRANSFORM_MAP.get(args.transform)

    print("Pipeline: %s -> %s (%d payloads)"
          % (cid, args.transform, len(payloads)))
    print("=" * 60)

    for i, orig in enumerate(payloads, 1):
        try:
            result = fn(orig) if fn else orig
        except Exception as e:
            print("[%d] transform failed: %s" % (i, e))
            continue

        ok, _ = check_payload_kept(result)
        mark = ""
        if "<<AIST_OK>>" in orig:
            mark = "  [OK] marker kept" if ok else "  [!] marker lost"

        print("[%d]%s" % (i, mark))
        if args.show_original:
            print("original: %s" % orig[:120])
            print("transformed: %s" % result[:120])
        else:
            print(result)
        print()

    return 0