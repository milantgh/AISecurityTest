# -*- coding: utf-8 -*-
"""
autoscan输出日志器，支持多级详细度。
详细度等级：
  0 - quiet    只打印最终报告
  1 - normal   打印用例级进度（默认）
  2 - verbose  打印 payload 级别进度
  3 - debug    打印 payload + 完整响应 + 评估细节
"""
import sys
import shutil

# 终端颜色（Windows 10+ 支持，旧版自动降级）
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"


def _supports_color():
    """检测终端是否支持 ANSI 颜色。"""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    # Windows 10+ 需要额外检测，这里简化处理
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # 启用虚拟终端处理
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True


class Logger:
    """autoscan 输出日志器。"""

    def __init__(self, level: int = 1, color: bool = None):
        """
        level: 0=quiet, 1=normal, 2=verbose, 3=debug
        color: None=自动检测, True=强制开启, False=强制关闭
        """
        self.level = level
        if color is None:
            color = _supports_color()
        self.color = color
        self._term_width = shutil.get_terminal_size((100, 24)).columns

    # ---------- 底层打印 ----------
    def _c(self, text: str, color_code: str) -> str:
        if not self.color:
            return text
        return color_code + text + C.RESET

    def _print(self, text: str):
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    # ---------- 分隔线 ----------
    def _line(self, char: str = "─", width: int = None):
        if width is None:
            width = min(self._term_width, 80)
        return char * width

    # ---------- 用例级 ----------
    def case_start(self, case_id: str, title: str = ""):
        if self.level < 1:
            return
        bar = self._line("═", 70)
        self._print(self._c("[autoscan] " + bar, C.CYAN))
        msg = "[autoscan] [%s] 用例启动" % case_id
        if title:
            msg += " — " + title
        self._print(self._c(msg, C.BOLD + C.CYAN))
        self._print(self._c("[autoscan] " + bar, C.CYAN))
        self._print("")

    def case_done(self, case_id: str, total: int, hits: int, errors: int, elapsed: float):
        if self.level < 1:
            return
        self._print("")
        msg = "[autoscan] [%s] 完成 · %d payload · %d 命中 · %d 错误 · 耗时 %.1fs" % (
            case_id, total, hits, errors, elapsed
        )
        color = C.GREEN if hits > 0 else (C.RED if errors > 0 else C.DIM)
        self._print(self._c(msg, color))
        self._print(self._c("[autoscan] " + self._line("═", 70), C.CYAN))
        self._print("")

    # ---------- payload 级 ----------
    def payload_start(self, idx: int, total: int):
        if self.level < 2:
            return
        self._print(self._c(
            "[autoscan] ── payload #%d/%d %s" % (idx, total, self._line("─", 40)),
            C.DIM
        ))

    def payload_sent(self, payload: str, endpoint: str, model: str):
        if self.level < 2:
            return
        # 多行 payload 缩进显示
        self._print(self._c("[autoscan] → Payload:", C.BOLD))
        for line in payload.split("\n"):
            self._print(self._c("[autoscan]   " + line, C.WHITE))
        if self.level >= 3:
            self._print(self._c(
                "[autoscan] → 发送到: %s (model=%s)" % (endpoint, model), C.DIM))

    def payload_response(self, response: str, latency_ms: int = 0,
                         tokens_in: int = 0, tokens_out: int = 0):
        if self.level < 2:
            return
        meta = ""
        if latency_ms:
            meta += "%dms" % latency_ms
        if tokens_out:
            meta += ", %d tokens" % tokens_out
        if meta:
            self._print(self._c("[autoscan] → 响应 (%s):" % meta, C.BOLD))
        else:
            self._print(self._c("[autoscan] → 响应:", C.BOLD))

        if self.level >= 3:
            # debug 级别：完整响应
            for line in (response or "").split("\n"):
                self._print(self._c("[autoscan]   " + line, C.WHITE))
        else:
            # verbose 级别：截断响应
            text = (response or "").strip()
            if len(text) > 300:
                text = text[:300] + "..."
            for line in text.split("\n"):
                self._print(self._c("[autoscan]   " + line, C.WHITE))

    def payload_evals(self, eval_results):
        if self.level < 2:
            return
        if not eval_results:
            return
        self._print(self._c("[autoscan] → 评估:", C.BOLD))
        for er in eval_results:
            name = getattr(er, "name", "?")
            hit = getattr(er, "hit", False)
            detail = getattr(er, "detail", "")
            if hit:
                mark = self._c("HIT ", C.BG_GREEN + C.WHITE) + " " + self._c(name, C.GREEN)
            else:
                mark = self._c("miss", C.DIM) + " " + self._c(name, C.DIM)
            self._print("[autoscan]   [%s] %s — %s" % (mark, "", detail))

    def payload_error(self, error: str):
        if self.level < 2:
            return
        self._print(self._c("[autoscan] → 错误: " + str(error), C.RED))

    def payload_result(self, success: bool, error: bool):
        if self.level < 2:
            return
        if error:
            tag = self._c("❌ ERROR", C.RED)
        elif success:
            tag = self._c("✅ HIT", C.BG_GREEN + C.WHITE)
        else:
            tag = self._c("· miss", C.DIM)
        self._print("[autoscan] → 结论: %s" % tag)
        self._print("")

    # ---------- 汇总级 ----------
    def scan_start(self, target: str, model: str, profile: str, total_cases: int):
        if self.level < 1:
            return
        self._print(self._c("[autoscan] " + self._line("═", 70), C.CYAN))
        self._print(self._c("[autoscan] 扫描启动", C.BOLD + C.CYAN))
        self._print(self._c("[autoscan]   目标:   %s" % target, C.WHITE))
        self._print(self._c("[autoscan]   模型:   %s" % model, C.WHITE))
        self._print(self._c("[autoscan]   Profile: %s" % profile, C.WHITE))
        self._print(self._c("[autoscan]   用例数: %d" % total_cases, C.WHITE))
        self._print(self._c("[autoscan] " + self._line("═", 70), C.CYAN))
        self._print("")

    def scan_done(self, result):
        if self.level < 1:
            return
        self._print(self._c("[autoscan] " + self._line("═", 70), C.CYAN))
        self._print(self._c("[autoscan] 扫描完成", C.BOLD + C.CYAN))
        self._print("[autoscan]   用例数:   %d" % result.total_cases)
        self._print("[autoscan]   Payload:  %d" % result.total_payloads)
        hits_color = C.GREEN if result.hits > 0 else C.DIM
        self._print(self._c("[autoscan]   命中:     %d" % result.hits, hits_color))
        if result.errors > 0:
            self._print(self._c("[autoscan]   错误:     %d" % result.errors, C.YELLOW))
        self._print("[autoscan]   命中率:   %.2f%%" % (result.hit_rate * 100))
        self._print("[autoscan]   耗时:     %.1f 秒" % result.duration_sec)
        self._print(self._c("[autoscan] " + self._line("═", 70), C.CYAN))

    # ---------- 通用提示 ----------
    def info(self, msg: str):
        if self.level < 1:
            return
        self._print(self._c("[autoscan] " + msg, C.CYAN))

    def warn(self, msg: str):
        if self.level < 1:
            return
        self._print(self._c("[autoscan] [!] " + msg, C.YELLOW))

    def error(self, msg: str):
        self._print(self._c("[autoscan] [x] " + msg, C.RED))

    def debug(self, msg: str):
        if self.level < 3:
            return
        self._print(self._c("[autoscan] [debug] " + msg, C.DIM))