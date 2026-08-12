# Skill Governance

[简体中文](README.md) | English

An open-source Agent Skill for discovering local Skill assets, identifying their real ownership, generating a machine-readable inventory, and establishing recovery boundaries before cleanup or migration.

It does not replace [CC Switch](https://github.com/farion1231/cc-switch), [Skillshare](https://github.com/runkids/skillshare), or [Skills Manager](https://github.com/xingkongliang/skills-manager). It governs the environment that exists when several installers, distributors, and agents operate at the same time.

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

```bash
npx skills add Billhzx/skill-governance --skill skill-governance
```

The installable Skill is under `skills/skill-governance`. Its operational instructions and reference documentation are written in Simplified Chinese.

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

