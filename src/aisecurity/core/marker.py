# -*- coding: utf-8 -*-
"""
Marker mechanism.
Used to verify whether an attack payload was preserved after rewriting or transformation.
"""
from typing import Optional, Tuple

PAYLOAD_MARKER = "<<AIST_OK>>"
PAYLOAD_MARKERS = (
    PAYLOAD_MARKER,
    PAYLOAD_MARKER.lower(),
    PAYLOAD_MARKER.capitalize(),
)


def check_payload_kept(text: str, marker: str = PAYLOAD_MARKER) -> Tuple[bool, Optional[str]]:
    """Check whether the target marker is preserved in the text.

    Returns:
        (kept, matched marker string or None)
    """
    if not text:
        return False, None
    for m in (marker, *PAYLOAD_MARKERS):
        if m in text:
            return True, m
    return False, None


def contains_marker(text: str) -> bool:
    """Return True if the text contains any form of the marker."""
    return check_payload_kept(text)[0]