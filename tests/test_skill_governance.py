from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "skill-governance" / "scripts" / "skill_governance.py"
SPEC = importlib.util.spec_from_file_location("skill_governance", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def make_skill(root: Path, name: str, body: str = "instructions") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}.\n---\n\n{body}\n", encoding="utf-8"
    )
    return skill


class GovernanceTests(unittest.TestCase):
    def test_inventory_detects_link_divergence_and_optional_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            canonical = base / "canonical"
            clients = base / "claude"
            canonical.mkdir()
            clients.mkdir()
            alpha = make_skill(canonical, "alpha")
            make_skill(clients, "alpha", "different")
            try:
                os.symlink(alpha, clients / "linked-alpha", target_is_directory=True)
            except OSError:
                pass

            codex = base / "config.toml"
            codex.write_text(
                f'[[skills.config]]\npath = "{(alpha / "SKILL.md").as_posix()}"\nenabled = true\n', encoding="utf-8"
            )
            lock = base / "lock.json"
            lock.write_text(json.dumps({"skills": {"alpha": {"sourceType": "github", "source": "acme/skills"}}}), encoding="utf-8")
            database = base / "cc.db"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE skills (directory TEXT, repo_owner TEXT, repo_name TEXT)")
            connection.execute("INSERT INTO skills VALUES ('alpha', 'acme', 'skills')")
            connection.commit()
            connection.close()
            overrides = base / "overrides.json"
            overrides.write_text(json.dumps({"skills": {"alpha": {"decision": "keep", "reason": "test"}}}), encoding="utf-8")
            config = base / "governance.json"
            config.write_text(json.dumps({
                "canonical_roots": [str(canonical)],
                "client_roots": {"claude": str(clients)},
                "codex_configs": [str(codex)],
                "lock_files": [str(lock)],
                "cc_switch_databases": [str(database)],
                "overrides_file": str(overrides),
            }), encoding="utf-8")

            data = MODULE.build_inventory(config)
            self.assertEqual(data["summary"]["skill_count"], 1)
            self.assertEqual(data["summary"]["codex_enabled_count"], 1)
            self.assertTrue(data["assets"][0]["ownership"]["cc_switch_managed"])
            self.assertEqual(data["assets"][0]["upstream"]["repository"], "acme/skills")
            self.assertEqual(len(data["integrity"]["same_name_noncanonical_instances"]), 1)
            code, report = MODULE.audit_inventory(data)
            self.assertEqual(code, 0)
            self.assertTrue(any("same-name" in item for item in report["warnings"]))

    def test_audit_fails_for_stale_rows_and_missing_paths(self):
        data = {
            "summary": {}, "assets": [],
            "integrity": {
                "warnings_during_discovery": [],
                "missing_codex_paths": ["missing/SKILL.md"],
                "stale_lock_entries": ["old"],
                "cc_switch_rows_without_physical_source": ["ghost"],
                "broken_links": [],
            },
        }
        code, report = MODULE.audit_inventory(data)
        self.assertEqual(code, 1)
        self.assertEqual(len(report["errors"]), 3)

    def test_recovery_policy_protects_source_less_assets(self):
        self.assertEqual(
            MODULE.recovery_policy(None, "manual_or_upstream_specific"),
            "protect_or_export_before_delete",
        )

    def test_frontmatter_folded_scalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_file = Path(tmp) / "SKILL.md"
            skill_file.write_text(
                "---\nname: >-\n  folded-name\ndescription: |\n  first line\n  second line\n---\n",
                encoding="utf-8",
            )
            metadata = MODULE.parse_frontmatter(skill_file)
            self.assertEqual(metadata["name"], "folded-name")
            self.assertEqual(metadata["description"], "first line\nsecond line")


if __name__ == "__main__":
    unittest.main()
