# -*- coding: utf-8 -*-
"""
AISecurityTest 自动化扫描引擎。
对外暴露 AutoScanner，CLI 只需要调用它。
贡献者只需要：
- 加一个 YAML 用例：data/cases/*.yaml
- 加一个扫描 profile：data/autotest/profiles/*.yaml
- 加一个多轮策略：data/autotest/multi_turn/*.yaml
无需改动 Python 代码。
"""
from .scanner import AutoScanner, ScanResult
from .session import Session
from .strategy import STRATEGIES, get_strategy

__all__ = ["AutoScanner", "ScanResult", "Session", "STRATEGIES", "get_strategy"]