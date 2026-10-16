# -*- coding: utf-8 -*-
"""
视频注入生成器（PI-041）。
支持四条注入路径：
  1. subtitle    —— 字幕文件注入（SRT/ASS，纯文本，无第三方依赖）
  2. frames      —— 视频帧注入（复用image模块，需opencv-python）
  3. audio_track —— 音轨注入（复用 audio 模块，需系统 ffmpeg）
  4. metadata    —— 容器元数据注入（MP4/MKV 的 title/comment/description）
设计原则：
- subtitle 和 metadata 是纯标准库实现，保证任何时候都能用。
- frames 和 audio_track 依赖外部工具，未安装时给出明确提示。
"""
import os
import struct
import subprocess
import tempfile

from .base import MultimodalGenerator, MultimodalSample

# 可选依赖检测
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _has_ffmpeg():
    """检测系统是否有 ffmpeg 可执行文件。"""
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class VideoGenerator(MultimodalGenerator):
    modality = "video"

    modes = {
        "subtitle": {
            "desc": "字幕文件注入（SRT，纯文本，无第三方依赖）",
            "dangerous": False,
        },
        "frames": {
            "desc": "视频关键帧注入（需 opencv-python）",
            "dangerous": False,
        },
        "audio_track": {
            "desc": "音轨注入（需系统 ffmpeg）",
            "dangerous": False,
        },
        "metadata": {
            "desc": "容器元数据注入（MP4/MKV title/comment）",
            "dangerous": False,
        },
    }

    def generate(self, payload, mode, out_path, **kwargs):
        # type: (str, str, str, **Any) -> MultimodalSample
        if mode not in self.modes:
            raise ValueError("未知视频注入模式：%s（可选：%s）"
                             % (mode, ", ".join(self.modes.keys())))

        if mode == "subtitle":
            path = make_subtitle_injection(
                payload, out_path,
                fmt=kwargs.get("fmt", "srt"),
                video_path=kwargs.get("video_path"),
            )
        elif mode == "frames":
            if not HAS_CV2:
                raise RuntimeError(
                    "未安装 opencv-python。运行：pip install opencv-python\n"
                    "或者用 --mode subtitle（纯文本，无依赖）。")
            path = make_frame_injection(
                payload, out_path,
                video_path=kwargs.get("video_path"),
                frame_interval=kwargs.get("frame_interval", 30),
                image_mode=kwargs.get("image_mode", "white_on_white"),
            )
        elif mode == "audio_track":
            if not _has_ffmpeg():
                raise RuntimeError(
                    "未检测到系统 ffmpeg。\n"
                    "  安装：https://ffmpeg.org/download.html\n"
                    "  或者用 --mode subtitle（纯文本，无依赖）。")
            path = make_audio_track_injection(
                payload, out_path,
                video_path=kwargs.get("video_path"),
                audio_mode=kwargs.get("audio_mode", "hidden_16k"),
            )
        elif mode == "metadata":
            path = make_metadata_injection(
                payload, out_path,
                video_path=kwargs.get("video_path"),
            )
        else:
            raise ValueError("未知视频注入模式：%s" % mode)

        return MultimodalSample(
            modality=self.modality,
            path=path,
            payload=payload,
            mode=mode,
            metadata={
                "video_path": kwargs.get("video_path"),
                "note": "视频回读验证（字幕提取/关键帧 OCR/ASR）在第二批实现",
            },
        )


# ============================================================
# 1. 字幕注入（纯标准库）
# ============================================================
def make_subtitle_injection(payload, out_path="sample.srt", fmt="srt",
                            video_path=None):
    """
    生成含注入载荷的字幕文件。
    fmt: srt / ass
    video_path: 若非空，用 ffmpeg 把字幕合并进视频（需 ffmpeg）。
    """
    if not payload:
        raise ValueError("payload 不能为空")

    # 第一步：先生成字幕文件
    sub_path = out_path
    if video_path:
        # 合并到视频时，字幕写临时文件
        sub_path = out_path + ".srt"

    if fmt == "srt":
        _write_srt(sub_path, payload)
    elif fmt == "ass":
        _write_ass(sub_path, payload)
    else:
        raise ValueError("未知字幕格式：%s（可选：srt / ass）" % fmt)

    # 第二步：如果需要合并进视频
    if video_path:
        if not _has_ffmpeg():
            raise RuntimeError("合并字幕到视频需要系统 ffmpeg")
        if not os.path.exists(video_path):
            raise FileNotFoundError("视频文件不存在：%s" % video_path)
        _merge_subtitle(video_path, sub_path, out_path)
        os.remove(sub_path)

    return out_path


def _write_srt(path, payload):
    """写 SRT 字幕：前 5 秒正常内容，后 5 秒注入载荷。"""
    content = (
        "1\n"
        "00:00:00,000 --> 00:00:05,000\n"
        "【银行业务公告】本行将于 2026 年 1 月 1 日起调整对公账户服务费。\n"
        "\n"
        "2\n"
        "00:00:05,000 --> 00:00:10,000\n"
        "%s\n"
        "\n"
        "3\n"
        "00:00:10,000 --> 00:00:15,000\n"
        "详情请咨询各营业网点或拨打客服热线。\n"
    ) % payload
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_ass(path, payload):
    """写 ASS 字幕：注入载荷用极小字号 + 白色（渲染时几乎不可见）。"""
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1280\n"
        "PlayResY: 720\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Microsoft YaHei,32,&H00FFFFFF,&H000000FF,"
        "&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n"
        "Style: Hidden,Microsoft YaHei,2,&H00FFFFFF,&H000000FF,"
        "&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,10,10,10,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )
    events = (
        "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,"
        "【银行业务公告】本行将于 2026 年 1 月 1 日起调整对公账户服务费。\n"
        "Dialogue: 0,0:00:05.00,0:00:10.00,Hidden,,0,0,0,,%s\n"
        "Dialogue: 0,0:00:10.00,0:00:15.00,Default,,0,0,0,,"
        "详情请咨询各营业网点或拨打客服热线。\n"
    ) % payload
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + events)


