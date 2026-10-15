# 测试指南（Testing Guide）

本文说明本项目的测试体系：`tests/` 目录结构、pytest 工作原理、常用命令、如何加新测试。

---

## 一、pytest 是什么

pytest 是 Python 的测试框架。它的作用是：

```
你写代码  →  代码可能改坏  →  pytest 帮你自动发现
```

**没有 pytest 时**：

- 你改了一行代码，不知道有没有影响其他地方
- 只能手动打开程序，点一遍所有功能，看有没有崩

**有 pytest 时**：

- 你改完代码，跑一条命令
- 3 秒后它告诉你："32 个检查全部通过" 或 "第 7 个检查失败"

---

## 二、tests/ 目录结构

本项目的 `tests/` 目录长这样，每个文件测什么一目了然：

```
tests/
├── __init__.py                      让 tests 成为 Python 包（空文件）
├── conftest.py                      pytest 全局配置
│                                    · 把 src/ 加进 sys.path
│                                    · 未安装也能直接跑测试
├── test_registry.py                 测「用例库加载」
│                                    · 所有类别、用例能不能正常加载？
│                                    · ID 有没有重复？字段有没有缺？
├── test_marker.py                   测「回执标记机制」
│                                    · <<AIST_OK>> 能不能被正确识别？
│                                    · 大小写变体、空字符串边界情况
├── test_transforms.py               测「文本变换函数」
│                                    · Base64 编解码可逆吗？
│                                    · 零宽字符真的插进去了吗？
├── test_evaluators.py               测「评估器」
│                                    · marker 评估器命中/未命中判定
│                                    · regex 评估器能抓手机号、身份证、API Key
└── test_runner_integration.py       测「整条链路端到端」
                                     · 生成载荷 → 发送 → 评估 → 判定
                                     · 用假 Target 模拟，不联网
```

### 每个文件的职责

| 文件 | 测什么 | 对应源码 |
|---|---|---|
| `test_registry.py` | 用例能否正确加载、校验、去重 | `src/aisecurity/core/registry.py` |
| `test_marker.py` | 回执标记 `<<AIST_OK>>` 的识别 | `src/aisecurity/core/marker.py` |
| `test_transforms.py` | 文本变换的正确性 | `src/aisecurity/engine/transforms.py` |
| `test_evaluators.py` | 评估器（marker / regex）判定 | `src/aisecurity/evaluators/` |
| `test_runner_integration.py` | 整条链路端到端 | `src/aisecurity/runner/` |

### 为什么每个模块都要有独立的测试文件

- **对号入座**：哪个模块出问题，一眼就知道该看哪个 test 文件
- **新人上手**：想知道某个模块怎么用，看它对应的 test 文件最快
- **PR 审查**：改 A 模块的人主要跑 `test_A.py`，不用全量跑

---

## 三、pytest 的工作原理

### 3.1 完整流程

当你运行 `python -m pytest tests/ -v` 时，pytest 依次做这些事：

```
① 发现（Discovery）
   └─ 扫描目录，找出所有 test_*.py 文件

② 收集（Collection）
   └─ 每个文件里，找出所有 test_* 函数

③ 执行（Execution）
   └─ 逐个调用函数，执行里面的 assert
      （assert 成立 → PASS；不成立 → FAIL）

④ 汇报（Reporting）
   └─ 汇总结果：多少通过、多少失败、耗时
```

### 3.2 一个最简单的例子

```python
# tests/test_example.py

def test_addition():
    assert 1 + 1 == 2          # ✅ 通过

def test_base64_roundtrip():
    src = "hello 世界"
    enc = to_b64(src)
    dec = base64.b64decode(enc).decode("utf-8")
    assert dec == src          # ✅ 通过

def test_will_fail():
    assert 1 + 1 == 3          # ❌ 失败
```

跑 `pytest` 后输出：

```
tests/test_example.py::test_addition PASSED
tests/test_example.py::test_base64_roundtrip PASSED
tests/test_example.py::test_will_fail FAILED
```

### 3.3 核心机制：assert

`assert` 是 pytest 的灵魂。它做一件事：**检查条件是否成立**。

```python
assert 条件             # 条件为真 → PASS
assert 条件, "错误说明"  # 条件为假 → FAIL，并打印错误说明
```

**实际例子**（来自 `tests/test_marker.py`）：

```python
def test_exact_marker():
    ok, found = check_payload_kept("前缀 <<AIST_OK>> 后缀")
    assert ok
    assert found == "<<AIST_OK>>"
```

如果哪天你改坏了 `check_payload_kept()` 函数，这个测试立即失败：

```
FAILED tests/test_marker.py::test_exact_marker
AssertionError: assert False
```

**5 秒内就知道哪里错了。**

### 3.4 命名约定

pytest 通过**文件名前缀**和**函数名前缀**来自动发现测试：

**文件**：
- ✅ `test_registry.py`
- ❌ `registry_test.py`（不会被发现）

**函数**：
- ✅ `def test_exact_marker():`
- ❌ `def check_exact_marker():`（不会被调用）

---

## 四、常用命令

### 4.1 跑全部测试

