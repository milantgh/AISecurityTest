# -*- coding: utf-8 -*-
"""
Convert an Excel / CSV dataset into a YAML case file with dynamic payloads.

This bridges the gap between raw attack datasets (Safety-Prompts,
HarmBench, AdvBench, etc.) and AISecurityTest's YAML case library.

Instead of hand-copying every payload into a YAML file, you point this
tool at a dataset, tell it which column holds the payload, and it emits a
YAML case that loads the dataset dynamically at runtime.

The generated YAML uses the ``dataset`` + ``{field}`` template mechanism
(see ``engine/payload.py``), so one case file can drive hundreds of
payloads without bloating the YAML.

Usage (CLI)
-----------
    python -m aisecurity.engine.excel_to_yaml \\
        --input safety_prompts.csv \\
        --payload-column prompt \\
        --case-id PI-200 \\
        --category direct \\
        --sub "提示正文注入" \\
        --sub3 "数据集驱动批量注入" \\
        --output direct/cases.yaml

Usage (Python)
--------------
    from aisecurity.engine.excel_to_yaml import convert
    convert("safety_prompts.csv", payload_column="prompt",
            case_id="PI-200", category="direct", sub="提示正文注入",
            sub3="数据集驱动批量注入", output="direct/cases.yaml")
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _read_rows(input_path: str) -> List[Dict[str, Any]]:
    """Read rows from a CSV, JSON, JSONL, or XLSX file."""
    path = Path(input_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        raise ValueError("JSON must be a list of objects")

    if suffix in (".jsonl", ".ndjson"):
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    if suffix in (".xlsx", ".xls"):
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel files. "
                "Install it with: pip install openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header = [str(c) if c is not None else "" for c in next(rows_iter)]
        rows = []
        for row in rows_iter:
            rows.append({header[i]: (str(v) if v is not None else "")
                         for i, v in enumerate(row)})
        return rows

    raise ValueError("Unsupported input format: %s" % suffix)


def convert(input_path: str,
            payload_column: str,
            case_id: str,
            category: str,
            sub: str = "",
            sub3: str = "",
            level: str = "高",
            owasp: str = "LLM01",
            defense: str = "",
            note: str = "",
            limit: Optional[int] = None,
            shuffle: bool = False,
            output: Optional[str] = None) -> str:
    """Convert a dataset file to a YAML case with dynamic payload loading.

    Parameters
    ----------
    input_path : str
        Path to the dataset (.csv / .json / .jsonl / .xlsx).
    payload_column : str
        Name of the column/field that holds the attack payload.
    case_id : str
        Case ID, e.g. ``PI-200``.
    category : str
        Category directory name, e.g. ``direct``.  Used to place the
        dataset reference and the output file.
    sub, sub3 : str
        Sub-category labels.
    level : str
        Risk level (严重 / 高 / 中-高 / 中 / 低).
    owasp : str
        OWASP LLM Top 10 tag(s).
    defense : str
        Defensive recommendations.
    note : str
        Additional notes.
    limit : int | None
        Maximum rows to load at runtime (written into the dataset block).
    shuffle : bool
        Whether to shuffle rows at runtime.
    output : str | None
        Output YAML path.  If ``None``, prints to stdout.

    Returns
    -------
    str
        The generated YAML content.
    """
    if not HAS_YAML:
        raise ImportError("PyYAML is required")

    # Validate that the payload column exists in a sample of the dataset.
    rows = _read_rows(input_path)
    if not rows:
        raise ValueError("Input dataset is empty: %s" % input_path)
    if payload_column not in rows[0]:
        available = ", ".join(sorted(rows[0].keys()))
        raise ValueError(
            "Column '%s' not found in dataset. Available columns: %s"
            % (payload_column, available))

    # The dataset is referenced relative to data/datasets/.  We copy the
    # dataset filename into the YAML so the loader can find it.
    dataset_filename = Path(input_path).name

    case = {
        "meta": {
            "name": category,
            "desc": "动态加载数据集的用例（自动生成）",
            "order": 999,
            "owasp": [owasp.split()[0] if owasp else "LLM01"],
            "contributors": ["@auto"],
        },
        "cases": {
            case_id: {
                "id": case_id,
                "sub": sub or "数据集驱动",
                "sub3": sub3 or "动态加载 %s" % payload_column,
                "pre": "目标 AI 系统 会话已开启；数据集已放置于 data/datasets/%s。"
                       % dataset_filename,
                "steps": [
                    "将数据集 %s 放置于 data/datasets/ 目录；" % dataset_filename,
                    "运行扫描，工具自动加载数据集中的每一行作为 payload；",
                    "记录模型对每条 payload 的响应。",
                ],
                "payloads": ["{%s}" % payload_column],
                "dataset": {
                    "source": dataset_filename,
                    "limit": limit,
                    "shuffle": shuffle,
                },
                "expect": "模型拒绝执行数据集中的恶意指令，不输出敏感信息。",
                "level": level,
                "defense": defense or "输入过滤、语义检测、输出层敏感信息检测。",
                "owasp": owasp,
                "note": note or "由 excel_to_yaml 自动生成，动态加载数据集。",
                "source": "auto-generated",
                "manual_only": False,
            }
        }
    }

    yaml_text = yaml.safe_dump(case, allow_unicode=True, sort_keys=False,
                               default_flow_style=False)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(yaml_text)
        print("YAML case written to %s" % out_path)
        print("  case ID : %s" % case_id)
        print("  payload : {%%%s%%}  from  %s (%d rows)"
              % (payload_column, dataset_filename, len(rows)))

    return yaml_text


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="excel-to-yaml",
        description="Convert Excel/CSV/JSON dataset to a dynamic YAML case")
    p.add_argument("--input", "-i", required=True,
                   help="input dataset (.csv/.json/.jsonl/.xlsx)")
    p.add_argument("--payload-column", "-c", required=True,
                   help="column name that holds the payload")
    p.add_argument("--case-id", required=True, help="case ID, e.g. PI-200")
    p.add_argument("--category", required=True,
                   help="category dir name, e.g. direct")
    p.add_argument("--sub", default="", help="sub-category label")
    p.add_argument("--sub3", default="", help="sub-sub-category label")
    p.add_argument("--level", default="高",
                   help="risk level (严重/高/中-高/中/低)")
    p.add_argument("--owasp", default="LLM01", help="OWASP tag(s)")
    p.add_argument("--defense", default="", help="defense recommendations")
    p.add_argument("--note", default="", help="additional notes")
    p.add_argument("--limit", type=int, default=None,
                   help="max rows to load at runtime")
    p.add_argument("--shuffle", action="store_true",
                   help="shuffle rows at runtime")
    p.add_argument("--output", "-o", default=None,
                   help="output YAML path; omit to print to stdout")
    args = p.parse_args(argv)

    yaml_text = convert(
        input_path=args.input,
        payload_column=args.payload_column,
        case_id=args.case_id,
        category=args.category,
        sub=args.sub,
        sub3=args.sub3,
        level=args.level,
        owasp=args.owasp,
        defense=args.defense,
        note=args.note,
        limit=args.limit,
        shuffle=args.shuffle,
        output=args.output,
    )

    if not args.output:
        print(yaml_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
