# -*- coding: utf-8 -*-
"""
Dataset loader for dynamic YAML payloads.

Loads attack-payload datasets (CSV / JSON / JSONL) so that YAML case
templates can reference dataset rows through ``{variable}`` placeholders
instead of hardcoding every payload.

Design mirrors xray/nuclei template variables: the YAML is the skeleton
(category, steps, expected, defense), and the dataset provides the blood
(the actual payload strings).  One template × N dataset rows = N payloads.

Supported formats
-----------------
* **CSV**  — first row is the header; each subsequent row is a record.
* **JSON** — a list of objects (``[{...}, {...}]``).
* **JSONL** — one JSON object per line.

Usage
-----
    from aisecurity.core.dataset_loader import load_dataset

    rows = load_dataset("data/datasets/safety_prompts.csv", limit=50)
    for row in rows:
        print(row["prompt"])
"""
from __future__ import annotations

import csv
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

_PKG_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = _PKG_ROOT / "data" / "datasets"


def _resolve_path(source: str) -> Path:
    """Resolve a dataset source to an absolute Path.

    Resolution order:
      1. As-is (absolute path or relative to cwd).
      2. Relative to the package ``data/datasets/`` directory.
    """
    p = Path(source)
    if p.is_file():
        return p
    bundled = DEFAULT_DATASET_DIR / source
    if bundled.is_file():
        return bundled
    # Last resort: return as-is so the caller gets a clear FileNotFoundError.
    return p


def load_csv(path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dicts (header row → keys)."""
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys and values.
            cleaned = {(k or "").strip(): (v or "").strip()
                       for k, v in row.items()}
            rows.append(cleaned)
    return rows


def load_json(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file. Accepts either a list of objects or a single object."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError("JSON dataset must be a list of objects or a single object")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file (one JSON object per line)."""
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except json.JSONDecodeError:
                continue
    return rows


def load_dataset(source: str,
                 limit: Optional[int] = None,
                 shuffle: bool = False,
                 seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load a dataset from *source*.

    Parameters
    ----------
    source : str
        Path to a .csv / .json / .jsonl file.  Resolved against cwd first,
        then against ``data/datasets/``.
    limit : int | None
        Maximum number of rows to return.  ``None`` means all rows.
    shuffle : bool
        Shuffle rows before applying *limit*.
    seed : int | None
        Random seed for reproducible shuffling.

    Returns
    -------
    list[dict]
        Each dict maps column/field names to values (strings for CSV).
    """
    path = _resolve_path(source)
    if not path.is_file():
        raise FileNotFoundError(
            "Dataset not found: %s (looked in cwd and %s)"
            % (source, DEFAULT_DATASET_DIR))

    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows = load_csv(path)
    elif suffix == ".json":
        rows = load_json(path)
    elif suffix in (".jsonl", ".ndjson"):
        rows = load_jsonl(path)
    else:
        raise ValueError(
            "Unsupported dataset format: %s (use .csv, .json, or .jsonl)"
            % suffix)

    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(rows)

    if limit is not None and limit > 0:
        rows = rows[:limit]

    return rows


def list_datasets() -> List[str]:
    """List available dataset files in ``data/datasets/``."""
    if not DEFAULT_DATASET_DIR.is_dir():
        return []
    return sorted(
        p.name for p in DEFAULT_DATASET_DIR.iterdir()
        if p.suffix.lower() in (".csv", ".json", ".jsonl", ".ndjson")
    )


__all__ = [
    "load_dataset", "load_csv", "load_json", "load_jsonl",
    "list_datasets", "DEFAULT_DATASET_DIR",
]
