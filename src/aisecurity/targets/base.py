# -*- coding: utf-8 -*-
"""Abstract base class for targets under test.
Any backend (OpenAI-compatible/Ollama/custom HTTP endpoint/RAG/MCP)implements this interface. 
The runner only cares about Target and does not know about the underlying implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TargetResponse:
    """Unified response object."""
    text: str
    raw: Any = None
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    metadata: dict = field(default_factory=dict)


class Target(ABC):
    """Base class for all target adapters."""

    name = "base"

    @abstractmethod
    def send(self, payload, **kwargs):
        # type: (str, **Any) -> TargetResponse
        """Send one payload, return a unified response."""
        raise NotImplementedError

    def close(self):
        """Release resources (connection pools, etc.)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()