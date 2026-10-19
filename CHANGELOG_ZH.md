# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

### 计划中

- 多模态样本生成（PNG / WAV / PDF / CSV）
- MCP 恶意 manifest 模板 + 审查清单
- Ollama / HTTP Webhook 目标适配器
- Tkinter GUI（轻量，跟随系统语言）
- Web UI（FastAPI + Vue）
- 多语言用例库（i18n）

---

## [1.1.0] - 2025-10-20

### 新增

- **漏洞扫描器**（`vulnscan/` 模块 + `aisec vuln` 命令）
  - 两阶段流程：指纹识别 → 版本判定 → CVE 匹配
  - 默认被动；`--active` 启用确认请求
  - YAML 驱动规则：`data/fingerprints/` + `data/vuln/`
  - 通过 `AISecurityTest_RULES_PATH` 加载外部规则
  - 内置指纹：Ollama、vLLM、ComfyUI
  - 内置 CVE：CVE-2024-37032（Ollama <0.1.34 路径穿越 RCE）
  - 退出码：0 = 无漏洞，2 = 发现 CRITICAL（可接入 CI/CD）

- **探针框架**（`probes/` 模块）
  - 可插拔的 LLM 端点安全探针

- **越狱数据集**（`jailbreak_dataset/`）
  - 14 个危害类别、400+ 条采样提示词

### 变更

- CLI 命令数：13 → 18
- 测试用例数：40 → 57
- `pyproject.toml`：package-data 包含 `fingerprints/` 和 `vuln/`
- `reportlab>=3.6.13` 移除上限以兼容 Python 3.12

### 修复

- 打包产物缺少子目录 YAML 文件

---

## [1.0.0] - 2025-10-11

首个正式版本。

### 新增

- **用例库**：40 条精选用例，覆盖 OWASP LLM01–LLM10 (2025)
  - LLM01 提示注入（直接 / 间接 / 多模态 / Agent 链路 / 编码混淆 / 渐进越狱）
  - LLM02 敏感信息泄露
  - LLM03 供应链风险
  - LLM04 数据与模型投毒
  - LLM05 不当输出处理
  - LLM06 过度代理
  - LLM07 系统提示泄露
  - LLM08 向量与嵌入弱点
  - LLM09 错误信息
  - LLM10 无界消耗

- **YAML 驱动用例库**
  - 15 个类别文件，一类一文件
  - 社区可零成本贡献新用例
  - 防御性加载：单个坏文件不影响整体

- **载荷引擎**（`engine/`）
  - 按用例生成载荷
  - 三层组合：载体 × 手法 × 载荷
  - 文本变换工具箱：零宽字符、Base64、Hex、Unicode 转义、大小写混淆、
    形近字替换、HTML 注释、代码块、ChatML/Llama 标记注入
  - 低资源语言翻译：斯瓦希里语、冰岛语、豪萨语、毛利语、威尔士语
  - AI 改写：OpenAI 兼容 API / Ollama

- **回执标记机制**
  - `<<AIST_OK>>` 用于验证载荷是否在改写/变换后被保留

- **目标适配器**（`targets/`）
  - `Target` 抽象基类
  - `OpenAITarget`：OpenAI 兼容 API

- **评估器**（`evaluators/`）
  - `MarkerEvaluator`：回执标记检测
  - `RegexEvaluator`：手机号、身份证、邮箱、API Key、银行卡号等敏感信息检测

- **编排层**（`runner/`）
  - 用例 × 目标 × 评估器 端到端编排

- **CLI**（`cli/`）—— **13 个命令**
  - `aisec list` —— 列出类别/用例
  - `aisec validate` —— 校验全部用例
  - `aisec run` —— 对目标执行用例
  - `aisec export` —— 导出用例（markdown / json / html / docx / xlsx）
  - `aisec next-id` —— 显示下一个可用用例 ID
  - `aisec categories` —— 列出所有分类名（一行一个）
  - `aisec check-name <name>` —— 检查分类名是否已被占用
  - `aisec show [case_id]` —— 显示用例详情（不带参数列出全部 ID）
  - `aisec gen <case_id>` —— 生成某用例的 payload
  - `aisec compose <payload>` —— 三层组合
  - `aisec transform <text> -m <method>` —— 文本变换
  - `aisec rewrite <text>` —— AI 改写（需要 API）
  - `aisec pipeline <case_id>` —— 一键流水线：生成 → 变换 → 校验

- **测试**
  - 32 个测试全绿
  - 单元测试 + 集成测试

- **CI**
  - GitHub Actions 自动校验（Python 3.8 / 3.10 / 3.12）

### 文档

- `README.md` / `README_ZH.md` —— 中英双语
- `CONTRIBUTING.md` / `CONTRIBUTING_ZH.md` —— 中英双语
- `SECURITY.md` / `SECURITY_ZH.md` —— 中英双语
- `CHANGELOG.md` / `CHANGELOG_ZH.md` —— 中英双语
- `docs/architecture.md` / `docs/architecture_ZH.md` —— 中英双语
- `docs/testing.md` / `docs/testing_ZH.md` —— 中英双语

### 已知限制

- 暂不支持多模态样本生成（CLI）
- 暂不支持 MCP 恶意 manifest 模板（CLI）
- 暂不支持 Ollama / HTTP Webhook 目标（run）
- 暂无 GUI

---

## 贡献

贡献方式见 [CONTRIBUTING_ZH.md](CONTRIBUTING_ZH.md)。

## 链接

- [仓库](https://github.com/milantgh/AISecurityTest)
- [Issues](https://github.com/milantgh/AISecurityTest/issues)
- [Releases](https://github.com/milantgh/AISecurityTest/releases)