# AISecurityTest

> 面向 OWASP LLM Top10 (2025) 的**轻量级本地 AI 红队载荷工具箱**。

AISecurityTest 帮助安全研究人员和开发者生成、变换、验证针对 LLM 应用、RAG 系统、
AI Agent 的对抗性载荷——**不依赖 Docker、不需要服务器、不需要数据库**。

[English](README.md) · [架构说明](docs/architecture_ZH.md) · [测试指南](docs/testing_ZH.md) · [贡献指南](CONTRIBUTING_ZH.md)

---

## 能做什么

- **57 条精选用例**，覆盖 OWASP LLM01–LLM10 (2025)
- **YAML 驱动用例库**——不写 Python 也能加用例
- **17 个 CLI 命令**——浏览、生成、变换、改写、执行、导出、侦察、探针、自动扫描
- **Probes 插件框架**——Python + YAML 双轨制，支持越狱 / DAN / 编码 / 角色扮演 / 前缀注入 / 多轮
- **动态 YAML 数据集加载**——通过 `{变量}` 占位符驱动 10 万级数据集（Safety-Prompts、AdvBench、HarmBench）
- **端点侦察**——`aisec recon` 探测目标的模型名、system prompt 泄露与注入面
- **自动扫描**——`aisec autoscan --probes` 一键对目标运行探针套件
- **Excel/CSV → YAML 转换**——把表格转成用例文件
- **文本变换工具箱**——零宽字符、Base64、Hex、形近字、ChatML/Llama 标记
- **三层组合生成器**——载体 × 手法 × 载荷
- **回执标记校验**——`<<AIST_OK>>` 验证载荷在改写后是否保留
- **可插拔目标适配器**——当前支持 OpenAI 兼容 API
- **内置评估器**——标记 / 正则 / Unicode 标签 / 多语言 / LLM 裁判（5 条检测线）
- **报告导出**——Markdown / JSON / Word / Excel / HTML
- **防御性加载**——单个坏 YAML 文件不会拖垮整个用例库
- **贡献者友好 CLI**——`aisec categories` / `aisec next-id` / `aisec check-name`

## 与 AI-Infra-Guard 的区别

AISecurityTest **不是**平台，是**载荷工具箱**：

| | AISecurityTest | AI-Infra-Guard |
|---|---|---|
| 定位 | 载荷生成与变换 | 全栈扫描平台 |
| 部署 | `pip install` / 本地 | Docker + Web UI |
| CVE 扫描 | ✗ | ✓（2000+ 规则） |
| 用例库 | YAML，社区可编辑 | 规则驱动 |
| 适合 | 手工红队、提示词工程 | 企业级扫描 |

两者互补，不冲突。

---

## 快速开始

### 安装

```bash
pip install aisecurity-test