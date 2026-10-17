# -*- coding: utf-8 -*-
"""
自动化扫描核心：把YAML用例-payload-发送-评估-报告全链路串起来。
设计：
- 单轮扫描：逐条 payload 发送 + 逐条打印
- 支持变体扩展：--transform 变换 × --lang 语言
- 多轮扫描：Session 里维护对话历史
- 结果落盘：SQLite（~/.aisecurity/scans.db）
- Ctrl+C 中断：保存已有结果并打印部分报告，不崩溃
"""
import time
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ..core.registry import CASE_LIB, CATEGORY_REGISTRY
from ..runner.runner import Runner
from ..runner.result import CaseResult
from .session import Session
from .strategy import get_strategy
from .logger import Logger


@dataclass
class ScanResult:
    scan_id: str
    target: str
    model: str
    profile: str
    started_at: str
    finished_at: str = ""
    duration_sec: float = 0.0
    total_cases: int = 0
    total_payloads: int = 0
    hits: int = 0
    errors: int = 0
    results: List[CaseResult] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        if self.total_payloads == 0:
            return 0.0
        return self.hits / self.total_payloads

    def to_dict(self):
        return {
            "scan_id": self.scan_id,
            "target": self.target,
            "model": self.model,
            "profile": self.profile,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_sec": round(self.duration_sec, 2),
            "total_cases": self.total_cases,
            "total_payloads": self.total_payloads,
            "hits": self.hits,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 4),
            "meta": self.meta,
            "results": [r.to_dict() for r in self.results],
        }


