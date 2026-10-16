# -*- coding: utf-8 -*-
"""
扫描结果 SQLite 存储。
支持：跨扫描查询、按目标/模型/时间筛选、结果去重。
存储位置：~/.aisecurity/scans.db
"""
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

from .scanner import ScanResult
from ..runner.result import CaseResult


def _db_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".aisecurity")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "scans.db")

def _conn():
    c = sqlite3.connect(_db_path())
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS scans (
        scan_id TEXT PRIMARY KEY,
        target TEXT,
        model TEXT,
        profile TEXT,
        started_at TEXT,
        finished_at TEXT,
        duration_sec REAL,
        total_cases INTEGER,
        total_payloads INTEGER,
        hits INTEGER,
        errors INTEGER,
        hit_rate REAL,
        meta TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT,
        case_id TEXT,
        payload TEXT,
        response TEXT,
        success INTEGER,
        latency_ms INTEGER,
        error TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scans_started ON scans(started_at DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_findings_scan ON findings(scan_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_findings_case ON findings(case_id)")
    return c


def save(result: ScanResult):
    """把一次扫描结果写入 SQLite。"""
    c = _conn()
    c.execute("""INSERT OR REPLACE INTO scans
        (scan_id, target, model, profile, started_at, finished_at,
         duration_sec, total_cases, total_payloads, hits, errors, hit_rate, meta)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        result.scan_id, result.target, result.model, result.profile,
        result.started_at, result.finished_at, result.duration_sec,
        result.total_cases, result.total_payloads, result.hits,
        result.errors, result.hit_rate,
        json.dumps(result.meta, ensure_ascii=False),
    ))
    # 先清掉旧记录（避免重复）
    c.execute("DELETE FROM findings WHERE scan_id=?", (result.scan_id,))
    for r in result.results:
        c.execute("""INSERT INTO findings
            (scan_id, case_id, payload, response, success, latency_ms, error)
            VALUES (?,?,?,?,?,?,?)""", (
            result.scan_id, r.case_id, r.payload or "",
            (r.response_text or "")[:4000],
            int(bool(r.success)), r.latency_ms or 0, r.error or "",
        ))
    c.commit()
    c.close()


def list_scans(limit: int = 50,
               target: Optional[str] = None,
               model: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出扫描历史（按时间倒序）。"""
    c = _conn()
    q = "SELECT * FROM scans WHERE 1=1"
    params = []
    if target:
        q += " AND target LIKE ?"
        params.append("%" + target + "%")
    if model:
        q += " AND model LIKE ?"
        params.append("%" + model + "%")
    q += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    rows = c.execute(q, params).fetchall()
    c.close()
    return [dict(r) for r in rows]


def load(scan_id: str) -> Optional[ScanResult]:
    """从 SQLite 加载一个历史扫描，还原成 ScanResult。"""
    c = _conn()
    row = c.execute("SELECT * FROM scans WHERE scan_id=?", (scan_id,)).fetchone()
    if not row:
        c.close()
        return None
    findings = c.execute(
        "SELECT * FROM findings WHERE scan_id=? ORDER BY id", (scan_id,)
    ).fetchall()
    c.close()

    result = ScanResult(
        scan_id=row["scan_id"],
        target=row["target"] or "",
        model=row["model"] or "",
        profile=row["profile"] or "",
        started_at=row["started_at"] or "",
        finished_at=row["finished_at"] or "",
        duration_sec=row["duration_sec"] or 0,
        total_cases=row["total_cases"] or 0,
        total_payloads=row["total_payloads"] or 0,
        hits=row["hits"] or 0,
        errors=row["errors"] or 0,
        meta=json.loads(row["meta"]) if row["meta"] else {},
        results=[],
    )

    # 评估结果不需要从 DB 还原（报告只用 success 字段）
    for f in findings:
        cr = CaseResult(
            case_id=f["case_id"] or "",
            payload=f["payload"] or "",
            response_text=f["response"] or "",
            latency_ms=f["latency_ms"] or 0,
            error=f["error"] or "",
        )
        cr.eval_results = []  # 简化：从 DB 不还原评估器细节
        result.results.append(cr)
    return result


def delete(scan_id: str) -> int:
    """删除一条扫描记录，返回被删除的 findings 数量。"""
    c = _conn()
    n = c.execute("DELETE FROM findings WHERE scan_id=?", (scan_id,)).rowcount
    c.execute("DELETE FROM scans WHERE scan_id=?", (scan_id,))
    c.commit()
    c.close()
    return n


def stats() -> Dict[str, Any]:
    """全局统计：总扫描数、总命中数、按模型分布。"""
    c = _conn()
    total_scans = c.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
    total_hits = c.execute("SELECT SUM(hits) FROM scans").fetchone()[0] or 0
    total_payloads = c.execute("SELECT SUM(total_payloads) FROM scans").fetchone()[0] or 0
    by_model = {}
    for r in c.execute("""SELECT model, COUNT(*) AS cnt, SUM(hits) AS hits
                          FROM scans GROUP BY model"""):
        by_model[r["model"]] = {"scans": r["cnt"], "hits": r["hits"] or 0}
    c.close()
    return {
        "total_scans": total_scans,
        "total_hits": total_hits,
        "total_payloads": total_payloads,
        "overall_hit_rate": (total_hits / total_payloads) if total_payloads else 0,
        "by_model": by_model,
    }