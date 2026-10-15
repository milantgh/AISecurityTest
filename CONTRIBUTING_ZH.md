# 贡献指南

感谢你想为 AISecurityTest 做贡献！本项目只需要你懂一件事就能贡献：往 YAML 文件里写用例。

## 三类贡献方式

### 1. 加用例（最容易，推荐第一次贡献选这个）

工作流：

第 1 步：查看已有分类名（避免重名）：

    aisec categories

第 2 步：拿下一个可用 ID：

    aisec next-id

第 3 步：检查你的分类名是否唯一：

    aisec check-name "你的新分类名"

第 4 步：看 `src/aisecurity/data/cases/_template.yaml`

第 5 步：找到对应的类别文件（比如 `direct_injection.yaml`）

第 6 步：在 `cases:` 下加一条新用例，字段照抄模板

第 7 步：本地运行 `aisec validate`，看到「✅ 全部用例校验通过」即可

第 8 步：提 PR

用例 ID 规范：

- 格式 `PI-XXX`，全局唯一
- 永远用下一个可用 ID——跑 `aisec next-id` 查看
- 不要预留号段、不要跳号
- 不要复用已有用例的 ID

风险等级：只能是 `严重` / `高` / `中-高` / `中` / `低`

### 2. 加一个新类别

1. 跑 `aisec categories` 查看已有分类名（避免重名）
2. 跑 `aisec next-id` 拿下一个可用 ID
3. 跑 `aisec check-name "你的类别名"` 确认不冲突
4. 复制 `src/aisecurity/data/cases/_template.yaml` 为 `你的类别名.yaml`
5. 填写 `meta` 部分（name 全局唯一，order 决定侧栏排序）
6. 在 `cases:` 下加用例，ID 用第 2 步拿到的号
7. `aisec validate` 通过后提 PR

### 3. 加目标适配器（需要会 Python）

参考 `src/aisecurity/targets/openai_compat.py`，实现 `Target` 抽象类的
`send()` 方法。

---

## 命名约定

文件名和分类名用同一个后缀。

| 后缀 | 场景 | 文件名 | 分类名 |
|---|---|---|---|
| （无） | 中文原始 | `direct_injection.yaml` | `直接提示注入` |
| `_en` | 英文 | `direct_injection_en.yaml` | `直接提示注入 EN` |
| `_ja` | 日文 | `direct_injection_ja.yaml` | `直接提示注入 JA` |
| `_v2` | 内容升级 | `direct_injection_v2.yaml` | `直接提示注入 v2` |
| `_financial` | 金融行业 | `direct_injection_financial.yaml` | `直接提示注入（金融）` |
| `_2025q4` | 时间批次 | `direct_injection_2025q4.yaml` | `直接提示注入 2025Q4` |

为什么这么约定：文件名同前缀的，在目录里排在一起；
分类名同前缀的，在侧栏里排在一起。用户一眼就知道它们属于同一类。

分类名必须全局唯一。两个文件用同一个 `meta.name`，第二个会被拒绝加载。
示例输出：

    $ aisec validate
    ...
    ⚠ 发现问题：
      - [my_file.yaml] 分类名 '直接提示注入' 已被 direct_injection.yaml 占用，本文件跳过。
        请改一个唯一的分类名（如 '直接提示注入 EN' / '直接提示注入 v2' / '直接提示注入（金融）'）。
        跑 `aisec categories` 查看已有分类名。

改个分类名就好了。

---

## 硬性规则

- ❌ 不要在用例文件里写恶意代码、真实 PII、真实密钥
- ❌ 不要重复定义已有的用例 ID
- ❌ 不要重复定义已有的分类名
- ✅ 用例中的「防御方案」必须有实际可操作性
- ✅ 引用外部资料时注明来源（OWASP / MITRE ATLAS / 论文等）

## 提 PR 前自检

跑：

    aisec validate

输出如下即通过：

    已加载 N 个类别，M 条用例。
    ...
    ✅ 全部用例校验通过。

## 本地开发

    git clone https://github.com/milantgh/AISecurityTest.git
    cd AISecurityTest
    pip install -e ".[dev]"
    aisec list
    aisec validate
    python -m pytest tests/ -v

## 代码风格

Python 部分用 `ruff`，行宽 100：

    pip install ruff
    ruff check src/

## 报告问题

用 GitHub Issues 报告 bug 和功能建议。
安全相关漏洞请勿公开 Issue，见 `SECURITY_ZH.md`。