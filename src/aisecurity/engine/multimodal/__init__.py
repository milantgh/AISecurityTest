# -*- coding: utf-8 -*-
"""
多模态载荷引擎。
本模块为纯逻辑层。
所有生成函数签名统一为 generate(payload, mode, out_path, **kwargs) -> MultimodalSample。

生成器：
  - image  ：图片注入（可见类 4 种 + 隐写类3种）
  - audio  ：音频注入（3 种频段模式）
  - pdf    ：PDF 注入（4 种隐藏方式）
  - csv    ：CSV 公式注入（4 模式×5载荷）
  - video  ：视频注入（4 条路径：字幕/关键帧/音轨/容器元数据）
"""
from .base import MultimodalSample, MultimodalGenerator
from .image import ImageGenerator, make_injection_image
from .audio import AudioGenerator, make_injection_wav
from .pdf import PDFGenerator, make_injection_pdf
from .csv_inject import CSVGenerator, make_injection_csv
from .video import VideoGenerator

__all__ = [
    "MultimodalSample",
    "MultimodalGenerator",
    "ImageGenerator",
    "AudioGenerator",
    "PDFGenerator",
    "CSVGenerator",
    "VideoGenerator",
    "make_injection_image",
    "make_injection_wav",
    "make_injection_pdf",
    "make_injection_csv",
    "GENERATORS",
]


# 名称 -> 生成器实例，供 CLI 遍历
GENERATORS = {
    "image": ImageGenerator(),
    "audio": AudioGenerator(),
    "pdf": PDFGenerator(),
    "csv": CSVGenerator(),
    "video": VideoGenerator(),
}