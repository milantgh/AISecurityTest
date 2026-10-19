# 架构说明

本文说明 AISecurityTest 的内部结构。

## 分层设计

```
┌─────────────────────────────────────────────┐
│ cli/            ← 命令行入口                │
├─────────────────────────────────────────────┤
│ runner/         ← 编排层：用例 × 目标 × 评估 │
├─────────────────────────────────────────────┤
│ engine/ targets/ evaluators/                │
│                 ← 能力层，纯逻辑             │
├─────────────────────────────────────────────┤
│ core/ data/cases/  ← 数据层，无副作用        │
└─────────────────────────────────────────────┘
```

**铁律**：箭头只能自上而下依赖。`core/` 和 `engine/` 绝不 import `cli/`。

## 目录结构

```
src/aisecurity/
├── __init__.py               对外 API 与版本号
├── _version.py               版本常量
│
├── core/                     数据层——无副作用
│   ├── __init__.py
│   ├── schema.py             用例数据结构与校验
│   ├── loader.py             YAML / 模块加载工具
│   ├── registry.py           用例注册表（防御性加载）
│   ├── marker.py             回执标记机制
│   └── errors.py             统一异常
│
├── data/                     数据文件
│   └── cases/                15 个 YAML 文件，40 条用例
│       ├── _template.yaml    贡献模板
│       ├── direct_injection.yaml
│       ├── indirect_injection.yaml
│       └── ...
│
├── engine/                   攻击载荷引擎——纯函数
│   ├── __init__.py
│   ├── payload.py            按用例生成载荷
│   ├── compose.py            三层组合
│   ├── transforms.py         文本变换工具箱
│   ├── translate.py          低资源语言翻译
│   └── rewrite.py            AI 改写（OpenAI 兼容 / Ollama）
│
├── targets/                  目标适配器
│   ├── __init__.py
│   ├── base.py               Target 抽象基类
│   └── openai_compat.py      OpenAI 兼容 API 适配器
│
├── evaluators/               攻击成功判定
│   ├── __init__.py
│   ├── base.py               Evaluator 抽象基类
│   ├── marker_eval.py        回执标记检测
│   └── regex_eval.py         正则敏感信息检测
│
├── runner/                   编排
│   ├── __init__.py
│   ├── runner.py             用例 × 目标 × 评估器
│   └── result.py             结果对象
│
└── cli/                      命令行——13 个命令
    ├── __init__.py
    ├── main.py               `aisec` 入口
    ├── cmd_list.py           aisec list
    ├── cmd_validate.py       aisec validate
    ├── cmd_run.py            aisec run
    ├── cmd_export.py         aisec export（md / json / html / docx / xlsx）
    ├── cmd_next_id.py        aisec next-id
    ├── cmd_categories.py     aisec categories
    ├── cmd_check_name.py     aisec check-name
    ├── cmd_show.py           aisec show
    ├── cmd_gen.py            aisec gen
    ├── cmd_compose.py        aisec compose
    ├── cmd_transform.py      aisec transform
    ├── cmd_rewrite.py        aisec rewrite
    └── cmd_pipeline.py       aisec pipeline
```

## 数据流

```
YAML 用例
   ↓ (core/registry: 加载 + 校验)
CASE_LIB
   ↓ (engine/payload: 生成)
payloads: List[str]
   ↓ (targets/*: 发送)
responses: List[TargetResponse]
   ↓ (evaluators/*: 判定)
EvalResults
   ↓ (cli/cmd_run 或 report/*)
输出
```

## 扩展点

项目有四个扩展点，每个对应一类贡献者。

| 扩展点 | 目录 / 文件 | 面向人群 |
|---|---|---|
| 加用例 | `src/aisecurity/data/cases/*.yaml` | 安全分析师 |
| 加目标适配器 | `src/aisecurity/targets/*.py` | 开发者 |
| 加评估器 | `src/aisecurity/evaluators/*.py` | 安全研究员 |
| 加文本变换 | `src/aisecurity/engine/transforms.py` | 红队工程师 |

### 加用例（不需要 Python）

1. 跑 `aisec categories` 查看已有分类名
2. 跑 `aisec next-id` 拿下一个可用 ID
3. 跑 `aisec check-name "你的分类名"` 检查是否冲突
4. 复制 `data/cases/_template.yaml`
5. 找到对应的类别文件（如 `direct_injection.yaml`）
6. 在 `cases:` 下加一条新用例，ID 用第 2 步拿到的号
7. 跑 `aisec validate`，看到「✅ 全部用例校验通过」即可
8. 提 PR

### 加目标适配器（需要 Python）

1. 复制 `targets/openai_compat.py`
2. 实现 `Target` 抽象基类的 `send()` 方法
3. 如需 CLI 支持，在 `cli/cmd_run.py` 中注册

### 加评估器（需要 Python）

1. 复制 `evaluators/marker_eval.py`
2. 实现 `Evaluator` 基类的 `evaluate(payload, response_text)` 方法
3. 在 `evaluators/__init__.py` 的 `build_evaluators()` 中注册

## 用例 ID 命名

- 格式：`PI-XXX`
- **全局唯一**——ID 顺序递增，不按类别分段
- 跑 `aisec next-id` 拿下一个可用 ID
- 跨文件冲突会被 registry 拒绝加载
- 当前范围：PI-001 ~ PI-040

## 分类名命名

- **全局唯一**——重复的 `meta.name` 会被拒绝加载
- 变体用后缀区分：`_en`、`_ja`、`_v2`、`_financial`、...
- 文件名和分类名应保持同一个后缀
  （如 `direct_injection_en.yaml` ↔ `直接提示注入 EN`）

## 防御性加载

registry 逐个文件独立加载：

- 语法错 / 导入错 → 该文件跳过，其它正常
- 字段缺失 → 记录到 `LOAD_ERRORS`，`aisec validate` 可见
- 用例 ID / 分类名冲突 → 保留先到者，报出冲突
- 单个文件里坏用例过半 → 整体跳过

**效果**：任何坏文件丢进 `data/cases/`，都不会让程序起不来。

## CLI 命令（13 个）

| 命令 | 用途 |
|---|---|
| `aisec list` | 列出类别和用例 |
| `aisec validate` | 校验全部用例（CI 使用） |
| `aisec run` | 对目标执行用例 |
| `aisec export` | 导出用例（md / json / html / docx / xlsx） |
| `aisec next-id` | 显示下一个可用用例 ID |
| `aisec categories` | 列出所有分类名（一行一个） |
| `aisec check-name <name>` | 检查分类名是否已被占用 |
| `aisec show [case_id]` | 显示用例详情（不带参数列出全部 ID） |
| `aisec gen <case_id>` | 生成某用例的 payload |
| `aisec compose <payload>` | 三层组合 |
| `aisec transform <text> -m <method>` | 文本变换 |
| `aisec rewrite <text>` | AI 改写（需要 API） |
| `aisec pipeline <case_id>` | 一键流水线：生成 → 变换 → 校验 |

## 为什么这么设计

| 设计选择 | 原因 |
|---|---|
| YAML 驱动用例 | 非 Python 贡献者也能加用例 |
| 防御性加载 | 单个坏文件不拖垮用例库 |
| 分层模块 | 纯逻辑与 CLI 分离，易测试 |
| CLI 优先 | 可脚本化、可进 CI、可测试 |
| 可插拔目标 | 加新 LLM 后端不用动核心 |
| 可插拔评估器 | 加新检测逻辑不用动 runner |
| 回执标记机制 | 攻击成功可自动判定 |
| 全局顺序 ID | 多语言也不冲突 |

