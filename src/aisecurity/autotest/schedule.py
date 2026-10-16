# -*- coding: utf-8 -*-
"""
扫描 profile 加载。
profile 定义"扫哪些用例"：可以是用例 ID 列表，也可以用 filter 条件。
"""
import os
from pathlib import Path
from typing import Dict, Any

from ..core.loader import load_yaml, discover_yaml_files

def _profile_dir() -> Path:
    here = Path(__file__).resolve().parent
    return here.parent / "data" / "autotest" / "profiles"


def list_profiles():
    d = _profile_dir()
    if not d.is_dir():
        return []
    return [p.stem for p in discover_yaml_files(d)]


def load_profile(name: str) -> Dict[str, Any]:
    """加载一个 profile。name 不带 .yaml 后缀。"""
    d = _profile_dir()
    path = d / (name + ".yaml")
    if not path.exists():
        # 允许传完整文件名
        alt = d / name
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError("profile not found: %s" % name)
    data, err = load_yaml(path)
    if err:
        raise RuntimeError("load profile failed: %s" % err)
    return data or {}