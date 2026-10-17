# -*- coding: utf-8 -*-
"""
Base class for attack probes (garak-style plugin framework).

A **probe** is a self-contained attack strategy that generates one or more
payloads programmatically.  Unlike YAML cases (which are static templates),
probes can compose payloads dynamically — building jailbreak chains,
encoding wrappers, multi-turn dialogues, etc.

Design mirrors garak's probe/detector separation:
* ``probe_name``      — unique identifier, used for CLI selection.
* ``description``      — human-readable summary.
* ``owasp_tags``       — OWASP LLM Top 10 tags this probe targets.
* ``primary_detector`` — the evaluator name used to judge compliance.
* ``extended_detectors`` — additional evaluator names to run.
* ``generate()``       — returns a list of payload strings.

Subclasses only need to set the class attributes and implement ``generate``.
"""
from __future__ import annotations

from typing import List, Optional


class BaseProbe:
    """Base class for all attack probes."""

    #: Unique probe name (used by CLI ``--probes``).
    probe_name: str = "base"

    #: One-line human-readable description.
    description: str = ""

    #: OWASP LLM Top 10 tags (e.g. ``["LLM01", "LLM02"]``).
    owasp_tags: List[str] = []

    #: Primary evaluator name (e.g. ``"marker"``, ``"regex"``, ``"judge"``).
    primary_detector: str = "marker"

    #: Additional evaluator names to run alongside the primary.
    extended_detectors: List[str] = []

    #: Risk level (严重 / 高 / 中-高 / 中 / 低).
    level: str = "高"

    def generate(self) -> List[str]:
        """Return a list of attack payload strings.

        Subclasses must override this.  Each string is sent to the target
        as a separate request.
        """
        raise NotImplementedError(
            "Probe %s must implement generate()" % self.probe_name)

    @property
    def all_detectors(self) -> List[str]:
        """Primary + extended detector names, de-duplicated."""
        seen = []
        for d in [self.primary_detector] + self.extended_detectors:
            if d and d not in seen:
                seen.append(d)
        return seen

    def __repr__(self) -> str:
        return "<Probe %s>" % self.probe_name
