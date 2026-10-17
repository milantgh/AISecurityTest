# -*- coding: utf-8 -*-
"""Integration tests for the Runner orchestration pipeline.

These tests use a FakeTarget so no network is involved. They verify that
the runner wires case -> payload -> target -> evaluator correctly.

Note on assertions:
    We deliberately avoid hard-coding the number of payloads per case.
    That number depends on the heuristic step extractor in
    engine/payload.py and can change when a case's steps are edited.
    Instead we assert the lower bound (>= 1) and, where useful, that a
    specific keyword appears in at least one payload.
"""
from aisecurity.targets.base import Target, TargetResponse
from aisecurity.runner.runner import Runner
from aisecurity.evaluators import build_evaluators
from aisecurity.core.marker import PAYLOAD_MARKER


class FakeTarget(Target):
    """Fake target: offline, returns a preset text."""

    name = "fake"

    def __init__(self, text):
        self.text = text

    def send(self, payload, **kwargs):
        return TargetResponse(text=self.text, latency_ms=10)


def test_runner_miss():
    """No marker -> all miss."""
    runner = Runner(FakeTarget("ignore"), build_evaluators("marker,regex"))
    results = runner.run_case("PI-001")
    assert len(results) >= 1
    assert all(not r.success for r in results)
    # Sanity: at least one payload must carry the injection keyword.
    assert any("忽略" in r.payload for r in results)


def test_runner_marker_hit():
    """With marker -> all hit."""
    runner = Runner(
        FakeTarget("response " + PAYLOAD_MARKER),
        build_evaluators("marker,regex"),
    )
    results = runner.run_case("PI-001")
    assert len(results) >= 1
    assert all(r.success for r in results)


def test_runner_regex_hit():
    """Contains PII -> regex hits."""
    runner = Runner(
        FakeTarget("customer phone 13812345678, ID card 110105199003071234"),
        build_evaluators("marker,regex"),
    )
    results = runner.run_case("PI-002")
    assert len(results) >= 1
    assert all(r.success for r in results)
    regex_results = [
        er for r in results for er in r.eval_results if er.name == "regex"
    ]
    assert regex_results
    assert all(er.hit for er in regex_results)


def test_runner_all_cases_runnable():
    """All cases should be runnable with a fake target."""
    runner = Runner(FakeTarget("test response"), build_evaluators("marker"))
    from aisecurity.core.registry import CASE_LIB
    for cid in CASE_LIB:
        results = runner.run_case(cid)
        assert len(results) >= 1, "Case %s produced no payload" % cid