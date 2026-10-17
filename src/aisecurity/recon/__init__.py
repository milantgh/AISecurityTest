# -*- coding: utf-8 -*-
"""
Endpoint reconnaissance module.

Inspired by vamp-llm-probe's Phase 1 (Endpoint Reconnaissance).

Performs network-level checks against an LLM inference endpoint WITHOUT
sending any attack payloads:

  * Model list exposure  — GET /v1/models (and /api/tags for Ollama)
  * Auth bypass           — inference without an API key
  * CORS misconfiguration — permissive Access-Control-Allow-Origin
  * Missing security headers
  * Rate limiting         — burst of parallel requests

All checks use only ``urllib`` (no extra dependencies), consistent with
the project's "minimal dependency" philosophy.

Usage:

    from aisecurity.recon import recon_endpoint
    findings = recon_endpoint("http://localhost:11434", api_key="")
    for f in findings:
        print(f.severity, f.id, f.title)
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReconFinding:
    """A single reconnaissance finding."""

    id: str
    title: str
    severity: str          # CRITICAL / HIGH / MEDIUM / LOW / INFO
    detail: str = ""
    evidence: str = ""
    owasp_tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "detail": self.detail,
            "evidence": self.evidence,
            "owasp_tags": self.owasp_tags,
        }


_SECURITY_HEADERS = [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", None),          # presence is enough
    ("Content-Security-Policy", None),
    ("Strict-Transport-Security", None),
    ("Referrer-Policy", None),
]


def _http_get(url: str, timeout: int = 10,
              headers: Optional[dict] = None) -> tuple:
    """GET *url*; return (status_code, headers_dict, body_text)."""
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers or {}), body
    except Exception as e:  # noqa: BLE001
        return 0, {}, str(e)


def _http_post_json(url: str, body: dict, timeout: int = 10,
                    headers: Optional[dict] = None) -> tuple:
    """POST JSON to *url*; return (status_code, headers_dict, body_text)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_txt = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body_txt
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers or {}), body_txt
    except Exception as e:  # noqa: BLE001
        return 0, {}, str(e)


def check_model_list(endpoint: str, timeout: int = 10) -> List[ReconFinding]:
    """Check if /v1/models or /api/tags is exposed without auth."""
    findings: List[ReconFinding] = []
    base = endpoint.rstrip("/")

    for path in ("/v1/models", "/api/tags"):
        status, headers, body = _http_get(base + path, timeout=timeout)
        if status == 200:
            findings.append(ReconFinding(
                id="LLM-001",
                title="Model list exposed without authentication",
                severity="CRITICAL",
                detail="GET %s returned HTTP 200" % path,
                evidence=body[:200],
                owasp_tags=["LLM06"],
            ))
            break
    return findings


