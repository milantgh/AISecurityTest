# -*- coding: utf-8 -*-
"""
多模态样本的统一数据结构与生成器抽象基类。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class MultimodalSample:
    """一个多模态注入样本。"""
    modality: str                  # "image" / "audio" / "pdf" / "csv"
    path: str                      # 生成的文件路径
    payload: str                   # 注入的原始载荷
    mode: str                      # 注入模式
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "modality": self.modality,
            "path": self.path,
            "payload": self.payload,
            "mode": self.mode,
            "metadata": self.metadata,
        }


class MultimodalGenerator(ABC):
    """多模态生成器抽象基类。"""

    modality = "base"
    # 子类覆盖：{mode_name: {"desc": "...", "dangerous": bool}}
    modes: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    def generate(self, payload, mode, out_path, **kwargs):
        # type: (str, str, str, **Any) -> MultimodalSample
        """生成注入样本，返回 MultimodalSample。"""
        raise NotImplementedError

    def list_modes(self):
        # type: () -> List[str]
        return list(self.modes.keys())

    def describe_modes(self):
        # type: () -> List[str]
        """返回可读的模式说明列表，供 CLI 显示。"""
        out = []
        for name, meta in self.modes.items():
            tag = " [危险]" if meta.get("dangerous") else ""
            out.append("  %-16s %s%s" % (name, meta.get("desc", ""), tag))
        return out