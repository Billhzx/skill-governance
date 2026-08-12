# 自动发现范围

默认 `scan` 命令不需要配置文件。它会在用户主目录下探测以下常见客户端：

`.agents`、Codex、Claude Code、CC Switch、Cursor、Qoder（兼容 `.qorder`）、Gemini、OpenCode、Cline、Roo Code、Windsurf、Continue、Qwen Code、Kiro、GitHub Copilot、WorkBuddy、Hermes、CodeBuddy、OpenClaw、AiderDesk、Augment、Goose、Zencoder 和 Trae。

不存在的目录会自动跳过。新增客户端时，应扩充脚本中的 `AGENT_SKILL_PATHS` 注册表并增加测试。

## 高级内部配置

以下配置接口保留给开发者、测试夹具及特殊目录布局，不属于普通用户的首次使用路径。

所有路径均支持 `~`、环境变量和 `{home}`。相对路径以配置文件所在目录为基准解析。

## 主要字段

- `canonical_roots`：预期存放用户实体 Skill 的根目录。比较客户端条目时，第一个根目录优先作为唯一真源。
- `client_roots`：按名称登记的 Agent 或分发器目录。扫描器会判断其中的条目是链接还是实体目录。
- `platform_managed_scopes`：只作为背景报告、不计入个人资产的路径。
- `codex_configs`：可选的 TOML 文件，其中包含带有 `path` 和 `enabled` 的 `skills.config` 条目。
- `lock_files`：可选的 JSON 文件，其中 `skills` 对象保存来源元数据。
- `cc_switch_databases`：可选的 SQLite 数据库。内置适配器会在字段兼容时读取 `skills` 表。
- `family_rules`：按顺序执行的前缀或精确名称规则，用于指定 Skill 家族及更新管理器。
- `overrides_file`：可选的人工治理结论 JSON，以 Skill 目录名作为键。

可选文件缺失只产生警告，不导致扫描失败。已经存在但并非目录、或者无法读取的真源配置属于错误。

## 退出码

- `inventory`：成功生成台账时返回 `0`；配置无效或必需根目录不可读时返回 `2`。
- `audit`：没有完整性错误时返回 `0`，存在错误时返回 `1`，输入无法解析时返回 `2`。

审计警告包括同名分叉、上游元数据缺失和没有人工治理结论的资产。审计错误包括失效链接、Codex 已登记但不存在的路径，以及分发器数据库中没有对应实体真源的记录。
