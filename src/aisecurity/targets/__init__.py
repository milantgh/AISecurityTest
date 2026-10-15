# -*- coding: utf-8 -*-
"""Target adapter layer."""
from .base import Target, TargetResponse
from .openai_compat import OpenAITarget

__all__ = ["Target", "TargetResponse", "OpenAITarget"]