def check_auth_bypass(endpoint: str, model: str = "",
                      timeout: int = 10) -> List[ReconFinding]:
    """Try an inference call WITHOUT an API key."""
    findings: List[ReconFinding] = []
    base = endpoint.rstrip("/")
    body = {"model": model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hi"}]}

    status, headers, resp_body = _http_post_json(
        base + "/v1/chat/completions", body, timeout=timeout)

    if status == 200:
        findings.append(ReconFinding(
            id="LLM-005",
            title="Inference endpoint accessible without API key",
            severity="CRITICAL",
            detail="POST /v1/chat/completions returned HTTP 200 without auth",
            evidence=resp_body[:200],
            owasp_tags=["LLM06"],
        ))
    elif status in (401, 403):
        findings.append(ReconFinding(
            id="LLM-005-ok",
            title="Auth required for inference endpoint",
            severity="INFO",
            detail="POST /v1/chat/completions returned HTTP %d" % status,
            owasp_tags=[],
        ))
    return findings


def check_cors(endpoint: str, timeout: int = 10) -> List[ReconFinding]:
    """Check for permissive CORS on the inference endpoint."""
    findings: List[ReconFinding] = []
    base = endpoint.rstrip("/")

    # Send a preflight-like request with an arbitrary Origin.
    status, headers, body = _http_get(
        base + "/v1/models", timeout=timeout,
        headers={"Origin": "https://evil.example.com"})

    acao = headers.get("Access-Control-Allow-Origin", "")
    if acao == "*":
        findings.append(ReconFinding(
            id="LLM-074",
            title="Permissive CORS on inference endpoint",
            severity="MEDIUM",
            detail="Access-Control-Allow-Origin: *",
            evidence="ACAO=%r" % acao,
            owasp_tags=["LLM06"],
        ))
    elif acao == "https://evil.example.com":
        findings.append(ReconFinding(
            id="LLM-074",
            title="CORS reflects arbitrary Origin",
            severity="HIGH",
            detail="Access-Control-Allow-Origin reflects request Origin",
            evidence="ACAO=%r" % acao,
            owasp_tags=["LLM06"],
        ))
    return findings


def check_security_headers(endpoint: str,
                           timeout: int = 10) -> List[ReconFinding]:
    """Check for missing HTTP security headers."""
    findings: List[ReconFinding] = []
    base = endpoint.rstrip("/")
    status, headers, body = _http_get(base + "/v1/models", timeout=timeout)

    # Only report when we actually received a response.
    if status == 0:
        return findings

    missing = []
    for name, expected_value in _SECURITY_HEADERS:
        value = headers.get(name)
        if value is None:
            missing.append(name)
        elif expected_value and expected_value not in value:
            missing.append("%s (got %r)" % (name, value))

    if missing:
        findings.append(ReconFinding(
            id="LLM-075",
            title="Missing HTTP security headers",
            severity="LOW",
            detail="Missing: %s" % ", ".join(missing),
            evidence="present headers: %s" % ", ".join(sorted(headers.keys())),
            owasp_tags=["LLM06"],
        ))
    return findings


def check_rate_limit(endpoint: str, api_key: str = "", model: str = "",
                     timeout: int = 10, count: int = 10) -> List[ReconFinding]:
    """Send a burst of requests to test rate limiting."""
    findings: List[ReconFinding] = []
    base = endpoint.rstrip("/")
    url = base + "/v1/chat/completions"
    body = {"model": model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hi"}]}

    hdrs = {}
    if api_key:
        hdrs["Authorization"] = "Bearer %s" % api_key

    statuses = []
    t0 = time.time()
    for _ in range(count):
        status, _, _ = _http_post_json(url, body, timeout=timeout, headers=hdrs)
        statuses.append(status)
    elapsed = time.time() - t0

    success = sum(1 for s in statuses if s == 200)
    if success == count:
        findings.append(ReconFinding(
            id="LLM-070",
            title="No rate limiting on inference endpoint",
            severity="HIGH",
            detail="%d/%d requests succeeded in %.1fs without 429"
                   % (success, count, elapsed),
            evidence="statuses: %s" % statuses,
            owasp_tags=["LLM10", "AGENT09"],
        ))
    else:
        findings.append(ReconFinding(
            id="LLM-070-ok",
            title="Rate limiting active",
            severity="INFO",
            detail="%d/%d requests succeeded (%d blocked)"
                   % (success, count, count - success),
            owasp_tags=[],
        ))
    return findings


def recon_endpoint(endpoint: str, api_key: str = "", model: str = "",
                   timeout: int = 10,
                   run_rate_limit: bool = False,
                   rate_limit_count: int = 10) -> List[ReconFinding]:
    """Run all reconnaissance checks against *endpoint*.

    Parameters
    ----------
    endpoint : str
        Base URL of the inference endpoint (e.g. ``http://localhost:11434``).
    api_key : str
        Optional API key for the rate-limit check.
    model : str
        Model name for inference checks.
    run_rate_limit : bool
        Whether to run the (slightly noisy) rate-limit burst test.
    """
    findings: List[ReconFinding] = []
    findings += check_model_list(endpoint, timeout)
    findings += check_auth_bypass(endpoint, model, timeout)
    findings += check_cors(endpoint, timeout)
    findings += check_security_headers(endpoint, timeout)
    if run_rate_limit:
        findings += check_rate_limit(endpoint, api_key, model, timeout,
                                     rate_limit_count)
    return findings


__all__ = [
    "ReconFinding", "recon_endpoint",
    "check_model_list", "check_auth_bypass", "check_cors",
    "check_security_headers", "check_rate_limit",
]
