# Scanner configuration

All paths accept `~`, environment variables, and `{home}`. Relative paths resolve from the configuration file directory.

## Main fields

- `canonical_roots`: physical roots that are intended to hold user-owned Skills. The first root is treated as the preferred authority when comparing client entries.
- `client_roots`: named Agent or distributor directories. Entries are inspected as links or physical directories.
- `platform_managed_scopes`: paths reported for context but excluded from personal assets.
- `codex_configs`: optional TOML files containing `skills.config` entries with `path` and `enabled`.
- `lock_files`: optional JSON files whose `skills` object contains source metadata.
- `cc_switch_databases`: optional SQLite databases. The built-in adapter reads a `skills` table when compatible columns exist.
- `family_rules`: ordered prefix or exact-name rules assigning a family and update manager.
- `overrides_file`: optional JSON decisions keyed by Skill directory name.

Missing optional files are reported as warnings, not fatal errors. An existing configured root that cannot be read is an error.

## Exit codes

- `inventory`: `0` when output was generated; `2` for invalid configuration or unreadable required roots.
- `audit`: `0` with no errors, `1` with integrity errors, `2` for invalid input.

Audit warnings include divergent same-name instances, missing upstream metadata, and assets without a human decision. Errors include broken configured links, missing registered Codex paths, and distributor rows with no physical source.

