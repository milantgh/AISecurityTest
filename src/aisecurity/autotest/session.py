# -*- coding: utf-8 -*-
"""
多轮会话管理。
维护对话历史，把每一轮 payload 发出去，并用评估器判定每轮结果。
"""
import time
import uuid
from typing import List, Dict, Any

from ..runner.result import CaseResult

class Session:
    """
    一次多轮会话。每一轮发送一条 payload，记录response和评估结果。
    """

    def __init__(self, target, evaluators=None, rate_limit_sec: float = 0.5):
        self.target = target
        self.evaluators = evaluators or []
        self.rate_limit_sec = rate_limit_sec
        self.session_id = "sess-" + uuid.uuid4().hex[:8]
        self.history: List[Dict[str, Any]] = []

    def send(self, payload: str, case_id: str = "") -> CaseResult:
        """发送一轮 payload，返回 CaseResult。"""
        try:
            resp = self.target.send(payload)
            evals = [ev.evaluate(payload, resp.text) for ev in self.evaluators]
            result = CaseResult(
                case_id=case_id or self.session_id,
                payload=payload,
                response_text=resp.text,
                eval_results=evals,
                latency_ms=resp.latency_ms,
            )
        except Exception as e:
            result = CaseResult(
                case_id=case_id or self.session_id,
                payload=payload,
                error="%s: %s" % (type(e).__name__, e),
            )

        self.history.append({
            "turn": len(self.history) + 1,
            "payload": payload,
            "response": result.response_text,
            "success": result.success,
            "error": result.error,
        })
        return result

    def reset(self):
        """重置会话（清空历史，保留 session_id）。"""
        self.history = []