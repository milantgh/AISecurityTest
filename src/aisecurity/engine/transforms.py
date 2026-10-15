# -*- coding: utf-8 -*-
"""
Text transform toolbox.
All functions have the same signature: (text: str) -> str.
"""
import base64
import random
import re

ZW = "\u200b"


def add_zw(t):
    """Insert zero-width characters between each character."""
    return ZW.join(list(t))


def to_b64(t):
    """Base64 encode (UTF-8)."""
    return base64.b64encode(t.encode("utf-8")).decode()


def to_hex(t):
    """Hex escape."""
    return " ".join("\\x%02x" % ord(c) for c in t)


def to_uni(t):
    """Unicode escape."""
    return "".join("\\u%04x" % ord(c) for c in t)


def case_mix(t):
    """Random case mixing."""
    return "".join(c.upper() if random.random() > 0.5 else c.lower() for c in t)


# Homoglyph substitution table for Chinese characters.
SIM = {
    "忽": "忽", "略": "畧", "所": "所", "有": "冇", "指": "栺", "令": "囹",
    "系": "係", "统": "統", "安": "桉", "全": "荃", "规": "規", "则": "則",
    "输": "輸", "出": "齣", "客": "愙", "户": "戶", "密": "宻", "钥": "鑰",
}


def similar(t):
    """Homoglyph substitution."""
    for k, v in SIM.items():
        t = t.replace(k, v)
    return t


def wrap_html(t):
    """Wrap in an HTML comment."""
    return "<!-- %s -->" % t


def wrap_code(t):
    """Wrap in a Markdown code block."""
    return "```\n%s\n```" % t


def chatml_sys(t):
    """Forge a ChatML system block."""
    return "<im_start>system %s <im_end>" % t


def chatml_ast(t):
    """Forge a ChatML assistant block."""
    return "<im_start>assistant %s <im_end>" % t


def llama_inst(t):
    """Forge a Llama INST marker."""
    return "[/INST] %s [INST]" % t


def strip_ws(t):
    """Strip leading/trailing whitespace."""
    return t.strip()


def collapse_ws(t):
    """Collapse consecutive whitespace."""
    return re.sub(r"[ \t]+", " ", t)


def trim_lines(t):
    """Drop empty lines and trailing whitespace on each line."""
    return "\n".join(line.rstrip() for line in t.splitlines() if line.strip())


# Name -> function mapping (for UI / CLI).
# Keys stay in Chinese because cmd_transform.py --method uses them.
TRANSFORM_MAP = {
    "零宽字符": add_zw,
    "Base64": to_b64,
    "Hex": to_hex,
    "Unicode转义": to_uni,
    "大小写混淆": case_mix,
    "形近字替换": similar,
    "HTML注释": wrap_html,
    "代码块": wrap_code,
    "ChatML-sys": chatml_sys,
    "ChatML-ast": chatml_ast,
    "Llama-INST": llama_inst,
    "去首尾空白": strip_ws,
    "合并空白": collapse_ws,
    "清理空行": trim_lines,
}


def get_transform(name):
    """Return the transform function by name; None means no transform."""
    if name in ("无", None, ""):
        return None
    return TRANSFORM_MAP.get(name)


def list_transforms():
    """List all available transform names."""
    return list(TRANSFORM_MAP.keys())