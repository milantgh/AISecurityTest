# -*- coding: utf-8 -*-
"""
aisec recon -- endpoint reconnaissance (no attack payloads).

Inspired by vamp-llm-probe Phase 1 (Endpoint Reconnaissance).

Usage:
    aisec recon --endpoint URL [--api-key KEY] [--model MODEL]
                [--timeout N] [--rate-limit] [--rate-count N]
                [--format text|json] [-o FILE]

Checks performed:
  * Model list exposure      (/v1/models, /api/tags)
  * Auth bypass              (inference without API key)
  * CORS misconfiguration
  * Missing security headers
  * Rate limiting            (optional burst test)
"""
import json
import sys

from ..recon import recon_endpoint, ReconFinding


def add_recon_parser(sub):
    p = sub.add_parser("recon", help="endpoint reconnaissance (no payloads)")
    p.add_argument("--endpoint", required=True,
                   help="base URL of the inference endpoint")
    p.add_argument("--api-key", default="", help="API key (for rate-limit test)")
    p.add_argument("--model", default="gpt-4o-mini", help="model name")
    p.add_argument("--timeout", type=int, default=10, help="request timeout (s)")
    p.add_argument("--rate-limit", action="store_true",
                   help="run the rate-limit burst test")
    p.add_argument("--rate-count", type=int, default=10,
                   help="number of requests for the rate-limit test")
    p.add_argument("--format", "-f", default="text",
                   choices=["text", "json"])
    p.add_argument("--output", "-o", default=None,
                   help="output file; omit to print to stdout")
    return p


def _print_text(findings, endpoint):
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    findings = sorted(findings, key=lambda f: sev_order.get(f.severity, 9))

    lines = []
    lines.append("=" * 64)
    lines.append("  AISecurityTest — Endpoint Reconnaissance")
    lines.append("  Target: %s" % endpoint)
    lines.append("=" * 64)

    by_sev = {}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)

    lines.append("")
    lines.append("Findings: %d" % len(findings))
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        if sev in by_sev:
            lines.append("  %-10s %d" % (sev, len(by_sev[sev])))
    lines.append("")

    for f in findings:
        lines.append("[%s] %s  %s" % (f.severity, f.id, f.title))
        if f.detail:
            lines.append("       %s" % f.detail)
        if f.evidence:
            lines.append("       evidence: %s" % f.evidence[:120])
        if f.owasp_tags:
            lines.append("       owasp: %s" % ", ".join(f.owasp_tags))
        lines.append("")
    return "\n".join(lines)


def handle_recon(args):
    findings = recon_endpoint(
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
        timeout=args.timeout,
        run_rate_limit=args.rate_limit,
        rate_limit_count=args.rate_count,
    )

    if args.format == "json":
        output = json.dumps(
            {"endpoint": args.endpoint,
             "findings": [f.to_dict() for f in findings]},
            ensure_ascii=False, indent=2)
    else:
        output = _print_text(findings, args.endpoint)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print("Recon report written to %s (%d findings)"
              % (args.output, len(findings)))
    else:
        print(output)

    # Exit code for CI/CD integration (vamp-llm-probe style).
    has_critical = any(f.severity == "CRITICAL" for f in findings)
    has_high = any(f.severity == "HIGH" for f in findings)
    if has_critical:
        return 2
    if has_high:
        return 1
    return 0
