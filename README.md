# Skill Governance

[![Tests](https://github.com/Billhzx/skill-governance/actions/workflows/test.yml/badge.svg)](https://github.com/Billhzx/skill-governance/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

简体中文 | [English](README.en.md)

> 当 Codex、Claude Code、CC Switch 和其他 Agent 都在管理 Skill 时，先回答三个问题：谁是真源？谁有权分发？谁决定启用？

一个面向多 Agent 本地环境的开源 Skill：发现 Skill 资产、识别真实所有权、生成机器可读台账，并在清理或迁移前建立恢复边界。

## 我为什么做这个项目

这个项目来自一次真实的本机 Skill 大扫除。

最初的问题看起来只是“电脑里为什么有这么多份 Skill”：同一个名字同时出现在 `.agents`、Codex、Claude Code、CC Switch、WorkBuddy 和 Hermes 的目录里；有的是实体目录，有的是 Junction 或软链接，有的是插件缓存，还有一些明明没有手动下载，却仍然能被某个 Agent 看到。

继续追查后，真正的问题逐渐暴露出来：

- 不知道哪一份才应该修改，担心改错副本。
- 不知道 Skill 由 CC Switch、GitHub、套件更新器还是 Agent 自己负责更新。
- “存在于目录中”“对 Agent 可见”“在 Agent 中启用”经常被混为一谈。
- 同名目录可能内容完全一致，也可能早已分叉，不能仅凭名称删除。
- 平台内置 Skill、插件缓存、知识库和运行数据容易被误认为重复安装。
- 真正准备清理时，不知道哪些可以重新下载，哪些包含无法恢复的本地修改。

第一次把这些路径完整盘点后，我的机器上识别出了 **105 个实体 Skill**：Codex 实际只启用了 **3 个**，CC Switch 管理 **49 个**。数字本身不是问题，问题是没有一份台账能解释每项资产的真源、所有者、可见性、更新方式和恢复办法。

所以我把整次清理过程沉淀成了这个 Skill。它不替你武断地删文件，而是先把混乱变成可以验证的事实。

## 你是否也需要它

| 你看到的现象 | 需要查清的真实问题 |
|---|---|
| 同名 Skill 出现在多个 Agent 目录 | 是实体副本、链接，还是内容已经分叉？ |
| 没下载过却仍然能调用 | 是安装器派生、平台内置，还是其他目录的链接？ |
| CC Switch 中 Skill 很多 | 它是唯一真源、分发器，还是只保存了登记信息？ |
| 删除后又重新出现 | 到底哪个更新器或安装器拥有它？ |
| 想只保留一套，又不敢删 | 哪份是可恢复副本，哪份是不可替代的本地资产？ |
| 换 Agent 或换电脑后重新混乱 | 是否有机器可读台账和固定治理规则？ |

如果你同时使用两个以上的 Agent、Skill 安装器或分发工具，这个项目就是为这种环境准备的。

它不是新的 Skill 下载器，也不取代 [CC Switch](https://github.com/farion1231/cc-switch)、[Skillshare](https://github.com/runkids/skillshare) 或 [Skills Manager](https://github.com/xingkongliang/skills-manager)。它解决的是这些工具同时存在以后出现的问题：哪一份是真源、哪些只是链接、谁负责更新、哪个 Agent 实际启用，以及删除后能否恢复。

```text
发现所有 Skill 路径
        ↓
区分实体、链接、缓存与平台资产
        ↓
识别真源、更新所有者和 Agent 可见性
        ↓
生成机器可读台账
        ↓
预览变更 → 用户确认 → 精确执行 → 重新审计
```

## 当前能力

- 零配置自动发现常见 Agent，安装后直接让 Agent 执行扫描。
- 跨平台扫描一个或多个个人 Skill 真源。
- 识别实体目录、符号链接、Windows Junction/重解析点和失效链接。
- 从 `SKILL.md` 读取真实名称，并对目录内容计算 SHA-256。
- 可选读取 Codex TOML、通用 Skill lock JSON 和 CC Switch SQLite 数据库。
- 区分更新管理器、分发器与 Agent 启用状态。
- 发现同名分叉、重复实体、失效登记和客户端独立 Skill。
- 给出三档恢复策略，并执行确定性审计。
- 盘点和审计命令严格只读；不自动删除、迁移或覆盖用户文件。

## 安装 Skill

仓库中的可安装 Skill 位于 `skills/skill-governance`，标准入口 `SKILL.md` 使用中文。

### 推荐：只安装到 Codex

```bash
npx skills add Billhzx/skill-governance -g --skill skill-governance --agent codex
```

`-g` 很重要：它把 Skill 安装到用户级真源 `~/.agents/skills/skill-governance`。如果省略，安装器默认使用项目级目录，离开当前项目后 Agent 可能无法识别。

### 安装到多个 Agent

```bash
npx skills add Billhzx/skill-governance -g --skill skill-governance
```

在交互界面中选择需要使用它的 Agent；存在多个目标目录时，选择推荐的 **Symlink** 模式。不要使用 `--copy`，否则会为各 Agent 创建彼此独立的副本。也不建议使用 `--all`，除非确实希望把它分发给机器上检测到的全部 Agent。

### 会不会重复安装

不会因为本仓库结构而出现两个同名 Skill。发布前使用官方 CLI 验证：仓库只会发现一个 `skill-governance`。在隔离环境中连续执行两次相同的全局安装命令，最终仍然只有一个实体目录和一条全局安装记录。

如果机器上已经存在其他工具手工创建的同名目录，安装器会进入覆盖确认流程。此时不要使用 `-y` 跳过确认；应先核实原目录的来源和本地修改。

安装后可验证：

```bash
npx skills list -g --json
```

结果中应只有一个名为 `skill-governance` 的全局条目，路径为 `~/.agents/skills/skill-governance`，来源为 `Billhzx/skill-governance`。

## 第一次使用

安装完成后，直接对 Agent 说：

> 帮我盘点本机所有 Skill。

Agent 会执行零配置扫描：

需要 Python 3.11+；Python 3.10 可额外安装 `tomli`。

```powershell
python skills/skill-governance/scripts/skill_governance.py scan
```

不需要先编辑 JSON。默认输出：

```text
skill-governance-output/
├── report.md       # 中文可读报告
└── inventory.json  # 机器可读完整台账
```

扫描器会自动探测 `.agents`、Codex、Claude Code、CC Switch、Cursor、Qoder、Gemini、OpenCode、Cline、Roo Code、Windsurf、Continue、Qwen Code、Kiro、WorkBuddy、Hermes、CodeBuddy、OpenClaw 等常见客户端。输出可能包含本机绝对路径，公开 Issue 或日志前请脱敏。

一份脱敏的实际输出见 [`examples/report.md`](examples/report.md)。

## 更新与卸载

```bash
npx skills update skill-governance -g
npx skills remove skill-governance -g
```

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
