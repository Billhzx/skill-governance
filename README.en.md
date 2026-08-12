# Skill Governance

[简体中文](README.md) | English

> When Codex, Claude Code, CC Switch, and other agents all manage Skills, answer three questions first: What is the source of truth? Who may distribute it? Who decides whether it is enabled?

An open-source Agent Skill for discovering local Skill assets, identifying their real ownership, generating a machine-readable inventory, and establishing recovery boundaries before cleanup or migration.

## Why I built this

This project grew out of a real cleanup of my local Agent Skills.

At first, the problem looked simple: why did the same Skills appear under `.agents`, Codex, Claude Code, CC Switch, WorkBuddy, and Hermes? Some entries were physical directories, some were Junctions or symlinks, some were plugin caches, and some remained visible even though I had never installed them manually.

The deeper problem was ownership:

- I could not tell which copy should be edited.
- Updates might belong to CC Switch, GitHub, a suite updater, or the Agent itself.
- “Present on disk,” “visible to an Agent,” and “enabled by an Agent” were treated as the same state.
- Same-name directories could be identical or silently divergent.
- Built-in Skills, plugin caches, knowledge bases, and runtime data could be mistaken for duplicate installations.
- Before deleting anything, there was no reliable way to tell what was reinstallable and what contained unique local changes.

The first complete inventory found **105 physical Skills** on my machine. Codex had only **3 enabled**, while CC Switch managed **49**. The counts were not the real problem. The missing piece was a ledger explaining the source, owner, visibility, update method, and recovery policy for every asset.

Skill Governance turns that cleanup process into a reusable workflow. It does not guess what to delete; it turns a confusing filesystem into verifiable evidence first.

## Do you need it?

| What you observe | What must actually be determined |
|---|---|
| The same Skill appears under several Agents | Is it a copy, a link, or divergent content? |
| A Skill is available although you never installed it | Is it installer-derived, built in, or linked from elsewhere? |
| CC Switch lists many Skills | Is it the source, a distributor, or only a metadata registry? |
| A deleted Skill comes back | Which installer or updater owns it? |
| You want one copy but are afraid to delete anything | What is recoverable, and what is unique local data? |
| A new Agent or machine recreates the mess | Do you have a machine-readable inventory and stable ownership rules? |

If you use more than one Agent, Skill installer, or distribution tool, this project is designed for that environment.

It does not replace [CC Switch](https://github.com/farion1231/cc-switch), [Skillshare](https://github.com/runkids/skillshare), or [Skills Manager](https://github.com/xingkongliang/skills-manager). It governs the environment that exists when several installers, distributors, and agents operate at the same time.

```text
Discover every Skill path
        ↓
Classify physical sources, links, caches, and platform assets
        ↓
Resolve ownership, update manager, and Agent visibility
        ↓
Generate a machine-readable inventory
        ↓
Preview → explicit approval → precise changes → audit again
```

## Capabilities

- Scan one or more canonical personal Skill roots on Windows, macOS, or Linux.
- Distinguish physical directories, symbolic links, Windows Junctions/reparse points, and broken links.
- Read declared names from `SKILL.md` and calculate deterministic SHA-256 content hashes.
- Optionally inspect Codex TOML configuration, generic Skill lock JSON, and the CC Switch SQLite database.
- Separate update ownership, distribution ownership, and per-Agent enablement.
- Detect divergent same-name instances, exact physical duplicates, stale registrations, and client-owned Skills.
- Assign recovery policies and run a deterministic integrity audit.
- Keep inventory and audit operations read-only.

## Install

### Recommended: Codex only

```bash
npx skills add Billhzx/skill-governance -g --skill skill-governance --agent codex
```

The installable Skill is under `skills/skill-governance`. Its operational instructions and reference documentation are written in Simplified Chinese.

The `-g` flag is important: it installs the Skill into the user-level source at `~/.agents/skills/skill-governance`. Without it, the CLI defaults to project scope and the Skill may not be visible after leaving that project.

### Multiple Agents

```bash
npx skills add Billhzx/skill-governance -g --skill skill-governance
```

Select only the Agents that need it. When several target directories are involved, choose the recommended **Symlink** mode. Avoid `--copy`, which deliberately creates independent copies, and avoid `--all` unless every detected Agent should receive the Skill.

### Duplicate-install behavior

The repository is discovered as exactly one Skill. In an isolated end-to-end test, running the same global installation twice still produced one physical directory and one global installation record.

If another tool has already created a same-name directory, do not add `-y` to bypass the overwrite prompt. Inspect that directory's source and local changes first.

Verify the result with:

```bash
npx skills list -g --json
```

There should be one global `skill-governance` entry at `~/.agents/skills/skill-governance`, sourced from `Billhzx/skill-governance`.

## Run the scanner directly

Python 3.11+ is recommended. Python 3.10 additionally requires `tomli`.

```bash
cp skills/skill-governance/references/config.example.json governance.json
python skills/skill-governance/scripts/skill_governance.py inventory --config governance.json --output inventory.json
python skills/skill-governance/scripts/skill_governance.py audit --inventory inventory.json
```

Edit paths and manager-family rules before running. Generated inventories may contain absolute local paths and are ignored by Git by default.

## Safety model

The scanner produces evidence, not deletion commands. Every mutation requires an exact target list, an explicit user decision, derived-link cleanup before physical-source changes, and a fresh post-change inventory and audit.

## Development

```bash
python -m unittest discover -s tests -v
python /path/to/skill-creator/scripts/quick_validate.py skills/skill-governance
```

## License

[MIT](LICENSE)
