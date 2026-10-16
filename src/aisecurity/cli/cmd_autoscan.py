# -*- coding: utf-8 -*-
"""
aisec autoscan -- 自动化扫描。
用法：
    aisec autoscan list
    aisec autoscan list-transforms
    aisec autoscan history [--limit N] [--target T] [--model M]
    aisec autoscan report [scan_id] [--format markdown|json|html] [-o file]
    aisec autoscan run --endpoint URL --model MODEL --api-key KEY
                       [--profile NAME] [--case IDS]
                       [--transform LIST | --transform-all]
                       [--lang LIST]
                       [-v|-vv|-vvv]
                       [--format markdown|json|html] [-o file]
"""
import sys
import json
from ..targets.openai_compat import OpenAITarget
from ..evaluators import build_evaluators
from ..core.registry import CASE_LIB
from ..autotest import AutoScanner
from ..autotest.schedule import list_profiles
from ..autotest.strategy import list_strategies
from ..autotest.report import to_json, to_markdown, to_html
from ..autotest import storage

def add_autoscan_parser(sub):
    p = sub.add_parser("autoscan", help="自动化扫描（YAML 驱动，支持多轮注入）")
    sp = p.add_subparsers(dest="as_cmd")

    # ---- list ----
    sp.add_parser("list", help="列出可用 profile 和策略")

    # ---- list-transforms ----
    sp.add_parser("list-transforms", help="列出所有可用的 payload 变换")

    # ---- history ----
    h = sp.add_parser("history", help="列出历史扫描")
    h.add_argument("--limit", "-n", type=int, default=20,
                   help="显示最近 N 条（默认 20）")
    h.add_argument("--target", default=None, help="按目标过滤")
    h.add_argument("--model", default=None, help="按模型过滤")

    # ---- report ----
    r = sp.add_parser("report", help="从历史扫描生成报告")
    r.add_argument("scan_id", nargs="?", default=None,
                   help="扫描 ID；省略则用最近一次")
    r.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "json", "html"])
    r.add_argument("--output", "-o", default=None,
                   help="输出文件；省略则打印到终端")

    # ---- run ----
    g = sp.add_parser("run", help="执行扫描")
    g.add_argument("--endpoint", required=True,
                   help="OpenAI 兼容 API 地址，例如 https://api.deepseek.com")
    g.add_argument("--model", required=True, help="模型名")
    g.add_argument("--api-key", default="", help="API Key")
    g.add_argument("--system-prompt", default=None, help="目标系统提示")
    g.add_argument("--timeout", type=int, default=60, help="单次请求超时秒数")

    # 用例选择
    g.add_argument("--profile", default=None, help="使用哪个 profile")
    g.add_argument("--case", default=None, help="按用例 ID 过滤，逗号分隔")
    g.add_argument("--category", default=None, help="按分类名过滤")
    g.add_argument("--owasp", default=None, help="按 OWASP 编号过滤")
    g.add_argument("--level", default=None, help="按风险等级过滤")

    # 变体扩展
    g.add_argument("--transform", "-t", default=None,
                   help="变换列表，逗号分隔（raw,base64,hex,zero_width,"
                        "case_mix,similar,html,code,chatml_sys,chatml_ast,llama_inst,unicode）；"
                        "省略则不变换")
    g.add_argument("--transform-all", action="store_true",
                   help="使用全部 12 种变换（笛卡尔积扩展）")
    g.add_argument("--lang", default=None,
                   help="语言列表，逗号分隔（zh,en,sw,is,ha,mi,cy）；省略则只用中文")

    # 多轮
    g.add_argument("--multi-turn", default=None, help="多轮策略名")
    g.add_argument("--max-turns", type=int, default=5, help="多轮最大轮数")

    # 执行控制
    g.add_argument("--rate", type=float, default=0.5, help="每次请求最小间隔秒数")
    g.add_argument("--eval", default="marker,regex", help="评估器，逗号分隔")
    g.add_argument("--stop-on-error", action="store_true", help="遇到错误立即停止")

    # 详细度
    g.add_argument("-v", "--verbose", action="count", default=0,
                   help="详细度：-v 用例级 / -vv payload 级 / -vvv 含完整响应")

    # 输出
    g.add_argument("--output", "-o", default=None, help="报告输出文件")
    g.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "json", "html"],
                   help="报告格式")
    return p


def handle_autoscan(args):
    if args.as_cmd == "list":
        return _handle_list()
    if args.as_cmd == "list-transforms":
        return _handle_list_transforms()
    if args.as_cmd == "history":
        return _handle_history(args)
    if args.as_cmd == "report":
        return _handle_report(args)
    if args.as_cmd == "run":
        return _handle_run(args)
    print("请指定子命令：list / list-transforms / history / report / run")
    return 1


# ---------- list ----------
def _handle_list():
    print("扫描 profiles：")
    for p in list_profiles():
        print("  %s" % p)
    print()
    print("多轮策略：")
    for s in list_strategies():
        print("  %s" % s)
    print()
    print("使用示例：")
    print("  aisec autoscan run --endpoint https://api.deepseek.com \\")
    print("      --model deepseek-chat --api-key sk-xxx \\")
    print("      --profile text_only --transform-all --lang zh,en -v")
    return 0


