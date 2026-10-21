# -*- coding: utf-8 -*-
"""
aisec vuln -- pluggable CVE scanning for (traditional) AI application components.

Rules live in two drop-in data folders, so the open-source community can add
new CVEs without touching the code:

    src/aisecurity/data/fingerprints/*.yaml   identify a component
    src/aisecurity/data/vuln/*.yaml           detect a vulnerability

Usage:
    aisec vuln list [--kind fingerprints|vuln]
    aisec vuln show ID
    aisec vuln validate
    aisec vuln scan --target URL [--only CVE-xxx,...] [--component ID,...]
                    [--active] [--timeout N] [--format text|json] [-o FILE]
"""
import json

from ..vulnscan import (
    Finding, load_fingerprints, load_rules, load_vulns, scan, validate_rule,
)
from ..vulnscan.rules import FINGERPRINT_DIRNAME, VULN_DIRNAME

_SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def add_vuln_parser(sub):
    p = sub.add_parser("vuln", help="CVE / component scan (pluggable YAML rules)")
    sp = p.add_subparsers(dest="vuln_cmd")

    li = sp.add_parser("list", help="list fingerprints and/or CVE rules")
    li.add_argument("--kind", default="all",
                    choices=["all", FINGERPRINT_DIRNAME, VULN_DIRNAME])

    sh = sp.add_parser("show", help="show one rule in full")
    sh.add_argument("id", help="rule id (component id or CVE id)")

    sp.add_parser("validate", help="validate every rule file (for contributors)")

    sc = sp.add_parser("scan", help="fingerprint a target and match CVE rules")
    sc.add_argument("--target", required=True,
                    help="base URL of the target, e.g. http://localhost:11434")
    sc.add_argument("--only", default=None,
                    help="restrict to CVE ids, comma-separated")
    sc.add_argument("--component", default=None,
                    help="restrict to component ids, comma-separated")
    sc.add_argument("--active", action="store_true",
                    help="allow rules with check.mode=request to send a "
                         "confirmation request (skipped by default)")
    sc.add_argument("--timeout", type=int, default=10, help="request timeout (s)")
    sc.add_argument("--format", "-f", default="text", choices=["text", "json"])
    sc.add_argument("--output", "-o", default=None,
                    help="output file; omit to print to stdout")
    return p


def handle_vuln(args):
    if args.vuln_cmd == "list":
        return _handle_list(args)
    if args.vuln_cmd == "show":
        return _handle_show(args)
    if args.vuln_cmd == "validate":
        return _handle_validate()
    if args.vuln_cmd == "scan":
        return _handle_scan(args)
    print("Please specify: list / show ID / scan --target URL / validate")
    return 1


# ---------- list ----------
def _handle_list(args):
    if args.kind in ("all", FINGERPRINT_DIRNAME):
        fps = load_fingerprints()
        print("Component fingerprints (%d):" % len(fps))
        print("-" * 72)
        for r in fps:
            print("  %-16s %s" % (r["id"], r.get("name", "")))
        print()

    if args.kind in ("all", VULN_DIRNAME):
        vulns = load_vulns()
        print("CVE rules (%d):" % len(vulns))
        print("-" * 72)
        for r in vulns:
            print("  %-22s [%-8s] %-14s %s" % (
                r.get("id", ""), str(r.get("severity", "")).upper(),
                r.get("component", ""), r.get("title", "")))
        print()
    print("Rule folders:")
    print("  .../data/fingerprints/*.yaml   .../data/vuln/*.yaml")
    print("  (or set AISecurityTest_RULES_PATH to an external folder)")
    return 0


# ---------- show ----------
def _handle_show(args):
    rid = args.id
    for kind, rules in ((FINGERPRINT_DIRNAME, load_fingerprints()),
                        (VULN_DIRNAME, load_vulns())):
        for r in rules:
            if str(r.get("id", "")).lower() == rid.lower():
                print(json.dumps(r, ensure_ascii=False, indent=2))
                return 0
    print("Rule not found: %s" % rid)
    print("Use `aisec vuln list` to see available ids.")
    return 1


# ---------- validate ----------
def _handle_validate():
    problems = 0
    total = 0
    component_ids = {f.get("id") for f in load_fingerprints()}
    for kind in (FINGERPRINT_DIRNAME, VULN_DIRNAME):
        for r in load_rules(kind):
            total += 1
            errs = validate_rule(kind, r, component_ids)
            if errs:
                problems += 1
                print("[FAIL] %s (%s): %s" % (
                    r.get("id", "<no id>"), kind, "; ".join(errs)))
    print()
    if problems:
        print("%d/%d rules invalid." % (problems, total))
        return 1
    print("All %d rules validated." % total)
    return 0


# ---------- scan ----------
def _split(value):
    return [x.strip() for x in value.split(",") if x.strip()] if value else None


def _print_text(findings, detected, target, active):
    lines = ["=" * 66]
    lines.append("  AISecurityTest — CVE Scan")
    lines.append("  Target: %s" % target)
    lines.append("=" * 66)
    lines.append("")
    lines.append("Detected components (%d):" % len(detected))
    if detected:
        for d in detected:
            ver = (" v%s" % d["version"]) if d.get("version") else ""
            lines.append("  %-16s %s%s" % (d["id"], d["name"], ver))
    else:
        lines.append("  (none matched)")
    lines.append("")

    by_sev = {}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    lines.append("Findings: %d" % len(findings))
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        if sev in by_sev:
            lines.append("  %-10s %d" % (sev, len(by_sev[sev])))
    lines.append("")

    for f in findings:
        lines.append("[%s] %s  %s" % (f.severity, f.cve, f.title))
        if f.component:
            lines.append("       component: %s%s" % (
                f.component, (" v%s" % f.version) if f.version else ""))
        if f.detail:
            lines.append("       %s" % f.detail)
        if f.evidence:
            lines.append("       evidence: %s" % f.evidence[:140])
        if f.remediation:
            lines.append("       fix: %s" % f.remediation)
        if f.references:
            lines.append("       ref: %s" % f.references[0])
        lines.append("")
    if not active:
        lines.append("(request-mode rules were skipped; add --active to "
                     "allow confirmation requests)")
    return "\n".join(lines)


def _handle_scan(args):
    findings, detected = scan(
        target=args.target,
        timeout=args.timeout,
        only=_split(args.only),
        components=_split(args.component),
        active=args.active,
    )

    if args.format == "json":
        output = json.dumps({
            "target": args.target,
            "detected": detected,
            "findings": [f.to_dict() for f in findings],
        }, ensure_ascii=False, indent=2)
    else:
        output = _print_text(findings, detected, args.target, args.active)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print("CVE report written to %s (%d findings)" % (args.output, len(findings)))
    else:
        print(output)

    # Exit code for CI/CD integration (same convention as `aisec recon`).
    if any(f.severity == "CRITICAL" for f in findings):
        return 2
    if any(f.severity == "HIGH" for f in findings):
        return 1
    return 0
