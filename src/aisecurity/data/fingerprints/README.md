# 组件指纹目录（可插拔模板）

把新的组件指纹以 YAML 文件放进本目录即可，**无需改动任何代码**。
`data/vuln/` 里的 CVE 规则通过 `component` 字段引用这里的 `id`。

## 指纹格式

```yaml
id: ollama                       # 唯一 id
name: Ollama                     # 展示名
category: llm-serving            # 可选分类
description: "组件说明"
match:
  any:                           # 命中任意一条即识别成功
    - path: /                    # 相对 target 的路径（默认 GET）
      status: 200
      body_contains: "Ollama is running"
    - path: /api/tags
      body_regex: '"models"\s*:'
version:                         # 可选：提取版本号，供 CVE 的 affected 区间使用
  header_regex:
    Server: "ollama/([0-9.]+)"
```

`match` 支持的条件：`status`（int 或列表）、`body_contains`、`body_regex`、
`header_contains`、`header_regex`；可选 `method`、`path`、`headers`。

## 贡献流程

1. 复制 [_template.yaml](_template.yaml)，改名为 `<组件id>.yaml`；
2. 填写字段；
3. 运行 `aisec vuln validate` 确认无误；
4. 提交 PR。

## 外部规则目录

```
export AISecurityTest_RULES_PATH=/path/to/my-rules
```
