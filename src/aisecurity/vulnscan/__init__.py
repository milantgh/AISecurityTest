# -*- coding: utf-8 -*-
"""Pluggable CVE / vulnerability scan framework.

Two drop-in folders make the rule set extensible by the community without
touching code::

    data/fingerprints/*.yaml   # identify a component (vllm / comfyui / n8n ...)
    data/vuln/*.yaml           # detect a vulnerability in that component

Add rules from outside the package too, via the
``AISecurityTest_RULES_PATH`` environment variable.

Usage::

    from aisecurity.vulnscan import scan, load_fingerprints, load_vulns

    findings, detected = scan("http://localhost:11434", active=False)
    for f in findings:
        print(f.severity, f.cve, f.title)
"""
from __future__ import annotations

from .engine import Finding, fingerprint, scan
from .rules import (
    load_fingerprints,
    load_vulns,
    load_rules,
    rule_dirs,
    validate_rule,
)
from .version import parse_version, version_in_range

__all__ = [
    "Finding",
    "scan",
    "fingerprint",
    "load_fingerprints",
    "load_vulns",
    "load_rules",
    "rule_dirs",
    "validate_rule",
    "parse_version",
    "version_in_range",
]
