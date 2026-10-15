# -*- coding: utf-8 -*-
"""Abstract base class for evaluators."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class EvalResult:
    """Single evaluation result."""
    name: str
    hit: bool = False
    detail: str = ""
    evidence: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "name": self.name,
            "hit": self.hit,
            "detail": self.detail,
            "evidence": self.evidence,
            "extra": self.extra,
        }


class Evaluator(ABC):
    """Base class for all evaluators."""

    name = "base"

    @abstractmethod
    def evaluate(self, payload, response_text):
        # type: (str, str) -> EvalResult
        """Evaluate one response. hit=True means attack succeeded / risk hit."""
        raise NotImplementedError