def _merge_subtitle(video_path, srt_path, out_path):
    """用 ffmpeg 把 SRT 字幕硬编码进视频（burn-in）。"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "subtitles=%s" % srt_path.replace("\\", "/"),
        "-c:a", "copy",
        out_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=300)
    if result.returncode != 0:
        raise RuntimeError("ffmpeg 合并字幕失败：%s"
                           % result.stderr.decode("utf-8", errors="replace"))


# ============================================================
# 2. 关键帧注入（需 opencv-python）
# ============================================================
def make_frame_injection(payload, out_path="sample.mp4",
                         video_path=None, frame_interval=30,
                         image_mode="white_on_white"):
    """
    在视频关键帧上叠加图片注入载荷。
    - 如果 video_path 为空，生成一个纯色背景的测试视频。
    - frame_interval：每隔多少帧注入一次。
    - image_mode：复用 image.py 的注入模式。
    """
    if not HAS_CV2:
        raise RuntimeError("未安装 opencv-python")
    if not HAS_PIL:
        raise RuntimeError("未安装 pillow")

    from .image import make_injection_image
    from PIL import Image as PILImage
    import numpy as np

    # 打开或创建视频
    if video_path and os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    else:
        # 创建 10 秒 1280x720 测试视频
        fps = 25
        width, height = 1280, 720
        total = fps * 10
        cap = None

    # 先生成注入图片（放在角落）
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "inject.png")
        make_injection_image(payload, mode=image_mode, out_path=img_path,
                             width=640, height=120)
        inject_img = PILImage.open(img_path).convert("RGB")
        inject_arr = np.array(inject_img)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    frame_idx = 0
    while frame_idx < total:
        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                break
        else:
            # 生成纯灰背景
            frame = np.full((height, width, 3), 200, dtype=np.uint8)

        # 每隔 frame_interval 帧注入一次
        if frame_idx % frame_interval == 0:
            h_img, w_img = inject_arr.shape[:2]
            y0 = height - h_img - 20
            x0 = width - w_img - 20
            if y0 >= 0 and x0 >= 0:
                frame[y0:y0 + h_img, x0:x0 + w_img] = inject_arr

        writer.write(frame)
        frame_idx += 1

    if cap is not None:
        cap.release()
    writer.release()
    return out_path


# ============================================================
# 3. 音轨注入（需 ffmpeg）
# ============================================================
def make_audio_track_injection(payload, out_path="sample.mp4",
                               video_path=None,
                               audio_mode="hidden_16k"):
    """
    在视频音轨上叠加隐藏频段。
    - 如果 video_path 为空，生成一个带音轨的测试视频。
    - audio_mode：复用 audio.py 的注入模式。
    """
    if not _has_ffmpeg():
        raise RuntimeError("未检测到系统 ffmpeg")

    from .audio import make_injection_wav

    with tempfile.TemporaryDirectory() as tmpdir:
        # 生成注入音频
        wav_path = os.path.join(tmpdir, "inject.wav")
        make_injection_wav(out_path=wav_path, seconds=10,
                           freq_main=440, freq_hidden=16000, sample_rate=44100)

        if video_path and os.path.exists(video_path):
            # 替换原视频音轨
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", wav_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                out_path,
            ]
        else:
            # 生成纯色视频 + 注入音轨
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=gray:s=1280x720:d=10",
                "-i", wav_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                out_path,
            ]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, timeout=300)
        if result.returncode != 0:
            raise RuntimeError("ffmpeg 生成音轨视频失败：%s"
                               % result.stderr.decode("utf-8", errors="replace"))
    return out_path


# ============================================================
# 4. 容器元数据注入（纯标准库，MP4 box 写入）
# ============================================================
def make_metadata_injection(payload, out_path="sample.mp4",
                            video_path=None):
    """
    在视频容器元数据（MP4 的 comment/description box）中注入载荷。
    - 如果 video_path 为空，生成一个最小可用的 MP4 文件。
    - 采用直接写 MP4 box 的方式，不依赖第三方库。
    """
    if not payload:
        raise ValueError("payload 不能为空")

    if video_path and os.path.exists(video_path):
        # 复制原视频，追加自定义 box
        with open(video_path, "rb") as f:
            data = f.read()
    else:
        # 生成一个最小 MP4 骨架（含 ftyp + mdat + moov + udta）
        data = _minimal_mp4()

    # 在文件末尾追加 udta box 承载载荷
    # udta box 格式：[size(4)][type='udta'][内容]
    # 内容再嵌套 comment box
    comment = payload.encode("utf-8")
    comment_box = struct.pack(">I", len(comment) + 8) + b"cmnt" + comment
    udta_box = struct.pack(">I", len(comment_box) + 8) + b"udta" + comment_box

    with open(out_path, "wb") as f:
        f.write(data)
        f.write(udta_box)
    return out_path


def _minimal_mp4():
    """生成一个最小 MP4 骨架（ftyp box）。"""
    # ftyp box: [size][ftyp][major_brand][minor_version][compatible_brands...]
    major = b"isom"
    minor = struct.pack(">I", 0x200)
    compatible = b"isomiso2avc1mp41"
    ftyp = struct.pack(">I", 8 + 4 + 4 + len(compatible)) + b"ftyp" + major + minor + compatible
    return ftyp