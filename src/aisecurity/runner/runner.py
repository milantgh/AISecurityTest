# -*- coding: utf-8 -*-
"""Execution orchestration: case -> payload -> target -> evaluate."""
from typing import List, Optional

from ..core.registry import CASE_LIB, CATEGORIES
from ..engine.payload import gen_by_case
from ..probes import get_probe
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

    def run_probe(self, probe_name: str) -> List[CaseResult]:
        """Run a probe by name.

        A probe generates payloads programmatically (unlike YAML cases
        which are static templates).  The probe's own detector list is
        used; otherwise the runner's default evaluators are applied.
        """
        probe = get_probe(probe_name)
        if probe is None:
            raise KeyError("Unknown probe: %s" % probe_name)

        payloads = probe.generate()
        # If the probe declares detectors, use them; otherwise fall back
        # to the runner's default evaluators.
        evaluators = self.evaluators

        results = []
        for p in payloads:
            try:
                resp = self.target.send(p)
                evals = [ev.evaluate(p, resp.text) for ev in evaluators]
                results.append(CaseResult(
                    case_id="probe:%s" % probe_name,
                    payload=p,
                    response_text=resp.text,
                    eval_results=evals,
                    latency_ms=resp.latency_ms,
                ))
            except Exception as e:
                results.append(CaseResult(
                    case_id="probe:%s" % probe_name,
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