# ---------- list-transforms ----------
def _handle_list_transforms():
    from ..autotest.expand import list_transforms
    print("可用的 payload 变换：")
    for t in list_transforms():
        print("  %-14s %s" % (t["name"], t["desc"]))
    print()
    print("用法：")
    print("  --transform base64,zero_width      只做指定变换")
    print("  --transform-all                    使用全部 12 种变换")
    print("  --lang zh,en,sw                    叠加多语言")
    return 0


# ---------- history ----------
def _handle_history(args):
    rows = storage.list_scans(limit=args.limit, target=args.target, model=args.model)
    if not rows:
        print("暂无历史扫描。")
        return 0
    print("%-24s %-42s %-22s %-6s %-6s %s" % (
        "SCAN ID", "TARGET", "MODEL", "HITS", "TOTAL", "STARTED"))
    print("-" * 130)
    for r in rows:
        print("%-24s %-42s %-22s %-6d %-6d %s" % (
            r["scan_id"],
            (r["target"] or "")[:42],
            (r["model"] or "")[:22],
            r["hits"] or 0,
            r["total_payloads"] or 0,
            r["started_at"] or "",
        ))
    print()
    s = storage.stats()
    print("总计: %d 次扫描 · %d payload · %d 命中 · 整体命中率 %.2f%%" % (
        s["total_scans"], s["total_payloads"], s["total_hits"],
        s["overall_hit_rate"] * 100))
    return 0


# ---------- report ----------
def _handle_report(args):
    scan_id = args.scan_id
    if not scan_id:
        rows = storage.list_scans(limit=1)
        if not rows:
            print("暂无历史扫描。")
            return 1
        scan_id = rows[0]["scan_id"]
        print("使用最近一次扫描: %s" % scan_id)

    result = storage.load(scan_id)
    if result is None:
        print("找不到扫描: %s" % scan_id)
        return 1

    if args.format == "json":
        text = to_json(result)
    elif args.format == "html":
        text = to_html(result)
    else:
        text = to_markdown(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("报告已写入: %s" % args.output)
    else:
        print(text)
    return 0


# ---------- run ----------
def _handle_run(args):
    from ..autotest.expand import parse_transform_list, parse_lang_list, count_variants

    target = OpenAITarget(
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
        system_prompt=args.system_prompt,
        timeout=args.timeout,
    )
    evaluators = build_evaluators(args.eval)

    # 解析变换和语言
    if args.transform_all:
        from ..autotest.expand import TRANSFORMS
        transforms = list(TRANSFORMS.keys())
    elif args.transform:
        transforms = parse_transform_list(args.transform)
    else:
        transforms = None

    languages = parse_lang_list(args.lang) if args.lang else None

    # -v 计数映射到 log_level
    log_level = min(3, 1 + args.verbose)

    scanner = AutoScanner(
        target=target,
        evaluators=evaluators,
        rate_limit_sec=args.rate,
        stop_on_error=args.stop_on_error,
        verbose=bool(args.verbose),
        log_level=log_level,
    )

    # 提示变体总数
    if transforms or languages:
        est = count_variants(transforms or ["raw"], languages or ["zh"])
        print("[autoscan] 每条 payload 将扩展成 %d 条变体" % est)
        sys.stdout.flush()

    # 非实时输出的格式提前提示
    if args.format in ("html", "json") and not args.output:
        print("[autoscan] 扫描中，请稍候...（报告将在扫描完成后一次性输出）")
    elif args.format in ("html", "json") and args.output:
        print("[autoscan] 扫描中，报告将写入 %s ..." % args.output)
    sys.stdout.flush()

    try:
        if args.multi_turn:
            case_id = (args.case.split(",")[0] if args.case else "PI-002")
            result = scanner.scan_multi_turn(
                args.multi_turn, case_id=case_id, max_turns=args.max_turns
            )
        elif args.profile:
            result = scanner.scan_profile(
                args.profile, transforms=transforms, languages=languages
            )
        else:
            case_ids = _resolve_case_ids(args)
            if not case_ids:
                print("没有匹配到任何用例。")
                print("请用 --profile / --case / --category / --owasp / --level 指定。")
                return 1
            result = scanner.scan(case_ids, transforms=transforms,
                                   languages=languages)
    except Exception as e:
        print("[autoscan] 执行失败: %s" % e)
        return 1

    # 报告输出
    if args.format == "json":
        text = to_json(result)
    elif args.format == "html":
        text = to_html(result)
    else:
        text = to_markdown(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("[autoscan] 报告已写入: %s" % args.output)
    else:
        if args.format == "markdown":
            print(text)
        else:
            print("[autoscan] 报告格式 %s 需要指定 --output 参数" % args.format)

    return 2 if result.hits > 0 else 0


# ---------- helpers ----------
def _resolve_case_ids(args):
    ids = []
    if args.case:
        ids = [c.strip() for c in args.case.split(",") if c.strip()]
    elif args.category:
        for cid, case in CASE_LIB.items():
            if case.get("cat") == args.category:
                ids.append(cid)
    elif args.owasp:
        for cid, case in CASE_LIB.items():
            if args.owasp in case.get("owasp", ""):
                ids.append(cid)
    elif args.level:
        for cid, case in CASE_LIB.items():
            if case.get("level") == args.level:
                ids.append(cid)
    return ids