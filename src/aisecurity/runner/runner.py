# -*- coding: utf-8 -*-
"""Execution orchestration: case -> payload -> target -> evaluate."""
from typing import List

from ..core.registry import CASE_LIB, CATEGORIES
from ..engine.payload import gen_by_case
from .result import CaseResult


class Runner:
    def __init__(self, target, evaluators=None):
        self.target = target
        self.evaluators = evaluators or []

    def run_case(self, case_id):
        # type: (str) -> List[CaseResult]
        if case_id not in CASE_LIB:
            raise KeyError("Unknown case: %s" % case_id)

        payloads = gen_by_case(case_id)
        results = []
        for p in payloads:
            try:
                resp = self.target.send(p)
                evals = [ev.evaluate(p, resp.text) for ev in self.evaluators]
                results.append(CaseResult(
                    case_id=case_id,
                    payload=p,
                    response_text=resp.text,
                    eval_results=evals,
                    latency_ms=resp.latency_ms,
                ))
            except Exception as e:
                results.append(CaseResult(
                    case_id=case_id,
                    payload=p,
                    error="%s: %s" % (type(e).__name__, e),
                ))
        return results

    def run_category(self, category):
        # type: (str) -> List[CaseResult]
        out = []
        for cid in CATEGORIES.get(category, []):
            out.extend(self.run_case(cid))
        return out

    def run_all(self):
        # type: () -> List[CaseResult]
        out = []
        for cid in CASE_LIB:
            out.extend(self.run_case(cid))
        return out