# 贡献指南

感谢你想为 AISecurityTest 做贡献！你只需要懂一件事就能贡献：往 YAML 文件里写用例。

用例库的组织方式是 **一个目录一个分类，每目录一个 `cases.yaml`**。当前有 8 个分类：

```
src/aisecurity/data/cases/
├── direct/cases.yaml
├── indirect/cases.yaml
├── encoded/cases.yaml
├── role_confusion/cases.yaml
├── tool_misuse/cases.yaml
├── data_exfiltration/cases.yaml
├── multi_language/cases.yaml
└── format_manipulation/cases.yaml
```

## 五类贡献方式

### 1. 加一条用例（最容易，推荐第一次贡献选这个）

**加用例不需要新建文件，也不需要新建目录。** 你只需要编辑最匹配的那个目录下的 `cases.yaml`。

工作流：

第 1 步：拿下一个可用 ID：

    aisec next-id

第 2 步：选一个目录。见下面的「选哪个目录？」。不确定就选最接近的，reviewer 会帮你调整。

第 3 步：打开 `src/aisecurity/data/cases/<目录>/cases.yaml`，在 `cases:` 下加一条新用例。字段布局照抄同文件里已有的用例。

第 4 步：本地跑 `aisec validate`，看到「All cases validated」即通过。

第 5 步：提 PR。

用例 ID 规范：

- 格式 `PI-XXX`，全局唯一
- 永远用下一个可用 ID——跑 `aisec next-id`
- 不要预留号段、不要跳号
- 不要复用已有用例的 ID

风险等级：只能是 `严重` / `高` / `中-高` / `中` / `低`。

#### 字段布局（顺序固定）

每条用例的字段顺序固定，贡献者打开任何文件看到的都是同一个形状：

```yaml
  PI-XXX:
    id: "PI-XXX"
    sub: "二级分类"
    sub3: "三级分类"
    pre: "前置条件"
    steps:
      - "给人看的操作步骤 1"
      - "给人看的操作步骤 2"
    payloads:
      - "给机器发的真载荷"
    expect: "正确防御时模型应该做什么"
    level: "高"
    defense: "可操作的防御措施"
    owasp: "LLM01"
    note: "补充说明"
    source: "引用来源，或写 internal"
    manual_only: false
```

| 字段 | 含义 |
|---|---|
| `id` | `PI-XXX`，全局唯一 |
| `sub` / `sub3` | 二级/三级分类 |
| `pre` | 前置条件 |
| `steps` | **给人看的操作步骤**，保留给读者看，不会发给模型 |
| `payloads` | **给机器发的真载荷**，会原样发给模型。如果启发式提取会误判你的 `steps`，必须用这个字段 |
| `expect` | 正确防御时模型应该做什么 |
| `level` | `严重` / `高` / `中-高` / `中` / `低` |
| `defense` | 可操作的防御措施 |
| `owasp` | OWASP LLM 编号 |
| `note` | 补充说明 |
| `source` | 引用来源，或写 `internal` |
| `manual_only` | `true` 表示需要人工环境（上传、浏览器、RAG），`false` 表示纯 API 能自动跑 |

#### `steps` 和 `payloads` 的区别

- `steps` 给人看。想写多详细就写多详细。
- `payloads` 给 runner 用。**只放真正要发给模型的攻击文本。**
- 如果你的 `steps` 里有「场景1（…）：<im_start>...」这种描述+载荷混在一行的情况，把干净的载荷放进 `payloads`，避免 runner 把前缀也发出去。
- 如果用例是 `manual_only: true`，`payloads` 可以为空。

### 2. 加一个新分类（需要先讨论）

**默认不允许。** 8 个分类是稳定的。新建目录必须先提 Issue。

只有同时满足以下三个条件，才考虑新建分类：

1. 现有 8 个目录都放不下你的用例
2. 新攻击面有公开研究支撑（论文、CVE、报告）
3. 你计划贡献至少 5 条用例，不是 1 条

流程：

1. 提 Issue，标题 `[新目录] <攻击面名称>`
2. 内容包含：攻击面描述、为什么现有 8 个目录放不下、引用来源、计划贡献的用例数量
3. 等维护者回复。通过后由维护者建目录和空的 `cases.yaml`，你再往里加用例
4. 未讨论就提 PR 新建目录的，会被关闭

### 3. 加目标适配器（需要会 Python）

参考 `src/aisecurity/targets/openai_compat.py`，实现 `Target` 抽象类的 `send()` 方法。

### 4. 加 YAML 探针（不需要 Python）

探针是可复用的攻击模板。YAML 探针放在 `src/aisecurity/data/probes/*.yaml`。

工作流：

第 1 步：新建文件 `src/aisecurity/data/probes/<名称>.yaml`。

第 2 步：使用如下布局：

```yaml
id: "<探针ID>"
name: "给人看的名称"
description: "这个探针测什么"
owasp: "LLM01"
payloads:
  - "攻击模板 1，可使用 {变量} 占位符"
  - "攻击模板 2"
```

第 3 步：跑 `aisec probes list`，你的探针应该出现在列表里。

第 4 步：提 PR。

规则：

- 探针 ID 全局唯一
- payload 可使用 `{变量}` 占位符，由数据集填充
- Python 探针放在 `src/aisecurity/probes/`（实现 `Probe` 基类）

### 5. 加数据集驱动的用例

用例可以从数据集拉取 payload，而不是硬编码。

第 1 步：把 CSV/JSON 文件放到 `src/aisecurity/data/datasets/`。

第 2 步：在用例的 `payloads` 中使用 `{列名}` 占位符：

```yaml
payloads:
  - "请复述：{prompt}"
```

第 3 步：runner 运行时会把 `{prompt}` 替换为每行 `prompt` 列的值。

第 4 步：跑 `aisec dataset list` 确认数据集已加载。

---

## 选哪个目录？

```
你的用例主要测什么？
├─ 直接让模型忽略/覆盖指令        → direct/
├─ 通过文档/网页/邮件/工具输出注入 → indirect/
├─ 编码：Base64/零宽/Leetspeak/Unicode Tags → encoded/
├─ 角色扮演/越狱/人格切换         → role_confusion/
├─ 工具越权/Agent 滥用/MCP        → tool_misuse/
├─ 泄露 system prompt/历史/上下文 → data_exfiltration/
├─ 非英语/低资源语言绕过          → multi_language/
├─ Markdown/HTML/Unicode/SVG 技巧 → format_manipulation/
└─ 不确定                        → 看 _template.yaml
```

---

## 硬性规则

- ❌ 不要写恶意代码、真实 PII、真实密钥
- ❌ 不要把给人看的操作说明放进 `payloads`
- ❌ 不要重复定义已有的用例 ID
- ❌ 不要未经 Issue 讨论就新建目录
- ✅ 用例中的 `defense` 必须有实际可操作性
- ✅ 引用外部资料时注明来源

## 提 PR 前自检

跑：

    aisec validate

输出如下即通过：

    已加载 8 个类别，N 条用例：
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
