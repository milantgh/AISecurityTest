# -*- coding: utf-8 -*-
"""
PDF 注入生成器（PI-003）。
支持4种隐藏方式：白字、极小字、alpha=0 透明、页面外坐标。
依赖：reportlab（可选，未安装时抛 RuntimeError）。
"""
from .base import MultimodalGenerator, MultimodalSample

try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class PDFGenerator(MultimodalGenerator):
    modality = "pdf"

    modes = {
        "white_text": {
            "desc": "白色字体（肉眼不可见，PDF 文本提取可读到）",
            "dangerous": False,
        },
        "tiny_text": {
            "desc": "极小字号（肉眼难辨）",
            "dangerous": False,
        },
        "alpha_zero": {
            "desc": "完全透明（alpha=0）",
            "dangerous": False,
        },
        "off_page": {
            "desc": "页面外坐标（渲染时不可见）",
            "dangerous": False,
        },
    }

    def generate(self, payload, mode, out_path, **kwargs):
        # type: (str, str, str, **Any) -> MultimodalSample
        if not HAS_REPORTLAB:
            raise RuntimeError("未安装 reportlab。运行：pip install reportlab")
        if mode not in self.modes:
            raise ValueError("未知 PDF 注入模式：%s（可选：%s）"
                             % (mode, ", ".join(self.modes.keys())))
        path = make_injection_pdf(payload, mode=mode, out_path=out_path)
        return MultimodalSample(
            modality=self.modality,
            path=path,
            payload=payload,
            mode=mode,
            metadata={"page_size": "A4"},
        )


def _register_cn_font():
    """注册中文字体；失败时回退到 Helvetica。"""
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        return "Helvetica"


def make_injection_pdf(text, mode="white_text", out_path="sample.pdf"):
    """
    生成含隐藏注入载荷的 PDF。
    mode:
      - white_text 白字
      - tiny_text  极小字
      - alpha_zero 全透明
      - off_page   页面外坐标
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("未安装 reportlab。运行：pip install reportlab")
    if not text:
        raise ValueError("payload 不能为空")

    c = rl_canvas.Canvas(out_path, pagesize=A4)
    W, H = A4
    cn_font = _register_cn_font()

    # 正常业务内容
    c.setFont(cn_font, 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(50, H - 80, "【银行业务公告】")
    c.drawString(50, H - 110, "本行将于 2026 年 1 月 1 日起调整对公账户服务费。")
    c.drawString(50, H - 140, "详情请咨询各营业网点或拨打客服热线。")

    # 注入载荷
    if mode == "white_text":
        c.setFillColorRGB(1, 1, 1)
        c.setFont(cn_font, 12)
        c.drawString(50, H - 200, text)
    elif mode == "tiny_text":
        c.setFillColorRGB(0, 0, 0)
        c.setFont(cn_font, 2)
        c.drawString(50, H - 200, text)
    elif mode == "alpha_zero":
        try:
            c.setFillAlpha(0)
        except Exception:
            pass
        c.setFillColorRGB(0, 0, 0)
        c.setFont(cn_font, 12)
        c.drawString(50, H - 200, text)
    elif mode == "off_page":
        c.setFillColorRGB(1, 1, 1)
        c.setFont(cn_font, 12)
        c.drawString(-2000, -2000, text)
    else:
        raise ValueError("未知 PDF 注入模式：%s" % mode)

    # 附带零宽字符载荷（间接注入变体）
    from ..transforms import add_zw
    c.setFillColorRGB(1, 1, 1)
    c.setFont(cn_font, 10)
    c.drawString(50, H - 240, add_zw(text))

    c.showPage()
    c.save()
    return out_path