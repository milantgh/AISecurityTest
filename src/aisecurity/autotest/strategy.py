# -*- coding: utf-8 -*-
"""
多轮注入策略。
策略从 data/autotest/multi_turn/*.yaml 加载，不写死在代码里。
贡献者加一个新策略：
1.在data/autotest/multi_turn/下新建 my_strategy.yaml
2.填好 name / description/turns模板
3.无需改 Python，get_strategy("my_strategy")就能用
"""
import os
from typing import Dict, List, Any, Optional

from ..core.loader import load_yaml, discover_yaml_files
from ..core.registry import CASE_LIB

def _strategy_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "autotest", "multi_turn")


class BaseStrategy:
    """所有多轮策略的基类。"""

    name = "base"

    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec or {}

    def build_turns(self, case_id: str, max_turns: int = 5) -> List[Dict[str, Any]]:
        """
        返回一组 turn，每个 turn 形如：
        {"label": "第1轮 - 无害寒暄", "payload": "...", "stop_on_hit": True}
        """
        raise NotImplementedError


class TemplateStrategy(BaseStrategy):
    """
    通用模板策略。turns 里每个元素是一段 Python 字符串模板，
    支持 {case_steps} 引用用例的原始 steps。
    """

    def build_turns(self, case_id, max_turns=5):
        case = CASE_LIB.get(case_id, {})
        steps = case.get("steps", [])
        case_steps = "\n".join(steps)

        turns_spec = self.spec.get("turns", [])
        out = []
        for i, t in enumerate(turns_spec[:max_turns]):
            if isinstance(t, str):
                payload = t.format(case_steps=case_steps)
                label = "turn %d" % (i + 1)
            else:
                payload = t.get("payload", "").format(case_steps=case_steps)
                label = t.get("label", "turn %d" % (i + 1))
            out.append({
                "label": label,
                "payload": payload,
                "stop_on_hit": True,
            })
        return out


_STRATEGY_CACHE: Optional[Dict[str, BaseStrategy]] = None


def _load_all() -> Dict[str, BaseStrategy]:
    """加载所有策略 YAML。"""
    global _STRATEGY_CACHE
    if _STRATEGY_CACHE is not None:
        return _STRATEGY_CACHE

    cache = {}
    d = _strategy_dir()
    if not os.path.isdir(d):
        _STRATEGY_CACHE = cache
        return cache

    for path in discover_yaml_files(__import__("pathlib").Path(d)):
        data, err = load_yaml(path)
        if err or not data:
            continue
        name = data.get("name") or os.path.splitext(path.name)[0]
        cache[name] = TemplateStrategy(data)

    _STRATEGY_CACHE = cache
    return cache


def get_strategy(name: str) -> Optional[BaseStrategy]:
    return _load_all().get(name)


def list_strategies() -> List[str]:
    return sorted(_load_all().keys())


STRATEGIES = property(lambda self: list_strategies())