class AutoScanner:
    """自动化扫描器。"""

    def __init__(self, target, evaluators=None,
                 rate_limit_sec: float = 0.5,
                 stop_on_error: bool = False,
                 verbose: bool = False,
                 auto_save: bool = True,
                 log_level: int = None):
        self.target = target
        self.evaluators = evaluators or []
        self.rate_limit_sec = rate_limit_sec
        self.stop_on_error = stop_on_error
        self.verbose = verbose
        self.auto_save = auto_save

        if log_level is None:
            log_level = 2 if verbose else 1
        self.log = Logger(level=log_level)

        self._runner = Runner(target, self.evaluators)
        self._interrupted = False

    # ---------- 中断安全 sleep ----------
    def _sleep(self):
        """Sleep, but let Ctrl+C break out cleanly. Returns True if interrupted."""
        try:
            time.sleep(self.rate_limit_sec)
            return False
        except KeyboardInterrupt:
            self._interrupted = True
            return True

    # ---------- 单轮扫描（支持变体扩展）----------
    def scan(self, case_ids: List[str],
             profile: str = "custom",
             transforms: List[str] = None,
             languages: List[str] = None) -> ScanResult:
        """
        transforms: 变换列表；None 时用每条 payload 原始形式
        languages: 语言列表；None 时只用中文
        """
        from .expand import expand_payload, expand_matrix

        self._interrupted = False

        result = self._new_result(case_ids, profile)
        result.meta["transforms"] = transforms or ["raw"]
        result.meta["languages"] = languages or ["zh"]

        self.log.scan_start(
            target=result.target, model=result.model,
            profile=result.profile, total_cases=result.total_cases,
        )

        try:
            for cid in case_ids:
                if self._interrupted:
                    self.log.warn("用户中断，停止后续用例")
                    break

                if cid not in CASE_LIB:
                    self.log.warn("未知用例，跳过: %s" % cid)
                    continue

                case = CASE_LIB[cid]

                # 跳过手工用例
                if case.get("manual_only"):
                    self.log.info("[%s] 手工用例，跳过" % cid)
                    continue

                case_title = case.get("sub3", "")
                self.log.case_start(cid, case_title)

                t0 = time.time()
                case_hits = 0
                case_errors = 0
                case_payloads = 0

                # 1. 生成基础 payload
                try:
                    from ..engine.payload import gen_by_case
                    base_payloads = gen_by_case(cid, mark=False)
                except Exception as e:
                    self.log.error("生成 payload 失败: %s" % e)
                    case_errors += 1
                    continue

                # 2. 扩展成变体
                all_variants = []
                for bp in base_payloads:
                    if languages and transforms:
                        variants = expand_matrix(bp, transforms, languages, mark=True)
                    elif transforms:
                        variants = expand_payload(bp, transforms, mark=True)
                    else:
                        variants = expand_payload(bp, ["raw"], mark=True)
                    all_variants.extend(variants)

                total = len(all_variants)
                self.log.info("[%s] 扩展出 %d 条变体" % (cid, total))

                # 3. 逐条发送
                for idx, variant in enumerate(all_variants, 1):
                    if self._interrupted:
                        self.log.warn("用户中断，停止当前用例")
                        break

                    payload = variant["payload"]
                    self.log.payload_start(idx, total)
                    self.log.payload_sent(
                        payload=payload,
                        endpoint=getattr(self.target, "endpoint", ""),
                        model=getattr(self.target, "model", ""),
                    )

                    label = "transform=%s" % variant.get("transform", "?")
                    if variant.get("language"):
                        label += " lang=%s" % variant["language"]
                    self.log.info("  <- " + label)

                    try:
                        resp = self.target.send(payload)
                        evals = [ev.evaluate(payload, resp.text) for ev in self.evaluators]

                        self.log.payload_response(
                            response=resp.text,
                            latency_ms=resp.latency_ms,
                            tokens_in=getattr(resp, "tokens_in", 0),
                            tokens_out=getattr(resp, "tokens_out", 0),
                        )
                        self.log.payload_evals(evals)

                        cr = CaseResult(
                            case_id=cid,
                            payload=payload,
                            response_text=resp.text,
                            eval_results=evals,
                            latency_ms=resp.latency_ms,
                            meta=variant,
                        )
                        if cr.success:
                            case_hits += 1
                            self.log.payload_result(success=True, error=False)
                        else:
                            self.log.payload_result(success=False, error=False)

                    except Exception as e:
                        err_msg = "%s: %s" % (type(e).__name__, e)
                        self.log.payload_error(err_msg)
                        self.log.payload_result(success=False, error=True)
                        cr = CaseResult(case_id=cid, payload=payload,
                                        error=err_msg, meta=variant)
                        case_errors += 1

                    result.results.append(cr)
                    case_payloads += 1
                    if self._sleep():
                        self.log.warn("用户中断，停止后续 payload")
                        break

                elapsed = time.time() - t0
                self.log.case_done(cid, case_payloads, case_hits, case_errors, elapsed)

                result.total_payloads += case_payloads
                result.hits += case_hits
                result.errors += case_errors

                if self.stop_on_error and case_errors > 0:
                    self.log.warn("遇到错误，停止扫描（--stop-on-error）")
                    break

        except KeyboardInterrupt:
            self.log.warn("用户中断（Ctrl+C），保存已有结果...")
            self._interrupted = True

        result.meta["interrupted"] = self._interrupted
        result = self._finalize(result)
        self.log.scan_done(result)
        if self._interrupted:
            self.log.warn("扫描被中断，已保存部分结果到 SQLite")
        return result

    # ---------- 按 profile 扫描（支持变体扩展）----------
    def scan_profile(self, profile_name: str,
                     transforms: List[str] = None,
                     languages: List[str] = None) -> ScanResult:
        from .schedule import load_profile
        profile = load_profile(profile_name)
        case_ids = profile.get("cases") or []
        if not case_ids:
            case_ids = self._select_cases(profile.get("filter", {}))
        return self.scan(case_ids, profile=profile_name,
                         transforms=transforms, languages=languages)

    # ---------- 多轮扫描 ----------
    def scan_multi_turn(self, strategy_name: str,
                        case_id: str = "PI-002",
                        max_turns: int = 5) -> ScanResult:
        self._interrupted = False
        result = self._new_result([case_id], profile="multi_turn:" + strategy_name)
        strategy = get_strategy(strategy_name)
        if strategy is None:
            raise ValueError("unknown multi-turn strategy: %s" % strategy_name)

        self.log.scan_start(
            target=result.target, model=result.model,
            profile=result.profile, total_cases=1,
        )

        session = Session(self.target, evaluators=self.evaluators,
                          rate_limit_sec=self.rate_limit_sec)
        try:
            turns = strategy.build_turns(case_id, max_turns=max_turns)
        except Exception as e:
            self.log.error("build_turns failed: %s" % e)
            result.errors += 1
            result = self._finalize(result)
            self.log.scan_done(result)
            return result

        try:
            for i, turn in enumerate(turns, 1):
                if self._interrupted:
                    self.log.warn("用户中断，停止后续轮次")
                    break

                label = turn.get("label", "turn %d" % i)
                self.log.payload_start(i, len(turns))
                self.log.payload_sent(
                    payload=turn["payload"],
                    endpoint=getattr(self.target, "endpoint", ""),
                    model=getattr(self.target, "model", ""),
                )
                self.log.info("轮次标签: %s" % label)

                try:
                    cr = session.send(turn["payload"], case_id=case_id)

                    self.log.payload_response(
                        response=cr.response_text or "",
                        latency_ms=cr.latency_ms,
                    )
                    self.log.payload_evals(cr.eval_results)
                    self.log.payload_result(success=cr.success, error=bool(cr.error))

                    result.results.append(cr)
                    result.total_payloads += 1
                    if cr.error:
                        result.errors += 1
                    elif cr.success:
                        result.hits += 1
                        if turn.get("stop_on_hit", True):
                            self.log.info("第 %d 轮命中，提前结束多轮会话" % i)
                            break
                except Exception as e:
                    self.log.payload_error(str(e))
                    result.errors += 1
                    if self.stop_on_error:
                        break

                if self._sleep():
                    self.log.warn("用户中断，停止后续轮次")
                    break

        except KeyboardInterrupt:
            self.log.warn("用户中断（Ctrl+C），保存已有结果...")
            self._interrupted = True

        result.meta["session_id"] = session.session_id
        result.meta["turn_count"] = len(session.history)
        result.meta["strategy"] = strategy_name
        result.meta["interrupted"] = self._interrupted

        result = self._finalize(result)
        self.log.scan_done(result)
        if self._interrupted:
            self.log.warn("扫描被中断，已保存部分结果到 SQLite")
        return result

    # ---------- 辅助 ----------
    def _new_result(self, case_ids, profile) -> ScanResult:
        sid = "scan-%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        return ScanResult(
            scan_id=sid,
            target=getattr(self.target, "endpoint", "unknown"),
            model=getattr(self.target, "model", "unknown"),
            profile=profile,
            started_at=datetime.datetime.now().isoformat(timespec="seconds"),
            total_cases=len(case_ids),
        )

    def _finalize(self, result: ScanResult) -> ScanResult:
        result.finished_at = datetime.datetime.now().isoformat(timespec="seconds")
        t0 = datetime.datetime.fromisoformat(result.started_at)
        t1 = datetime.datetime.fromisoformat(result.finished_at)
        result.duration_sec = (t1 - t0).total_seconds()

        if self.auto_save:
            try:
                from . import storage
                storage.save(result)
                self.log.debug("SQLite 已保存: %s" % result.scan_id)
            except Exception as e:
                self.log.warn("SQLite 保存失败: %s" % e)

        return result

    def _select_cases(self, filter_spec: Dict[str, Any]) -> List[str]:
        out = []
        cats = filter_spec.get("categories")
        owasp = filter_spec.get("owasp")
        levels = filter_spec.get("levels")
        for cid, case in CASE_LIB.items():
            if cats and case.get("cat") not in cats:
                continue
            if owasp and not any(o in case.get("owasp", "") for o in owasp):
                continue
            if levels and case.get("level") not in levels:
                continue
            out.append(cid)
        return out