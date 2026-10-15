# -*- coding: utf-8 -*-
"""Tests for the evaluators module."""
from aisecurity.evaluators import MarkerEvaluator, RegexEvaluator, build_evaluators
from aisecurity.core.marker import PAYLOAD_MARKER


def test_marker_evaluator_hit():
    ev = MarkerEvaluator()
    r = ev.evaluate("payload", "response contains " + PAYLOAD_MARKER)
    assert r.hit


def test_marker_evaluator_miss():
    ev = MarkerEvaluator()
    r = ev.evaluate("payload", "normal response")
    assert not r.hit


def test_regex_evaluator_phone():
    ev = RegexEvaluator()
    r = ev.evaluate("payload", "customer phone 13812345678")
    assert r.hit


def test_regex_evaluator_id_card():
    ev = RegexEvaluator()
    r = ev.evaluate("payload", "ID card 110105199003071234")
    assert r.hit


def test_regex_evaluator_api_key():
    ev = RegexEvaluator()
    r = ev.evaluate("payload", "key: sk-abcdef1234567890XYZ")
    assert r.hit


def test_regex_evaluator_clean():
    ev = RegexEvaluator()
    r = ev.evaluate("payload", "nice weather today")
    assert not r.hit


def test_build_evaluators():
    evs = build_evaluators("marker,regex")
    assert len(evs) == 2
    assert isinstance(evs[0], MarkerEvaluator)
    assert isinstance(evs[1], RegexEvaluator)