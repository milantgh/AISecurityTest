# -*- coding: utf-8 -*-
"""Single-run result object."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class CaseResult:
    case_id: str
    payload: str
    response_text: str = ""
    eval_results: List[Any] = field(default_factory=list)
    latency_ms: int = 0
    error: str = ""

    @property
    def success(self):
        """Attack succeeds if any evaluator hits."""
        return any(r.hit for r in self.eval_results)

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "payload": self.payload,
            "response_text": self.response_text,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "success": self.success,
            "eval_results": [r.to_dict() for r in self.eval_results],
        }