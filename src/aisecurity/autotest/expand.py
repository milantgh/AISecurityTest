# -*- coding: utf-8 -*-
"""
Payload 变体扩展。
把一条基础 payload 扩展成 N 条变体（按变换矩阵笛卡尔积）。
"""
import itertools
from typing import List, Dict, Any, Callable

from ..engine import transforms as T
from ..core.marker import PAYLOAD_MARKER

# 变换字典：名称 → (函数, 说明)
TRANSFORMS = {
    "raw":         (None,          "原文，不变换"),
    "base64":      (T.to_b64,      "Base64 编码"),
    "hex":         (T.to_hex,      "Hex 转义"),
    "unicode":     (T.to_uni,      "Unicode 转义"),
    "zero_width":  (T.add_zw,      "零宽字符插入"),
    "case_mix":    (T.case_mix,    "随机大小写"),
    "similar":     (T.similar,     "形近字替换"),
    "html":        (T.wrap_html,   "HTML 注释包裹"),
    "code":        (T.wrap_code,   "代码块包裹"),
    "chatml_sys":  (T.chatml_sys,  "伪造 ChatML system 块"),
    "chatml_ast":  (T.chatml_ast,  "伪造 ChatML assistant 块"),
    "llama_inst":  (T.llama_inst,  "伪造 Llama INST 标记"),
}


def list_transforms() -> List[Dict[str, str]]:
    """列出所有可用变换。"""
    out = []
    for name, (fn, desc) in TRANSFORMS.items():
        out.append({"name": name, "desc": desc})
    return out


def expand_payload(
    payload: str,
    transform_names: List[str] = None,
    mark: bool = True,
) -> List[Dict[str, Any]]:
    """
    把一条 payload 扩展成多条变体。

    payload: 基础文本
    transform_names: 要用的变换名列表；None 表示只用 raw
    mark: 是否追加 <<AIST_OK>> 标记

    返回：[{"payload": "...", "transform": "base64", "transform_desc": "..."}, ...]
    """
    if not transform_names:
        transform_names = ["raw"]

    out = []
    for name in transform_names:
        if name not in TRANSFORMS:
            continue
        fn, desc = TRANSFORMS[name]
        text = payload

        # 在变换前先加标记，保证标记能进入变换
        if mark and PAYLOAD_MARKER not in text:
            text = text.rstrip("；;。.  \n") + " " + PAYLOAD_MARKER

        if fn is not None:
            try:
                text = fn(text)
            except Exception:
                continue

        out.append({
            "payload": text,
            "transform": name,
            "transform_desc": desc,
        })

    return out


def expand_matrix(
    payload: str,
    transform_names: List[str] = None,
    languages: List[str] = None,
    mark: bool = True,
) -> List[Dict[str, Any]]:
    """
    笛卡尔积扩展：变换 × 语言。

    languages: 语言代码列表（["zh", "en", "sw", ...]）；None 表示只用中文
    """
    if not transform_names:
        transform_names = ["raw"]
    if not languages:
        languages = ["zh"]

    out = []
    for lang in languages:
        translated = _translate(payload, lang)
        variants = expand_payload(translated, transform_names, mark=mark)
        for v in variants:
            v["language"] = lang
            out.append(v)
    return out


def _translate(text: str, lang: str) -> str:
    """调用现有 translate 模块。失败则返回原文。"""
    if lang == "zh":
        return text
    try:
        from ..engine.translate import translate_low_res, LOW_RES_LANGS
        name = None
        for k, v in LOW_RES_LANGS.items():
            if v == lang:
                name = k
                break
        if name:
            return translate_low_res(text, name)
    except Exception:
        pass
    return text


def count_variants(transform_names: List[str], languages: List[str]) -> int:
    """预估变体总数。"""
    t = len(transform_names) if transform_names else 1
    l = len(languages) if languages else 1
    return t * l


def parse_transform_list(s: str) -> List[str]:
    """解析 'base64,zero_width,similar' → ['base64', 'zero_width', 'similar']"""
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def parse_lang_list(s: str) -> List[str]:
    """解析 'zh,en,sw' → ['zh', 'en', 'sw']"""
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]