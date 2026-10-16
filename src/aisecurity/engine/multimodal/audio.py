# -*- coding: utf-8 -*-
"""
音频注入生成器（PI-026）。
生成含隐藏频段的 WAV 文件：主频段是可听业务音，隐藏频段承载注入指令。
依赖：标准库 wave/struct/math，无第三方依赖。
采样率说明：
- 按奈奎斯特定理，可表示的最高频率=采样率/2。
- 信号频率必须严格小于奈奎斯特频率（等于边界时无法无失真重建）。
- 因此各模式的采样率都留有余量：
  * hidden_16k：16000 Hz 隐藏频段 → 44100 Hz 采样率（奈奎斯特 22050）
  * hidden_8k ：8000 Hz 隐藏频段 → 22050 Hz 采样率（奈奎斯特 11025）
  * audible  ：无隐藏频段 → 22050 Hz 采样率
"""
import math
import struct
import wave

from .base import MultimodalGenerator, MultimodalSample

class AudioGenerator(MultimodalGenerator):
    modality = "audio"

    modes = {
        "hidden_16k": {
            "desc": "16kHz 超声波频段隐藏（采样率 44100，人耳听不到）",
            "dangerous": False,
        },
        "hidden_8k": {
            "desc": "8kHz 高频段隐藏（采样率 22050，文件更小）",
            "dangerous": False,
        },
        "audible": {
            "desc": "可听频段（对照组，验证音频内容能被识别）",
            "dangerous": False,
        },
    }

    # 模式 -> (隐藏频段 Hz, 采样率 Hz)
    # 采样率必须 >= 2.2 * 隐藏频段，留出安全余量
    _MODE_CONFIG = {
        "hidden_16k": (16000, 44100),
        "hidden_8k":  (8000,  22050),
        "audible":    (None,  22050),   # 无隐藏频段
    }

    def generate(self, payload, mode, out_path, **kwargs):
        # type: (str, str, str, **Any) -> MultimodalSample
        if mode not in self.modes:
            raise ValueError("未知音频注入模式：%s（可选：%s）"
                             % (mode, ", ".join(self.modes.keys())))

        default_hidden, default_sr = self._MODE_CONFIG[mode]
        seconds = kwargs.get("seconds", 3)
        freq_main = kwargs.get("freq_main", 440)
        freq_hidden = kwargs.get("freq_hidden", default_hidden)
        sample_rate = kwargs.get("sample_rate", default_sr)

        path = make_injection_wav(
            out_path=out_path,
            seconds=seconds,
            freq_main=freq_main,
            freq_hidden=freq_hidden,
            sample_rate=sample_rate,
        )
        return MultimodalSample(
            modality=self.modality,
            path=path,
            payload=payload,
            mode=mode,
            metadata={
                "seconds": seconds,
                "freq_main": freq_main,
                "freq_hidden": freq_hidden,
                "sample_rate": sample_rate,
                "note": "payload 尚未编码进音频，第二批实现编码与回读",
            },
        )


def make_injection_wav(out_path="sample.wav", seconds=3,
                       freq_main=440, freq_hidden=16000, sample_rate=44100):
    """
    生成一段 WAV 音频：主频段 + 隐藏频段叠加。
    - freq_main：可听业务音
    - freq_hidden：隐藏频段，人耳通常听不到；为 None 时只生成主音
    - sample_rate：采样率，必须 > 2 * max(freq_main, freq_hidden)
    """
    if seconds <= 0:
        raise ValueError("seconds 必须为正数")
    if sample_rate <= 0:
        raise ValueError("sample_rate 必须为正数")

    nyquist = sample_rate / 2.0
    if freq_main >= nyquist:
        raise ValueError("freq_main (%d Hz) 必须小于采样率的一半（%d Hz）"
                         % (freq_main, int(nyquist)))
    if freq_hidden is not None and freq_hidden >= nyquist:
        # 给出更明确的修复建议：最小采样率 = 2.2 * freq_hidden
        min_sr = int(freq_hidden * 2.2)
        raise ValueError(
            "freq_hidden (%d Hz) 必须小于采样率的一半（%d Hz）。"
            "建议 --sample-rate >= %d。"
            "例如：16kHz 隐藏频段推荐 44100；8kHz 隐藏频段推荐 22050。"
            % (freq_hidden, int(nyquist), min_sr))

    total = int(sample_rate * seconds)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        chunk = 4096
        i = 0
        while i < total:
            n = min(chunk, total - i)
            buf = bytearray()
            for k in range(n):
                t = (i + k) / sample_rate
                v = 0.3 * math.sin(2 * math.pi * freq_main * t)
                if freq_hidden:
                    v += 0.15 * math.sin(2 * math.pi * freq_hidden * t)
                s = int(max(-1.0, min(1.0, v)) * 32767)
                buf += struct.pack("<h", s)
            w.writeframes(bytes(buf))
            i += n
    return out_path