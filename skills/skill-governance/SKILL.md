---
name: skill-governance
description: 发现、盘点并安全治理 Codex、Claude Code、CC Switch、WorkBuddy、Hermes 及其他本地 AI 工具中的 Agent Skills。当 Skill 疑似重复、被复制或链接、已经失效、启用状态不一致、由多个安装器共同管理、难以更新或删除，或者需要建立唯一真源、生成机器可读资产台账和安全清理方案时使用。必须先审计，并在任何变更前取得用户对精确目标清单的明确授权。
---

# Skill 治理

把 Skill 管理视为资产治理：采取任何变更前，先确定存在哪些资产、谁拥有它们、如何分发以及如何恢复。

## 工作流程

1. 直接运行零配置扫描。不得要求普通用户先编辑配置文件：

   ```powershell
   python scripts/skill_governance.py scan
   ```

2. 读取 `skill-governance-output/report.md`，并把摘要、优先处理项及输出路径告诉用户。需要精确证据时再读取 `inventory.json`。
3. 按照 `references/governance.md` 对每项发现进行分类。区分实体真源、链接、生成缓存、平台托管资产和客户端自有目录。
4. 展示拟处理的精确目标、所有权、恢复等级以及预期变更后状态。用户明确批准该清单前不得执行变更。
5. 获得批准后，先解除客户端派生项，再修改或删除实体真源。全程使用同一种 Shell，并验证解析后的目标路径。
6. 重新运行 `scan`，报告仍然存在的警告和残留。

## 安全规则

- 发现和审计阶段必须保持只读。
- 读取 `SKILL.md` 的 frontmatter；不得只用目录名判断 Skill 身份。
- 计算内容哈希，区分完全重复与同名内容分叉。
- 在证明并非引用以前，把符号链接、Windows Junction 和其他重解析点视为引用。
- 不得为了让目录看起来统一，就收编或覆盖安装器拥有的资产。
- 不得把平台缓存当作个人 Skill 真源删除。
- “清理重复项”等模糊要求不构成删除授权。
- 对可重新安装的资产，删除前仍须验证声明的管理器和上游可用。
- 对存在本地修改、没有上游或内容唯一的资产，删除前必须导出或保护。

## 配套资源

- 涉及所有权、恢复等级和变更规则时，读取 `references/governance.md`。
- 适配新的工具或目录结构时，读取 `references/configuration.md`。
- 使用 `scripts/skill_governance.py` 生成确定性的盘点和审计结果。
