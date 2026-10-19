# CVE 规则目录（可插拔模板）

把新的 CVE 规则以 YAML 文件放进本目录即可，**无需改动任何代码**。

## 规则格式

每个文件一条规则，最小字段：

```yaml
id: CVE-2024-37032                 # 唯一 id
title: "漏洞标题"
component: ollama                  # 必须是 data/fingerprints/ 里某个指纹的 id
severity: CRITICAL                 # CRITICAL / HIGH / MEDIUM / LOW / INFO
affected: "<0.1.34"                # 受影响版本区间，"*" 表示全部
description: "漏洞说明"
references: [https://nvd.nist.gov/vuln/detail/CVE-2024-37032]
remediation: "升级到 0.1.34+"
check:
  mode: version                    # version(默认) | request
```

### 两种检测模式

| mode | 行为 | 风险 |
|---|---|---|
| `version`（默认） | 指纹识别出的版本落入 `affected` 区间即告警 | 被动、零风险 |
| `request` | 额外发一个确认请求，仅 `--active` 时执行 | 会向目标发请求，需授权 |

`request` 模式的 `match` 支持 `status` / `body_contains` / `body_regex` / `header_contains` / `header_regex`。

## 版本区间语法

`*`（全部）、`>=1.2,<1.5`、`<=2.0`、`==1.2.3`、`>1.0`，逗号表示 AND。缺省位补 0（`1.2` == `1.2.0`）。

## 贡献流程

1. 复制 [_template.yaml](_template.yaml)，改名为 `<CVE-ID>.yaml`；
2. 填写字段（`component` 必须是已存在的指纹 id）；
3. 运行 `aisec vuln validate` 确认无误；
4. 提交 PR。

## 外部规则目录

不想改仓库？把规则放在任意目录，设置环境变量即可：

```
export AISecurityTest_RULES_PATH=/path/to/my-rules   # 目录内含 fingerprints/ 与 vuln/ 子目录
aisec vuln list
```

## 使用

```bash
aisec vuln list                       # 列出全部指纹与 CVE 规则
aisec vuln show CVE-2024-37032       # 查看某条规则
aisec vuln scan --target http://localhost:11434
aisec vuln scan --target http://localhost:11434 --active   # 允许 request 模式确认
```
