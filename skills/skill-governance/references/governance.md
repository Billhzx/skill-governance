# Governance model

## Asset classes

| Class | Meaning | Default action |
|---|---|---|
| Canonical source | User-owned physical Skill directory | Preserve unless explicitly selected |
| Derived link | Symlink, Junction, or reparse point targeting a canonical source | Manage as distribution state |
| Divergent instance | Same name in another physical directory with different content | Investigate owner and local changes |
| Exact physical duplicate | Same name and content hash in multiple physical directories | Consolidation candidate after ownership check |
| Client-owned asset | Skill visible only inside one tool | Let that tool or installer own updates |
| Platform-managed scope | Built-in Skill or plugin cache | Exclude from personal inventory |
| Supporting asset | Knowledge, reports, or runtime data without `SKILL.md` | Do not classify as a duplicate Skill |

## Ownership layers

Keep these decisions independent:

1. **Physical authority:** where editable personal Skill content lives.
2. **Distribution owner:** what creates links or copies for each client.
3. **Update manager:** Git, a suite updater, an installer, or manual maintenance.
4. **Enablement owner:** the individual Agent configuration deciding whether a visible Skill is active.

One product does not need to own all four layers.

## Recovery classes

- `reinstallable_by_declared_manager`: verify the manager and remote source still work before removal.
- `verify_upstream_and_local_changes_before_direct_delete`: compare the local hash or Git diff with upstream.
- `protect_or_export_before_delete`: preserve the directory, an archive, or a content hash before removal.

## Mutation sequence

1. Show exact paths and recovery classes.
2. Resolve links and reparse points without following them recursively.
3. Remove derived links first.
4. Update Agent enablement configuration.
5. Update distributor metadata or database records.
6. Change physical sources last.
7. Regenerate inventory and audit the final state.

Never turn audit findings directly into deletion commands. The inventory is evidence, not authorization.

