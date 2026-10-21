# -*- coding: utf-8 -*-
"""Loading and discovery of CVE rules and component fingerprints.

Rules are plain YAML files, so the community can add new CVEs by dropping
a file into the data folder -- no code changes required::

    data/fingerprints/*.yaml   identify a component (vllm / comfyui / n8n ...)
    data/vuln/*.yaml           detect a vulnerability in a component

Additional rule directories can be supplied through the
``AISecurityTest_RULES_PATH`` environment variable (colon-separated). Each
entry is either a directory that itself contains ``fingerprints/`` and/or
``vuln/`` sub-folders, or a directory holding the rule files directly.

Files whose name starts with ``_`` (e.g. ``_template.yaml``) are ignored.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

FINGERPRINT_DIRNAME = "fingerprints"
VULN_DIRNAME = "vuln"
ENV_RULES_PATH = "AISecurityTest_RULES_PATH"

_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")


def _package_data_dir() -> Optional[Path]:
    """Return ``<installed package>/data/`` if it exists."""
    try:
        import aisecurity
        d = Path(aisecurity.__file__).resolve().parent / "data"
        if d.is_dir():
            return d
    except Exception:
        pass
    d = Path(__file__).resolve().parent.parent / "data"
    return d if d.is_dir() else None


def rule_dirs(kind: str) -> List[Path]:
    """Return the directories searched for rules of *kind*.

    *kind* is ``"fingerprints"`` or ``"vuln"``. Package data comes first,
    then any directory listed in ``AISecurityTest_RULES_PATH``.
    """
    assert kind in (FINGERPRINT_DIRNAME, VULN_DIRNAME)
    dirs: List[Path] = []

    data = _package_data_dir()
    if data is not None and (data / kind).is_dir():
        dirs.append(data / kind)

    for entry in os.environ.get(ENV_RULES_PATH, "").split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        p = Path(entry)
        if not p.is_dir():
            continue
        if (p / kind).is_dir():          # containing fingerprints/ + vuln/
            dirs.append(p / kind)
        else:                            # holding rule files directly
            dirs.append(p)
    return dirs


def load_rules(kind: str) -> List[Dict]:
    """Load every rule file of *kind*, tagging each with ``_source``."""
    rules: List[Dict] = []
    seen: set = set()
    for directory in rule_dirs(kind):
        for path in sorted(directory.glob("*.y*ml")):
            if path.name.startswith("_"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
            except Exception as e:  # noqa: BLE001
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to load rule %s: %s", path.name, e)
                continue
            if not isinstance(data, dict) or "id" not in data:
                continue
            # The same CVE can affect several products; keep one rule per
            # (id, component) pair instead of dropping every copy after the
            # first one.
            key = (data["id"], data.get("component")) \
                if kind == VULN_DIRNAME else data["id"]
            if key in seen:
                continue
            seen.add(key)
            data["_source"] = str(path)
            rules.append(data)
    return rules


def load_fingerprints() -> List[Dict]:
    return load_rules(FINGERPRINT_DIRNAME)


def load_vulns() -> List[Dict]:
    return load_rules(VULN_DIRNAME)


def _check_regexes(patterns, where: str, errors: List[str]) -> None:
    """Flag any pattern that does not compile, so bad rules are caught early."""
    for p in patterns:
        if not isinstance(p, str) or not p:
            continue
        try:
            re.compile(p)
        except re.error as e:
            errors.append("invalid regex in %s: %r (%s)" % (where, p, e))


def validate_rule(kind: str, rule: Dict,
                  component_ids: Optional[set] = None) -> List[str]:
    """Return a list of schema problems (empty list == valid).

    *component_ids* lets callers that validate many rules reuse a single
    fingerprint index instead of reloading every fingerprint per rule.
    """
    errors: List[str] = []
    if not isinstance(rule, dict):
        return ["rule is not a mapping"]
    rid = rule.get("id")
    if not rid:
        errors.append("missing 'id'")

    if kind == FINGERPRINT_DIRNAME:
        if not rule.get("name"):
            errors.append("missing 'name'")
        match = rule.get("match")
        if not isinstance(match, dict) or not match.get("any"):
            errors.append("'match.any' must be a non-empty list")
        else:
            for i, cond in enumerate(match["any"]):
                if not isinstance(cond, dict):
                    errors.append("match.any[%d] is not a mapping" % i)
                    continue
                _check_regexes([cond.get("body_regex")],
                               "match.any[%d].body_regex" % i, errors)
                _check_regexes(list((cond.get("header_regex") or {}).values()),
                               "match.any[%d].header_regex" % i, errors)
        ver = rule.get("version")
        if isinstance(ver, dict):
            _check_regexes([ver.get("body_regex"), ver.get("value_regex")],
                           "version", errors)
            _check_regexes(list((ver.get("header_regex") or {}).values()),
                           "version.header_regex", errors)
    elif kind == VULN_DIRNAME:
        if not rule.get("title"):
            errors.append("missing 'title'")
        comp = rule.get("component")
        if component_ids is None:
            component_ids = {f.get("id") for f in load_fingerprints()}
        if not comp or comp not in component_ids:
            errors.append(
                "unknown component %r (see `aisec vuln list --kind fingerprints`)"
                % comp)
        sev = str(rule.get("severity", "")).upper()
        if sev not in _SEVERITIES:
            errors.append("severity must be one of %s" % ", ".join(_SEVERITIES))
        check = rule.get("check")
        if check is not None:
            if not isinstance(check, dict):
                errors.append("'check' must be a mapping")
            else:
                if check.get("mode", "version") not in ("version", "request"):
                    errors.append("check.mode must be 'version' or 'request'")
                cm = check.get("match") or {}
                if isinstance(cm, dict):
                    _check_regexes([cm.get("body_regex")],
                                   "check.match.body_regex", errors)
                    _check_regexes(
                        list((cm.get("header_regex") or {}).values()),
                        "check.match.header_regex", errors)
    return errors
