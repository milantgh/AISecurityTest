# -*- coding: utf-8 -*-
"""Marker evaluator: checks whether the marker appears in the response."""
from ..core.marker import PAYLOAD_MARKER, check_payload_kept
from .base import Evaluator, EvalResult


class MarkerEvaluator(Evaluator):
    name = "marker"

    def evaluate(self, payload, response_text):
        # type: (str, str) -> EvalResult
        if not response_text:
            return EvalResult(name=self.name, hit=False, detail="empty response")

        ok, found = check_payload_kept(response_text, PAYLOAD_MARKER)
        return EvalResult(
            name=self.name,
            hit=ok,
            detail=("marker reproduced: %s" % (found or PAYLOAD_MARKER)) if ok
                   else "marker not reproduced",
            evidence=found or "",
        )