# -*- coding: utf-8 -*-
"""
扫描结果报告输出：JSON/Markdown/HTML。
HTML报告带样式+打印为PDF按钮。
"""
import json
from typing import List
from .scanner import ScanResult
from ..core.registry import CASE_LIB

# 严重度顺序（从重到轻）
_LEVEL_ORDER = ["严重", "高", "中-高", "中", "低"]

def _level_counts(result: ScanResult):
    """统计命中的用例按严重度分布。"""
    counts = {lv: 0 for lv in _LEVEL_ORDER}
    for r in result.results:
        if not r.success:
            continue
        case = CASE_LIB.get(r.case_id, {})
        lv = case.get("level", "低")
        if lv in counts:
            counts[lv] += 1
        else:
            counts["低"] += 1
    return counts


def to_json(result: ScanResult, indent: int = 2) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=indent)


def to_markdown(result: ScanResult) -> str:
    lines = []
    lines.append("# AISecurityTest 自动化扫描报告\n")
    lines.append("- **扫描 ID**: `%s`" % result.scan_id)
    lines.append("- **目标**: `%s`" % result.target)
    lines.append("- **模型**: `%s`" % result.model)
    lines.append("- **Profile**: `%s`" % result.profile)
    lines.append("- **开始时间**: %s" % result.started_at)
    lines.append("- **结束时间**: %s" % result.finished_at)
    lines.append("- **耗时**: %.1f 秒" % result.duration_sec)
    lines.append("")
    lines.append("## 总览\n")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    lines.append("| 用例数 | %d |" % result.total_cases)
    lines.append("| Payload 总数 | %d |" % result.total_payloads)
    lines.append("| 命中（攻击成功） | %d |" % result.hits)
    lines.append("| 错误 | %d |" % result.errors)
    lines.append("| 命中率 | %.2f%% |" % (result.hit_rate * 100))
    lines.append("")

    # 按严重度分级
    lc = _level_counts(result)
    lines.append("## 按严重度分级\n")
    lines.append("| 严重度 | 命中数 |")
    lines.append("|---|---|")
    for lv in _LEVEL_ORDER:
        if lc[lv] > 0:
            lines.append("| %s | %d |" % (lv, lc[lv]))
    if sum(lc.values()) == 0:
        lines.append("| （无命中） | 0 |")
    lines.append("")

    lines.append("## 结果明细\n")
    lines.append("| # | 用例 | Payload | 结果 | 延迟(ms) | 评估 |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(result.results, 1):
        payload = (r.payload or "").replace("|", "\\|")[:50]
        status = "HIT" if r.success else ("ERROR" if r.error else "miss")
        evals = "; ".join(
            "%s=%s" % (er.name, "hit" if er.hit else "miss")
            for er in (r.eval_results or [])
        )
        lines.append("| %d | %s | `%s` | %s | %d | %s |" % (
            i, r.case_id, payload, status, r.latency_ms, evals
        ))
    return "\n".join(lines)


def to_html(result: ScanResult) -> str:
    """生成带样式的 HTML 报告，右上角有打印/存 PDF 按钮。"""
    lc = _level_counts(result)
    mid_count = lc["中-高"] + lc["中"]

    # 构建明细行
    rows_html = []
    for i, r in enumerate(result.results, 1):
        cls = "hit" if r.success else ("err" if r.error else "miss")
        if r.success:
            status = "✅ HIT"
        elif r.error:
            status = "❌ ERROR"
        else:
            status = "· miss"
        payload = (r.payload or "")[:120]
        payload = payload.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        response = (r.response_text or "")[:160]
        response = response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows_html.append(
            '<tr class="%s"><td>%d</td><td>%s</td>'
            '<td><code>%s</code></td>'
            '<td>%s</td><td>%d</td>'
            '<td class="resp">%s</td></tr>'
            % (cls, i, r.case_id, payload, status, r.latency_ms, response)
        )
    rows = "\n".join(rows_html)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>AISecurityTest 扫描报告 - %(scan_id)s</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
    max-width: 1100px; margin: 40px auto; padding: 20px 30px;
    color: #1f2328; line-height: 1.6; background: #fff;
  }
  h1 { border-bottom: 3px solid #0969da; padding-bottom: 12px;
       font-size: 26px; margin-bottom: 8px; }
  h2 { margin-top: 32px; font-size: 20px;
       border-left: 4px solid #0969da; padding-left: 10px; }
  .meta { color: #57606a; font-size: 13px; margin-bottom: 24px; }
  .meta code { background: #f6f8fa; padding: 2px 6px; border-radius: 4px;
               font-family: Consolas, Monaco, monospace; }
  .stats {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 14px; margin: 18px 0;
  }
  .stat {
    padding: 18px; border-radius: 10px; text-align: center;
    background: #f6f8fa; border: 1px solid #d0d7de;
  }
  .stat .num { font-size: 32px; font-weight: 700; line-height: 1.1; }
  .stat .label { color: #57606a; font-size: 13px; margin-top: 6px; }
  .stat.critical { background: #ffebe9; border-color: #ff8182; color: #cf222e; }
  .stat.high     { background: #fff1e5; border-color: #ffb77c; color: #bc4c00; }
  .stat.medium   { background: #fff8c5; border-color: #d4a72c; color: #9a6700; }
  .stat.low      { background: #dafbe1; border-color: #4ac26b; color: #1a7f37; }
  table {
    width: 100%%; border-collapse: collapse; margin: 14px 0;
    font-size: 13px;
  }
  th, td {
    border: 1px solid #d0d7de; padding: 8px 10px; text-align: left;
    vertical-align: top;
  }
  th { background: #f6f8fa; font-weight: 600; }
  td.resp { color: #57606a; font-size: 12px; max-width: 320px; }
  tr.hit  { background: #dafbe1; }
  tr.err  { background: #ffebe9; }
  tr.miss { background: #fff; }
  code {
    background: #f6f8fa; padding: 1px 5px; border-radius: 3px;
    font-family: Consolas, Monaco, monospace; font-size: 12px;
    word-break: break-all;
  }
  .print-btn {
    position: fixed; top: 24px; right: 24px;
    padding: 10px 20px; background: #0969da; color: #fff;
    border: none; border-radius: 6px; cursor: pointer;
    font-size: 14px; font-weight: 500; box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }
  .print-btn:hover { background: #0860ca; }
  .footer { color: #57606a; font-size: 12px; margin-top: 40px;
            padding-top: 16px; border-top: 1px solid #d0d7de; }
  @media print {
    .print-btn { display: none; }
    body { margin: 0; padding: 15px; max-width: 100%%; }
    tr.hit { background: #dafbe1 !important;
             -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .stat.critical, .stat.high, .stat.medium, .stat.low {
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
  }
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">🖨 打印 / 存为 PDF</button>

<h1>AISecurityTest 扫描报告</h1>
<div class="meta">
  扫描 ID: <code>%(scan_id)s</code> ｜
  目标: <code>%(target)s</code> ｜
  模型: <code>%(model)s</code> ｜
  Profile: <code>%(profile)s</code><br>
  开始: %(started_at)s ｜ 结束: %(finished_at)s ｜
  耗时: %(duration).1f 秒
</div>

<h2>总览</h2>
<div class="stats">
  <div class="stat"><div class="num">%(total_cases)d</div><div class="label">用例数</div></div>
  <div class="stat"><div class="num">%(total_payloads)d</div><div class="label">Payload 总数</div></div>
  <div class="stat"><div class="num">%(hits)d</div><div class="label">命中（攻击成功）</div></div>
  <div class="stat"><div class="num">%(hit_rate).1f%%</div><div class="label">命中率</div></div>
</div>

<h2>按严重度分级</h2>
<div class="stats">
  <div class="stat critical"><div class="num">%(c_crit)d</div><div class="label">严重</div></div>
  <div class="stat high"><div class="num">%(c_high)d</div><div class="label">高</div></div>
  <div class="stat medium"><div class="num">%(c_mid)d</div><div class="label">中</div></div>
  <div class="stat low"><div class="num">%(c_low)d</div><div class="label">低</div></div>
</div>

<h2>结果明细</h2>
<table>
  <thead>
    <tr>
      <th style="width:40px">#</th>
      <th style="width:80px">用例</th>
      <th>Payload</th>
      <th style="width:80px">结果</th>
      <th style="width:70px">延迟(ms)</th>
      <th>模型响应（截断）</th>
    </tr>
  </thead>
  <tbody>
%(rows)s
  </tbody>
</table>

<div class="footer">
  由 AISecurityTest 自动生成 · 仅限授权安全测试使用 · 
  绿色行表示命中（攻击成功），红色行表示错误
</div>

</body>
</html>""" % {
        "scan_id": result.scan_id,
        "target": result.target,
        "model": result.model,
        "profile": result.profile,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "duration": result.duration_sec,
        "total_cases": result.total_cases,
        "total_payloads": result.total_payloads,
        "hits": result.hits,
        "hit_rate": result.hit_rate * 100,
        "c_crit": lc["严重"],
        "c_high": lc["高"],
        "c_mid": mid_count,
        "c_low": lc["低"],
        "rows": rows,
    }
    return html