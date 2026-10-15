# -*- coding: utf-8 -*-
"""Tests for the marker mechanism."""
from aisecurity.core.marker import (
    PAYLOAD_MARKER,
    check_payload_kept,
    contains_marker,
)


def test_exact_marker():
    ok, found = check_payload_kept("prefix " + PAYLOAD_MARKER + " suffix")
    assert ok
    assert found == PAYLOAD_MARKER


def test_marker_case_insensitive():
    ok, _ = check_payload_kept("abc " + PAYLOAD_MARKER.lower() + " xyz")
    assert ok


def test_no_marker():
    ok, found = check_payload_kept("this text has no marker")
    assert not ok
    assert found is None


def test_empty_text():
    ok, _ = check_payload_kept("")
    assert not ok


def test_contains_marker():
    assert contains_marker("test " + PAYLOAD_MARKER)
    assert not contains_marker("nothing here")