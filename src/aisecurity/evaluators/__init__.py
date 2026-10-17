# -*- coding: utf-8 -*-
"""Evaluator layer: determine whether an attack succeeded."""
from .base import Evaluator, EvalResult
from .marker_eval import MarkerEvaluator
from .regex_eval import RegexEvaluator
from .judge_eval import JudgeEvaluator

__all__ = [
    "Evaluator", "EvalResult",
    "MarkerEvaluator", "RegexEvaluator", "JudgeEvaluator",
    "build_evaluators",
]


def build_evaluators(names, judge_config=None):
    """Build evaluator instances from a list of names.

    Parameters
    ----------
    names : str | list[str]
        Comma-separated string or list. Accepted values:
        "marker", "regex", "judge". Unknown names are ignored.
    judge_config : dict | None
        Optional kwargs for JudgeEvaluator, e.g.
            {"endpoint": "https://api.openai.com",
             "api_key": "sk-...", "model": "gpt-4o-mini"}
        If "judge" is requested but judge_config is None (or lacks an
        endpoint), the judge evaluator is silently skipped. This keeps the
        judge fully optional: existing callers that never pass
        judge_config keep the original marker+regex behavior.

    Returns
    -------
    list[Evaluator]
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
        elif n in ("judge", "judge_eval"):
            # Only build the judge if the caller actually configured it.
            if judge_config and judge_config.get("endpoint"):
                out.append(JudgeEvaluator(**judge_config))
    return out