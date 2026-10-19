# -*- coding: utf-8 -*-
"""Fingerprint + CVE scan engine.

Data-driven: everything is decided by the YAML rule files, so adding a new
CVE is a data change, never a code change.

Two-phase flow::

    1. fingerprint()  -> probe the target with each fingerprint rule and
                         identify the component (and its version, if exposed)
    2. scan()         -> for every vuln rule whose component was detected and
                         whose ``affected`` range matches the version, report
                         a finding. Rules with ``check.mode: request`` send a
                         confirmation request, but only when *active* is on.

Only ``urllib`` is used (no extra dependencies).
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .rules import load_fingerprints, load_vulns
from .version import version_in_range


@dataclass
class Finding:
    """A single vulnerability finding."""

    cve: str
    title: str
    severity: str
    component: str = ""
    version: str = ""
    detail: str = ""
    evidence: str = ""
    references: List[str] = field(default_factory=list)
    remediation: str = ""
    owasp_tags: List[str] = field(default_factory=list)
    source: str = ""

    def to_dict(self):
        return {
            "cve": self.cve,
            "title": self.title,
            "severity": self.severity,
            "component": self.component,
            "version": self.version,
            "detail": self.detail,
            "evidence": self.evidence,
            "references": self.references,
            "remediation": self.remediation,
            "owasp_tags": self.owasp_tags,
            "source": self.source,
        }


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def _request(method: str, url: str, timeout: int = 10,
             headers: Optional[dict] = None,
             body=None) -> Tuple[int, Dict[str, str], str]:
    """Perform one HTTP request; return (status, headers, body).

    Never raises: network failures yield status ``0`` with the error text
    as the body, so a scan against an unreachable target degrades cleanly.
    """
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) \
            else json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method.upper())
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    if data is not None and not any(
            k.lower() == "content-type" for k in (headers or {})):
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), \
                resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers or {}), body_txt
    except Exception as e:  # noqa: BLE001
        return 0, {}, str(e)


def _safe_search(pattern, text, flags=0):
    """``re.search`` that never raises on a malformed rule regex.

    Community-contributed rules may contain a bad pattern; that must
    degrade to "no match" instead of crashing the scan.
    """
    try:
        return re.search(pattern, text, flags)
    except re.error:
        return None


def _status_ok(spec, status: int) -> bool:
    if spec is None:
        return True
    if isinstance(spec, (list, tuple, set)):
        return status in spec
    return status == spec


def _match(cond: dict, status: int, headers: Dict[str, str],
           body: str) -> bool:
    """Evaluate one fingerprint/check condition against a response."""
    if not _status_ok(cond.get("status"), status):
        return False

    contains = cond.get("body_contains")
    if contains and contains not in body:
        return False

    regex = cond.get("body_regex")
    if regex and not _safe_search(regex, body, re.S):
        return False

    for name, needle in (cond.get("header_contains") or {}).items():
        if needle not in headers.get(name, ""):
            return False

    for name, pattern in (cond.get("header_regex") or {}).items():
        if not _safe_search(pattern, headers.get(name, "")):
            return False

    return True


# --------------------------------------------------------------------------
# Fingerprinting
# --------------------------------------------------------------------------
def _probe_version(spec: Optional[dict], base: str, timeout: int,
                   headers: Dict[str, str], body: str) -> str:
    """Extract a version string.

    If the rule declares ``version.path``, a dedicated request is sent to
    that path (many components expose the version on an endpoint that is
    not the one used for identification, e.g. Ollama's ``/api/version``).
    Otherwise the already-fetched response is reused.
    """
    if not isinstance(spec, dict):
        return ""
    if spec.get("path"):
        _, headers, body = _request(
            spec.get("method", "GET"), base + spec["path"], timeout=timeout,
            headers=spec.get("headers"))

    patterns = []
    if spec.get("body_regex"):
        patterns.append((spec["body_regex"], body))
    for name, pattern in (spec.get("header_regex") or {}).items():
        patterns.append((pattern, headers.get(name, "")))
    if spec.get("header") and spec.get("value_regex"):
        patterns.append((spec["value_regex"], headers.get(spec["header"], "")))

    for pattern, text in patterns:
        m = _safe_search(pattern, text)
        if m:
            return m.group(1) if m.groups() else m.group(0)
    return ""


def fingerprint(target: str, timeout: int = 10,
                fingerprints: Optional[List[dict]] = None) -> List[dict]:
    """Identify components running on *target*.

    Returns a list of ``{"id", "name", "version", "evidence", "source"}``
    dicts, one per matched fingerprint rule.
    """
    rules = fingerprints if fingerprints is not None else load_fingerprints()
    base = target.rstrip("/")
    detected: List[dict] = []

    for rule in rules:
        for cond in (rule.get("match") or {}).get("any", []):
            path = cond.get("path", "/")
            status, headers, body = _request(
                cond.get("method", "GET"), base + path, timeout=timeout,
                headers=cond.get("headers"))
            if not _match(cond, status, headers, body):
                continue
            detected.append({
                "id": rule["id"],
                "name": rule.get("name", rule["id"]),
                "version": _probe_version(rule.get("version"), base, timeout,
                                          headers, body),
                "evidence": "GET %s -> HTTP %s" % (path, status),
                "source": rule.get("_source", ""),
            })
            break
    return detected


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------
def scan(target: str, timeout: int = 10, only: Optional[List[str]] = None,
         components: Optional[List[str]] = None, active: bool = False,
         fingerprints: Optional[List[dict]] = None,
         vulns: Optional[List[dict]] = None) -> Tuple[List[Finding], List[dict]]:
    """Fingerprint *target*, then evaluate every applicable CVE rule.

    Parameters
    ----------
    only : list[str] | None
        Restrict to these CVE ids (case-insensitive).
    components : list[str] | None
        Restrict to these component ids.
    active : bool
        Allow rules with ``check.mode: request`` to send their confirmation
        request. When False such rules are skipped (safe default).

    Returns
    -------
    (findings, detected)
    """
    detected = fingerprint(target, timeout, fingerprints)
    by_id = {d["id"]: d for d in detected}

    only_set = {o.lower() for o in only} if only else None
    comp_set = set(components) if components else None
    rules = vulns if vulns is not None else load_vulns()

    findings: List[Finding] = []
    for rule in rules:
        comp = rule.get("component", "")
        if comp not in by_id:
            continue
        if comp_set and comp not in comp_set:
            continue
        if only_set and str(rule.get("id", "")).lower() not in only_set:
            continue

        info = by_id[comp]
        version = info.get("version", "")
        if not version_in_range(version, rule.get("affected", "*")):
            continue

        check = rule.get("check") or {}
        mode = check.get("mode", "version")
        evidence = info.get("evidence", "")

        if mode == "request":
            if not active:
                continue
            status, headers, body = _request(
                check.get("method", "GET"), target.rstrip("/")
                + check.get("path", "/"), timeout=timeout,
                headers=check.get("headers"), body=check.get("body"))
            match_spec = check.get("match", {})
            if not _match(match_spec, status, headers, body):
                continue
            evidence = "%s %s -> HTTP %d" % (
                check.get("method", "GET"), check.get("path", "/"), status)

        findings.append(Finding(
            cve=rule.get("id", ""),
            title=rule.get("title", ""),
            severity=str(rule.get("severity", "INFO")).upper(),
            component=comp,
            version=version,
            detail=rule.get("description", ""),
            evidence=evidence,
            references=list(rule.get("references", [])),
            remediation=rule.get("remediation", ""),
            owasp_tags=list(rule.get("owasp_tags", [])),
            source=rule.get("_source", ""),
        ))

    _order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    findings.sort(key=lambda f: _order.get(f.severity, 9))
    return findings, detected
