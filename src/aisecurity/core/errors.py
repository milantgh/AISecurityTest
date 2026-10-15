# -*- coding: utf-8 -*-
"""Unified exceptions."""

class AISecError(Exception):
    """Base class for all project exceptions."""

class CaseSchemaError(AISecError):
    """Invalid case schema."""

class CaseConflictError(AISecError):
    """Case ID or category name conflict."""

class TargetError(AISecError):
    """Target adapter error."""

class EvaluatorError(AISecError):
    """Evaluator error."""