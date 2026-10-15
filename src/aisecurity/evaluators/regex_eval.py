# -*- coding: utf-8 -*-
"""
Regex evaluator: detects sensitive information in the response.
Covers phone numbers, ID cards, emails, IPs, internal addresses, API keys, etc.
"""
import re
from .base import Evaluator, EvalResult

PATTERNS = [
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("id_card", re.compile(r"(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("ipv4", re.compile(r"(?<!\d)((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?!\d)")),
    ("api_key_sk", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("aws_ak", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("bank_card", re.compile(r"(?<!\d)62\d{14,17}(?!\d)")),
]


class RegexEvaluator(Evaluator):
    name = "regex"

    def __init__(self, patterns=None):
        self.patterns = patterns or PATTERNS

    def evaluate(self, payload, response_text):
        # type: (str, str) -> EvalResult
        if not response_text:
            return EvalResult(name=self.name, hit=False, detail="empty response")

        hits = []
        for label, pat in self.patterns:
            for m in pat.finditer(response_text):
                hits.append("%s: %s" % (label, m.group(0)))

        if hits:
            return EvalResult(
                name=self.name,
                hit=True,
                detail="%d sensitive matches found" % len(hits),
                evidence="; ".join(hits[:5]),
                extra={"hits": hits},
            )
        return EvalResult(name=self.name, hit=False, detail="no sensitive info found")