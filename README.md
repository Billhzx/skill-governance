# Skill Governance

一个面向多 Agent 本地环境的开源 Skill：发现 Skill 资产、识别真实所有权、生成机器可读台账，并在清理或迁移前建立恢复边界。

它不是新的 Skill 下载器，也不取代 [CC Switch](https://github.com/farion1231/cc-switch)、[Skillshare](https://github.com/runkids/skillshare) 或 [Skills Manager](https://github.com/xingkongliang/skills-manager)。它解决的是这些工具同时存在以后出现的问题：哪一份是真源、哪些只是链接、谁负责更新、哪个 Agent 实际启用，以及删除后能否恢复。

## 当前能力

- 跨平台扫描一个或多个个人 Skill 真源。
- 识别实体目录、符号链接、Windows Junction/重解析点和失效链接。
- 从 `SKILL.md` 读取真实名称，并对目录内容计算 SHA-256。
- 可选读取 Codex TOML、通用 Skill lock JSON 和 CC Switch SQLite 数据库。
- 区分更新管理器、分发器与 Agent 启用状态。
- 发现同名分叉、重复实体、失效登记和客户端独立 Skill。
- 给出三档恢复策略，并执行确定性审计。
- 盘点和审计命令严格只读；不自动删除、迁移或覆盖用户文件。

## 安装 Skill

仓库中的可安装 Skill 位于 `skills/skill-governance`，标准入口 `SKILL.md` 使用中文。兼容 `npx skills` 的 Agent 可执行：

```bash
npx skills add Billhzx/skill-governance --skill skill-governance
```

仓库发布前，也可以直接把该目录链接或复制到 Agent 的 Skill 目录。

## 直接运行扫描器

需要 Python 3.11+；Python 3.10 可额外安装 `tomli`。

```powershell
Copy-Item skills/skill-governance/references/config.example.json governance.json
python skills/skill-governance/scripts/skill_governance.py inventory --config governance.json --output inventory.json
python skills/skill-governance/scripts/skill_governance.py audit --inventory inventory.json
```

先修改 `governance.json` 里的路径和家族更新规则。输出可能包含本机绝对路径，公开 Issue 或日志前请脱敏。

## 安全模型

扫描器只生成证据，不生成删除命令。实际变更必须遵循：

1. 展示精确目标、所有权与恢复等级；
2. 用户明确确认；
3. 先解除派生链接和登记；
4. 最后处理实体真源；
5. 重新生成台账并通过审计。

详细规则见 [`governance.md`](skills/skill-governance/references/governance.md)。

## 开发验证

```powershell
python -m unittest discover -s tests -v
python C:/path/to/skill-creator/scripts/quick_validate.py skills/skill-governance
```

## 许可证

[MIT](LICENSE)
