# -*- coding: utf-8 -*-
"""Basic tests for the text transform functions."""
from aisecurity.engine import transforms as T


def test_zero_width_inserts():
    out = T.add_zw("abc")
    assert "\u200b" in out
    assert out.replace("\u200b", "") == "abc"


def test_base64_roundtrip():
    import base64
    src = "hello world"
    enc = T.to_b64(src)
    dec = base64.b64decode(enc).decode("utf-8")
    assert dec == src


def test_hex_format():
    out = T.to_hex("AB")
    assert "\\x41" in out and "\\x42" in out


def test_unicode_escape():
    out = T.to_uni("A")
    assert out == "\\u0041"


def test_wrap_html():
    out = T.wrap_html("payload")
    assert out.startswith("<!--") and out.endswith("-->")


def test_chatml_sys():
    out = T.chatml_sys("test")
    assert out.startswith("<im_start>system") and out.endswith("<im_end>")


def test_llama_inst():
    out = T.llama_inst("test")
    assert "[/INST]" in out and "[INST]" in out


def test_get_transform_none():
    # "无" is the sentinel key used internally by transforms.TRANSFORM_MAP
    assert T.get_transform("无") is None
    assert T.get_transform("") is None
    assert T.get_transform(None) is None


def test_get_transform_ok():
    assert callable(T.get_transform("Base64"))
    assert callable(T.get_transform("零宽字符"))


def test_list_transforms():
    names = T.list_transforms()
    assert "Base64" in names
    assert "零宽字符" in names