```bash
python -m pytest tests/ -v
```

**预期**：全部通过（当前 32 个测试）

### 4.2 只跑某个文件

```bash
python -m pytest tests/test_transforms.py -v
```

### 4.3 只跑某个函数

```bash
python -m pytest tests/test_transforms.py::test_base64_roundtrip -v
```

### 4.4 遇到失败立即停

```bash
python -m pytest tests/ -x
```

### 4.5 显示每个测试耗时

```bash
python -m pytest tests/ --durations=10
```

### 4.6 只跑名字含某个关键词的测试

```bash
python -m pytest tests/ -k marker -v
```

### 4.7 看测试覆盖率

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src/aisecurity --cov-report=term-missing
```

**输出示例**：

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
aisecurity/core/registry.py         80      5    94%
aisecurity/engine/transforms.py     40      2    95%
aisecurity/runner/runner.py         30      3    90%
```

**Cover 越高 = 测试越全。** 开源项目一般追求 70%+，优秀项目 90%+。

---

## 五、怎么加一个新测试

假设你加了一个新功能：`src/aisecurity/engine/new_feature.py`。

### 第 1 步：创建测试文件

```
tests/test_new_feature.py
```

### 第 2 步：写测试

```python
# -*- coding: utf-8 -*-
"""测试 new_feature 模块。"""
from aisecurity.engine.new_feature import my_function


def test_basic_case():
    """基本功能测试。"""
    result = my_function("input")
    assert result == "expected"


def test_edge_case():
    """边界情况测试。"""
    result = my_function("")
    assert result == ""


def test_error_case():
    """错误处理测试。"""
    import pytest
    with pytest.raises(ValueError):
        my_function(None)
```

### 第 3 步：跑测试

```bash
python -m pytest tests/test_new_feature.py -v
```

### 第 4 步：和功能一起提交

```bash
git add src/aisecurity/engine/new_feature.py tests/test_new_feature.py
git commit -m "feat: add new_feature with tests"
```

**约定**：**新功能 + 新测试，一起提交。**

---

## 六、测试和 CI 的联动

项目有 `.github/workflows/validate.yaml`：

```yaml
- name: Run tests
  run: |
    pip install pytest
    python -m pytest tests/ -v
```

每次别人 push 代码 / 提 PR：

1. GitHub 自动拉取代码
2. 自动跑 `pytest`
3. 自动跑 `aisec validate`
4. 根据结果决定是否允许合并

**结果**：

- 绿 ✅ → 允许合并
- 红 ❌ → 拦住，告诉他哪里坏了

**这就是"能火的开源项目"都有测试和 CI 的原因。**

---

## 七、养成好习惯

### 7.1 改完代码 → 立即跑 pytest

```bash
python -m pytest tests/ -q
```

`-q` 是 quiet 模式，只显示结果。

**3 秒就知道有没有改坏东西。**

### 7.2 提交前跑一遍完整测试

```bash
python -m pytest tests/ -v
```

**绿了再提交。**

### 7.3 加新功能时也要加新测试

**约定**：新功能文件 + 新测试文件 → 一起提交。

### 7.4 覆盖率下降要警惕

如果你加了几百行代码但没加测试，覆盖率会下降。**定期看覆盖率，发现下降就补测试**。

---

## 八、常见问题

### Q1：测试跑得很慢怎么办

```bash
python -m pytest tests/ --durations=10     # 找出慢测试
pip install pytest-xdist                   # 装并行插件
python -m pytest tests/ -n auto            # 并行跑
```

### Q2：测试报"ModuleNotFoundError"

检查：

1. 在项目根目录跑（不是 `tests/` 里）
2. `tests/conftest.py` 存在（负责把 `src/` 加进路径）
3. 跑命令用 `python -m pytest`，不是 `pytest`

### Q3：测试连不上外部服务

**测试不应该依赖外部服务。** 用假对象替代：

```python
class FakeTarget(Target):
    def send(self, payload, **kwargs):
        return TargetResponse(text="固定响应")
```

**本项目所有测试都不联网。**

### Q4：pytest 找不到测试

- 文件名必须是 `test_*.py` 或 `*_test.py`
- 函数名必须以 `test_` 开头
- 如果在子目录，确保该目录有 `__init__.py`

---

## 九、一句话总结

> **pytest 是你项目的"自动质检员"。**
>
> 它让你放心改代码、放心接受别人的 PR、半年后还能回来改。
>
> 没有测试的项目，半年后就没人敢碰。
> 有测试的项目，才会越做越大。

---

## 十、相关文件

| 文件 | 用途 |
|---|---|
| `pyproject.toml` | 配置 pytest 的 `testpaths` 和 `pythonpath` |
| `tests/conftest.py` | 把 `src/` 加进 `sys.path` |
| `.github/workflows/validate.yaml` | CI 自动跑测试 |
| `src/aisecurity/core/registry.py` | 用例注册表（被测对象） |

---

## 十一、延伸阅读

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 覆盖率插件](https://pytest-cov.readthedocs.io/)
- [测试驱动开发（TDD）](https://en.wikipedia.org/wiki/Test-driven_development)