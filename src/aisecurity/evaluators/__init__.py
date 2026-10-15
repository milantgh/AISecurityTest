# -*- coding: utf-8 -*-
"""Evaluator layer: determine whether an attack succeeded."""
from .base import Evaluator, EvalResult
from .marker_eval import MarkerEvaluator
from .regex_eval import RegexEvaluator

__all__ = ["Evaluator", "EvalResult", "MarkerEvaluator", "RegexEvaluator"]


def build_evaluators(names):
    """Build evaluator instances from a list of names.

    names: ["marker", "regex"] or ["marker,regex"]
    """
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    out = []
    for n in names or []:
        n = n.lower()
        if n in ("marker", "marker_eval"):
            out.append(MarkerEvaluator())
        elif n in ("regex", "regex_eval"):
            out.append(RegexEvaluator())
    return out