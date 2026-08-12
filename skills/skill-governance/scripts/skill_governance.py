#!/usr/bin/env python3
"""Read-only inventory and audit CLI for local Agent Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def expand_path(value: str, base: Path) -> Path:
    expanded = os.path.expandvars(value.replace("{home}", str(Path.home())))
    path = Path(expanded).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    block = match.group(1)
    for key in ("name", "description", "version"):
        item = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\r\n\"']+)", block)
        if item:
            value = item.group(1).strip()
            if value in {">", ">-", ">+", "|", "|-", "|+"}:
                tail = block[item.end():]
                continuation = []
                for line in tail.splitlines():
                    if not line.strip():
                        if continuation:
                            break
                        continue
                    if not line.startswith((" ", "\t")):
                        break
                    continuation.append(line.strip())
                value = " ".join(continuation) if value.startswith(">") else "\n".join(continuation)
            result[key] = value
    return result


def folder_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def is_link_like(path: Path) -> bool:
    if path.is_symlink() or os.path.islink(path):
        return True
    try:
        return bool(path.lstat().st_file_attributes & 0x400)  # Windows reparse point
    except (AttributeError, OSError):
        return False


def resolved_equal(left: Path, right: Path) -> bool:
    try:
        return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))
    except OSError:
        return False


def entry_state(path: Path, sources: list[Path]) -> dict[str, Any]:
    lexists = os.path.lexists(path)
    if not lexists:
        return {"present": False, "path": str(path), "kind": "absent", "points_to_source": False}
    link = is_link_like(path)
    exists = path.exists()
    target = next((source for source in sources if exists and resolved_equal(path, source)), None)
    if link and not exists:
        kind = "broken_link_or_reparse_point"
    elif link:
        kind = "link_or_reparse_point"
    elif path.is_dir():
        kind = "real_directory"
    else:
        kind = "other"
    state: dict[str, Any] = {
        "present": True,
        "path": str(path),
        "kind": kind,
        "points_to_source": target is not None,
        "resolved_target": str(target) if target else None,
    }
    if exists and path.is_dir() and not target:
        state["has_skill_md"] = (path / "SKILL.md").is_file()
        if state["has_skill_md"]:
            state["content_sha256"] = folder_hash(path)
    return state


def read_codex(paths: list[Path], warnings: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            warnings.append(f"optional Codex config not found: {path}")
            continue
        try:
            config = tomllib.loads(path.read_text(encoding="utf-8"))
            for item in config.get("skills", {}).get("config", []):
                if isinstance(item, dict) and item.get("path"):
                    skill_path = expand_path(str(item["path"]), path.parent)
                    result.append({
                        "name": skill_path.parent.name,
                        "path": str(skill_path),
                        "enabled": bool(item.get("enabled", False)),
                        "config": str(path),
                    })
        except (OSError, ValueError) as exc:
            warnings.append(f"could not parse Codex config {path}: {exc}")
    return result


def read_locks(paths: list[Path], warnings: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            warnings.append(f"optional lock file not found: {path}")
            continue
        try:
            for name, row in load_json(path, {}).get("skills", {}).items():
                if isinstance(row, dict):
                    result[name] = {**row, "_lock_file": str(path)}
        except (OSError, ValueError) as exc:
            warnings.append(f"could not parse lock file {path}: {exc}")
    return result


def read_cc_switch(paths: list[Path], warnings: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            warnings.append(f"optional CC Switch database not found: {path}")
            continue
        try:
            connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "skills" not in tables:
                warnings.append(f"CC Switch database has no skills table: {path}")
            else:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(skills)")}
                key = "directory" if "directory" in columns else "name" if "name" in columns else None
                if not key:
                    warnings.append(f"CC Switch skills table has no directory/name key: {path}")
                else:
                    for row in connection.execute("SELECT * FROM skills"):
                        data = dict(row)
                        result[str(data[key])] = {**data, "_database": str(path)}
            connection.close()
        except sqlite3.Error as exc:
            warnings.append(f"could not read CC Switch database {path}: {exc}")
    return result


def classify(name: str, rules: list[dict[str, Any]]) -> tuple[str, str | None]:
    for rule in rules:
        if rule.get("exact") == name or (rule.get("prefix") and name.startswith(rule["prefix"])):
            return str(rule.get("family", "independent")), rule.get("update_manager")
    return "independent", None


def repository_for(lock: dict[str, Any], cc_row: dict[str, Any], override: dict[str, Any]) -> str | None:
    if override.get("repository"):
        return str(override["repository"])
    owner, repo = cc_row.get("repo_owner"), cc_row.get("repo_name")
    if owner and repo:
        return f"{owner}/{repo}"
    source = lock.get("source")
    return str(source) if source else None


def recovery_policy(repository: str | None, manager: str) -> str:
    declared = {"cc_switch_github", "dbs-update", "arkcli", "lark-cli", "lark_well_known"}
    if manager in declared:
        return "reinstallable_by_declared_manager"
    if repository:
        return "verify_upstream_and_local_changes_before_direct_delete"
    return "protect_or_export_before_delete"


def build_inventory(config_path: Path) -> dict[str, Any]:
    config = load_json(config_path)
    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    base = config_path.parent
    warnings: list[str] = []
    roots = [expand_path(item, base) for item in config.get("canonical_roots", [])]
    if not roots:
        raise ValueError("canonical_roots must contain at least one path")
    unreadable = [str(path) for path in roots if path.exists() and not path.is_dir()]
    if unreadable:
        raise ValueError(f"canonical roots are not directories: {unreadable}")
    for path in roots:
        if not path.exists():
            warnings.append(f"canonical root not found: {path}")

    clients = {name: expand_path(value, base) for name, value in config.get("client_roots", {}).items()}
    codex_entries = read_codex([expand_path(p, base) for p in config.get("codex_configs", [])], warnings)
    locks = read_locks([expand_path(p, base) for p in config.get("lock_files", [])], warnings)
    cc_rows = read_cc_switch([expand_path(p, base) for p in config.get("cc_switch_databases", [])], warnings)
    override_path = config.get("overrides_file")
    overrides = load_json(expand_path(override_path, base), {}) if override_path else {}
    decisions = overrides.get("skills", {}) if isinstance(overrides, dict) else {}

    sources_by_name: dict[str, list[Path]] = {}
    for root in roots:
        if not root.exists():
            continue
        for entry in root.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                sources_by_name.setdefault(entry.name, []).append(entry)

    assets: list[dict[str, Any]] = []
    for name in sorted(sources_by_name, key=str.casefold):
        sources = sources_by_name[name]
        preferred = sources[0]
        metadata = parse_frontmatter(preferred / "SKILL.md")
        lock, cc_row = locks.get(name, {}), cc_rows.get(name, {})
        override = decisions.get(name, {}) if isinstance(decisions.get(name, {}), dict) else {}
        family, family_manager = classify(name, config.get("family_rules", []))
        repository = repository_for(lock, cc_row, override)
        manager = str(override.get("update_manager") or family_manager or
                      ("cc_switch_github" if cc_row.get("repo_owner") and cc_row.get("repo_name") else
                       "github_manual" if lock.get("sourceType") == "github" else "manual_or_upstream_specific"))
        codex_matches = [item for item in codex_entries if item["name"] == name]
        assets.append({
            "name": name,
            "declared_name": metadata.get("name"),
            "description": metadata.get("description"),
            "family": family,
            "physical_sources": [{"path": str(p), "content_sha256": folder_hash(p)} for p in sources],
            "preferred_source": str(preferred),
            "upstream": {"repository": repository, "skill_path": override.get("skill_path") or lock.get("skillPath")},
            "ownership": {
                "update_manager": manager,
                "cc_switch_managed": bool(cc_row),
                "recovery_policy": recovery_policy(repository, manager),
            },
            "codex": {
                "registered": bool(codex_matches),
                "enabled": any(item["enabled"] for item in codex_matches),
                "entries": codex_matches,
            },
            "clients": {client: entry_state(root / name, sources) for client, root in clients.items()},
            "decision": {
                "status": override.get("decision", "unreviewed"),
                "reason": override.get("reason"),
            },
        })

    known = set(sources_by_name)
    client_only: list[dict[str, Any]] = []
    for client, root in clients.items():
        if not root.exists() or not root.is_dir():
            continue
        for entry in root.iterdir():
            if entry.name not in known and entry.is_dir() and (entry / "SKILL.md").is_file():
                client_only.append({
                    "name": entry.name,
                    "declared_name": parse_frontmatter(entry / "SKILL.md").get("name"),
                    "client": client,
                    "path": str(entry),
                    "kind": "client_owned_or_unadopted",
                    "content_sha256": folder_hash(entry),
                })

    divergent: list[dict[str, Any]] = []
    broken: list[dict[str, str]] = []
    for asset in assets:
        canonical_hashes = {item["content_sha256"] for item in asset["physical_sources"]}
        for client, state in asset["clients"].items():
            if state["kind"] == "broken_link_or_reparse_point":
                broken.append({"name": asset["name"], "client": client, "path": state["path"]})
            elif state["present"] and not state["points_to_source"]:
                divergent.append({
                    "name": asset["name"], "client": client, "path": state["path"],
                    "content_sha256": state.get("content_sha256"),
                    "matches_canonical_content": state.get("content_sha256") in canonical_hashes,
                })

    missing_codex = sorted({item["path"] for item in codex_entries if not Path(item["path"]).exists()})
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "configuration": str(config_path.resolve()),
        "authority": {"canonical_roots": [str(path) for path in roots], "client_roots": {k: str(v) for k, v in clients.items()}},
        "summary": {
            "skill_count": len(assets), "physical_source_count": sum(len(a["physical_sources"]) for a in assets),
            "client_only_count": len(client_only), "codex_enabled_count": sum(a["codex"]["enabled"] for a in assets),
            "cc_switch_managed_count": sum(a["ownership"]["cc_switch_managed"] for a in assets),
        },
        "integrity": {
            "warnings_during_discovery": warnings,
            "missing_codex_paths": missing_codex,
            "stale_lock_entries": sorted(set(locks) - known),
            "cc_switch_rows_without_physical_source": sorted(set(cc_rows) - known),
            "broken_links": broken,
            "same_name_noncanonical_instances": divergent,
            "multiple_canonical_sources": sorted(name for name, paths in sources_by_name.items() if len(paths) > 1),
            "assets_without_upstream_repository": sorted(a["name"] for a in assets if not a["upstream"]["repository"]),
            "unreviewed_assets": sorted(a["name"] for a in assets if a["decision"]["status"] == "unreviewed"),
        },
        "platform_managed_scopes": [
            {**item, "path": str(expand_path(item["path"], base))}
            for item in config.get("platform_managed_scopes", [])
        ],
        "supporting_assets": overrides.get("supporting_assets", []) if isinstance(overrides, dict) else [],
        "assets": assets,
        "client_only_assets": client_only,
    }


def audit_inventory(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    integrity = data.get("integrity", {})
    errors: list[str] = []
    warnings: list[str] = list(integrity.get("warnings_during_discovery", []))
    error_fields = {
        "missing_codex_paths": "registered Codex paths do not exist",
        "stale_lock_entries": "lock entries have no canonical source",
        "cc_switch_rows_without_physical_source": "CC Switch rows have no canonical source",
        "broken_links": "broken links or reparse points",
    }
    warning_fields = {
        "same_name_noncanonical_instances": "same-name noncanonical instances require review",
        "multiple_canonical_sources": "skills exist in multiple canonical roots",
        "assets_without_upstream_repository": "skills have no declared upstream repository",
        "unreviewed_assets": "skills have no human governance decision",
    }
    for field, label in error_fields.items():
        if integrity.get(field):
            errors.append(f"{label}: {integrity[field]}")
    for field, label in warning_fields.items():
        if integrity.get(field):
            warnings.append(f"{label}: {integrity[field]}")
    for asset in data.get("assets", []):
        if asset.get("declared_name") and asset["declared_name"] != asset["name"]:
            warnings.append(f"directory/frontmatter name mismatch: {asset['name']} != {asset['declared_name']}")
        if asset.get("ownership", {}).get("update_manager") == "cc_switch_github" and not asset.get("upstream", {}).get("repository"):
            errors.append(f"CC Switch GitHub manager lacks repository metadata: {asset['name']}")
    managers = Counter(a.get("ownership", {}).get("update_manager", "unknown") for a in data.get("assets", []))
    report = {"summary": data.get("summary", {}), "update_managers": dict(managers), "errors": errors, "warnings": warnings}
    return (1 if errors else 0), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory", help="generate a read-only JSON inventory")
    inventory.add_argument("--config", type=Path, required=True)
    inventory.add_argument("--output", type=Path, required=True)
    audit = sub.add_parser("audit", help="audit an existing inventory")
    audit.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            data = build_inventory(args.config.resolve())
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(data["summary"], ensure_ascii=False))
            return 0
        data = load_json(args.inventory)
        if not isinstance(data, dict):
            raise ValueError("inventory must be a JSON object")
        code, report = audit_inventory(data)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"skill-governance: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
