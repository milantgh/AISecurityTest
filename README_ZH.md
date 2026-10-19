# AISecurityTest

> 面向 OWASP LLM Top10 (2025) 的**轻量级本地 AI 红队载荷工具箱**，
> 内置可插拔的基础设施漏洞扫描器。

AISecurityTest 帮助安全研究人员和开发者生成、变换、验证针对 LLM 应用、RAG 系统、
AI Agent 的对抗性载荷——**不依赖 Docker、不需要服务器、不需要数据库**。

[English](README.md) · [架构说明](docs/architecture_ZH.md) · [测试指南](docs/testing_ZH.md) · [贡献指南](CONTRIBUTING_ZH.md)

---

## 能做什么

- **57 条精选用例**，覆盖 OWASP LLM01–LLM10 (2025)
- **YAML 驱动用例库**——不写 Python 也能加用例
- **18 个 CLI 命令**——浏览、生成、变换、改写、执行、导出、扫描
- **文本变换工具箱**——零宽字符、Base64、Hex、形近字、ChatML/Llama 标记
- **三层组合生成器**——载体 × 手法 × 载荷
- **回执标记校验**——`<<AIST_OK>>` 验证载荷在改写后是否保留
- **可插拔目标适配器**——当前支持 OpenAI 兼容 API
- **内置评估器**——回执标记检测 + 基于正则的敏感信息检测
- **漏洞扫描器**（`vuln`）——指纹识别 + 版本判定 + CVE 匹配，默认被动
- **报告导出**——Markdown / JSON / Word / Excel / HTML
- **防御性加载**——单个坏 YAML 文件不会拖垮整个用例库
- **贡献者友好 CLI**——`aisec categories` / `aisec next-id` / `aisec check-name`

---

## 快速开始

### 安装

```bash
pip install aisecurity-test
```

### 浏览用例

```bash
aisec list                  # 列出所有分类和用例
aisec categories            # 只列出分类名
aisec show PI-001           # 查看单条用例详情
aisec validate              # 校验全部用例
```

### 生成与执行

```bash
aisec gen PI-001            # 为某用例生成载荷
aisec transform "你好" -m base64
aisec rewrite "你的文本"     # AI 改写（需要 API Key）
aisec run PI-001 --target openai --api-key sk-xxx
```

### 漏洞扫描

```bash
aisec vuln list                               # 列出指纹和 CVE 规则
aisec vuln scan --target http://localhost:11434
aisec vuln scan --target http://localhost:11434 --active
aisec vuln scan --target http://localhost:11434 --format json -o result.json
```

### 导出

```bash
aisec export --format markdown -o cases.md
aisec export --format html -o cases.html
aisec export --format docx -o cases.docx
aisec export --format xlsx -o cases.xlsx
```

---

## 漏洞扫描器（`vuln`）

`vuln` 命令采用**指纹识别 → 版本判定 → CVE 匹配**的流程，
扫描 AI 基础设施组件的已知 CVE。

- **默认被动**——仅做版本比对，不发送攻击载荷
- **主动模式**（`--active`）——对 `mode: request` 规则发送确认请求
- **YAML 驱动规则**——不写 Python 即可添加指纹和 CVE
- **外部规则**——设置 `AISecurityTest_RULES_PATH` 加载社区规则

内置指纹：Ollama、vLLM、ComfyUI。
内置 CVE：CVE-2024-37032（Ollama <0.1.34 路径穿越 RCE）。

退出码：`0` = 无漏洞，`2` = 发现 CRITICAL——可接入 CI/CD。

---

## 项目结构

```
src/aisecurity/
├── cli/                  # 18 个 CLI 命令
├── engine/               # 载荷生成与变换
├── targets/              # 目标适配器（OpenAI 兼容）
├── evaluators/           # 回执标记 + 正则评估器
├── runner/               # 端到端编排
├── vulnscan/             # 指纹 + CVE 扫描引擎
├── recon/                # 端点侦察
├── probes/               # 探针框架
└── data/
    ├── cases/            # 57 条 YAML 用例
    ├── fingerprints/     # 组件指纹
    ├── vuln/             # CVE 规则
    ├── datasets/         # 测试数据集
    └── probes/           # 探针定义
```

---

## 本地开发

```bash
git clone https://github.com/milantgh/AISecurityTest.git
cd AISecurityTest
pip install -e ".[dev]"
aisec list
aisec validate
python -m pytest tests/ -v
```

## 文档

- `README.md` / `README_ZH.md`
- `CONTRIBUTING.md` / `CONTRIBUTING_ZH.md`
- `SECURITY.md` / `SECURITY_ZH.md`
- `CHANGELOG.md` / `CHANGELOG_ZH.md`

## 许可证

MIT License