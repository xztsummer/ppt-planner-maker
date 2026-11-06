from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import resolve_skills as rs  # type: ignore  # noqa: E402


def write_skill(root: Path, skill_id: str, capabilities) -> Path:
    base = root / skill_id
    base.mkdir(parents=True)
    (base / "SKILL.md").write_text(
        "---\nname: " + skill_id + "\ndescription: test fixture\n---\n",
        encoding="utf-8",
    )
    for relative in capabilities:
        target = base / relative
        if relative.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")
    return base


def skill_definition() -> dict:
    return {
        "id": "ppt-master",
        "title": "test",
        "source": "https://example.com/ppt-master",
        "license": "MIT",
        "branches": ["A", "B"],
        "capabilities": {
            "skill": {"path": "SKILL.md", "required": True},
            "routing": {"path": "workflows/routing.md", "required": True},
            "scripts": {"path": "scripts", "required": True},
            "deck": {"path": "templates/decks/中国电子云", "for": ["A"]},
        },
        "install": {
            "type": "git",
            "url": "https://example.com/ppt-master.git",
            "targetName": "ppt-master",
        },
    }


def deck_probe_definition() -> dict:
    """Manifest with a generic 'at least one deck' probe instead of a named deck."""
    data = skill_definition()
    data["capabilities"] = {
        "skill": {"path": "SKILL.md", "required": True},
        "routing": {"path": "workflows/routing.md", "required": True},
        "scripts": {"path": "scripts", "required": True},
        "decks": {
            "path": "templates/decks",
            "required": False,
            "for": ["A"],
            "requireAnyChild": True,
        },
    }
    return data


class DependencyManifestTests(unittest.TestCase):
    def test_real_manifest_loads(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        ids = {skill["id"] for skill in deps["skills"]}
        self.assertEqual(
            ids,
            {"ppt-master", "gorden-ppt-skill", "html-ppt", "guizang-ppt-skill"},
        )
        for skill in deps["skills"]:
            self.assertTrue(skill["branches"])
            self.assertTrue(skill["capabilities"])

    def test_select_skills_by_branch(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        selected = rs.select_skills(deps, [], ["A", "F"])
        self.assertEqual([skill["id"] for skill in selected], ["ppt-master"])

    def test_select_skills_by_id(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        selected = rs.select_skills(deps, ["html-ppt", "guizang-ppt-skill"], [])
        self.assertEqual(
            [skill["id"] for skill in selected], ["html-ppt", "guizang-ppt-skill"]
        )

    def test_unknown_id_raises(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        with self.assertRaises(ValueError):
            rs.select_skills(deps, ["not-a-skill"], [])

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deps.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                rs.load_deps(path)

    def test_require_any_child_must_be_bool(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deps.json"
            data = {
                "skills": [
                    {
                        "id": "fake",
                        "branches": ["A"],
                        "capabilities": {
                            "decks": {"path": "templates/decks", "requireAnyChild": "yes"}
                        },
                    }
                ]
            }
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                rs.load_deps(path)

    def test_any_commands_must_be_string_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deps.json"
            data = {
                "skills": [
                    {
                        "id": "fake",
                        "branches": ["D"],
                        "capabilities": {"skill": {"path": "SKILL.md"}},
                        "runtime": {"anyCommands": ["msedge", 3]},
                    }
                ]
            }
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                rs.load_deps(path)

    def test_real_manifest_uses_generic_deck_probe(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        ppt_master = next(s for s in deps["skills"] if s["id"] == "ppt-master")
        self.assertIn("decks", ppt_master["capabilities"])
        self.assertTrue(ppt_master["capabilities"]["decks"]["requireAnyChild"])
        self.assertEqual(
            ppt_master["capabilities"]["decks"]["childPath"],
            "templates/design_spec.md",
        )
        self.assertIn("deck-index", ppt_master["capabilities"])
        self.assertNotIn("deck:中国电子云", ppt_master["capabilities"])


class RootTests(unittest.TestCase):
    def test_root_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "ws"
            workspace.mkdir()
            explicit = base / "explicit"
            explicit.mkdir()
            dsh_home = base / "home" / ".dsh"
            (dsh_home / "skills").mkdir(parents=True)
            agents_home = base / "home" / ".agents"
            (agents_home / "skills").mkdir(parents=True)
            zcode_home = base / "home" / ".zcode"
            (zcode_home / "skills").mkdir(parents=True)

            roots = rs.build_roots(workspace, [explicit], dsh_home, agents_home, zcode_home)
            self.assertEqual(
                [root["source"] for root in roots[:9]],
                [
                    "explicit",
                    "project-dsh",
                    "project-zcode",
                    "project-agents",
                    "legacy-workspace",
                    "user-private",
                    "user-dsh",
                    "user-zcode",
                    "user-agents",
                ],
            )
            self.assertEqual(roots[-1]["source"], "claude-user")

    def test_private_root_follows_env_and_stays_unscanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"PPT_PLANNER_HOME": tmp}):
                self.assertEqual(rs.private_skills_root(), Path(tmp) / "skills")
        self.assertNotIn("user-private", rs.HOST_SCANNED_SOURCES)

    def test_duplicate_paths_are_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            workspace.mkdir()
            duplicate = workspace / ".dsh" / "skills"
            duplicate.mkdir(parents=True)
            roots = rs.build_roots(
                workspace,
                [duplicate],
                Path(tmp) / "home" / ".dsh",
                Path(tmp) / "home" / ".agents",
                Path(tmp) / "home" / ".zcode",
            )
            matches = [root for root in roots if Path(root["path"]) == duplicate.resolve()]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["source"], "explicit")


class ResolveSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ok_with_all_capabilities(self):
        root = self.base / "skills"
        bundle = write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/中国电子云/"],
        )
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["root"], str(bundle))
        self.assertEqual(result["resolvedFrom"], "test")
        self.assertTrue(result["capabilities"]["deck"]["required"])
        self.assertIn("git clone", result["install"])

    def test_incomplete_when_branch_capability_missing(self):
        root = self.base / "skills"
        write_skill(root, "ppt-master", ["workflows/routing.md", "scripts/"])
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missingRequired"], ["deck"])

    def test_deck_not_required_for_other_branch(self):
        root = self.base / "skills"
        write_skill(root, "ppt-master", ["workflows/routing.md", "scripts/"])
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["B"],
        )
        self.assertEqual(result["status"], "ok")

    def test_empty_deck_directory_is_incomplete_for_branch_a(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/"],
        )
        result = rs.resolve_skill(
            deck_probe_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missingRequired"], ["decks"])
        self.assertEqual(result["capabilities"]["decks"]["status"], "empty")

    def test_deck_directory_with_child_is_ok_for_branch_a(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/company-a/"],
        )
        result = rs.resolve_skill(
            deck_probe_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["capabilities"]["decks"]["status"], "ok")

    def test_empty_deck_directory_not_required_for_branch_b(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/"],
        )
        result = rs.resolve_skill(
            deck_probe_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["B"],
        )
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["capabilities"]["decks"]["required"])

    def test_missing_when_absent(self):
        result = rs.resolve_skill(
            skill_definition(), [{"path": str(self.base), "source": "test"}], ["A"]
        )
        self.assertEqual(result["status"], "missing")
        self.assertIsNone(result["root"])

    def test_flat_only_is_invalid(self):
        root = self.base / "skills"
        root.mkdir()
        (root / "ppt-master.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["warnings"])

    def test_flat_file_does_not_shadow_valid_bundle(self):
        flat_root = self.base / "first"
        bundle_root = self.base / "second"
        flat_root.mkdir()
        (flat_root / "ppt-master.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        write_skill(
            bundle_root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/中国电子云/"],
        )
        result = rs.resolve_skill(
            skill_definition(),
            [
                {"path": str(flat_root), "source": "first", "exists": True},
                {"path": str(bundle_root), "source": "second", "exists": True},
            ],
            ["A"],
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["root"], str(bundle_root / "ppt-master"))
        self.assertEqual(result["resolvedFrom"], "second")
        self.assertTrue(any("扁平" in warning for warning in result["warnings"]))

    def test_child_path_requires_matching_child(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/empty/"],
        )
        definition = deck_probe_definition()
        definition["capabilities"]["decks"]["childPath"] = "templates/design_spec.md"
        result = rs.resolve_skill(
            definition,
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["capabilities"]["decks"]["status"], "empty")

    def test_child_path_accepts_complete_deck(self):
        root = self.base / "skills"
        bundle = write_skill(
            root,
            "ppt-master",
            [
                "workflows/routing.md",
                "scripts/",
                "templates/decks/company-a/templates/design_spec.md",
            ],
        )
        definition = deck_probe_definition()
        definition["capabilities"]["decks"]["childPath"] = "templates/design_spec.md"
        result = rs.resolve_skill(
            definition,
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["root"], str(bundle))
        self.assertEqual(result["capabilities"]["decks"]["status"], "ok")

    def test_company_template_file_does_not_require_installed_deck(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "requirements.txt"],
        )
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        definition = next(s for s in deps["skills"] if s["id"] == "ppt-master")
        result = rs.resolve_skill(
            definition,
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
            company_template_file=True,
        )
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["capabilities"]["decks"]["required"])
        self.assertFalse(result["capabilities"]["deck-index"]["required"])

    def test_installed_deck_path_keeps_deck_probes_strict(self):
        root = self.base / "skills"
        write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "requirements.txt"],
        )
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        definition = next(s for s in deps["skills"] if s["id"] == "ppt-master")
        result = rs.resolve_skill(
            definition,
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missingRequired"], ["decks", "deck-index"])
        self.assertTrue(result["capabilities"]["decks"]["required"])
        self.assertTrue(result["capabilities"]["deck-index"]["required"])

    def test_version_from_skill_frontmatter(self):
        root = self.base / "skills"
        bundle = write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/中国电子云/"],
        )
        (bundle / "SKILL.md").write_text(
            "---\nname: ppt-master\nmetadata:\n  version: \"6.7.2\"\n---\n",
            encoding="utf-8",
        )
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["version"], "6.7.2")

    def test_shadowed_candidates(self):
        first = self.base / "first"
        second = self.base / "second"
        for root in (first, second):
            write_skill(
                root,
                "ppt-master",
                ["workflows/routing.md", "scripts/", "templates/decks/中国电子云/"],
            )
        result = rs.resolve_skill(
            skill_definition(),
            [
                {"path": str(first), "source": "first", "exists": True},
                {"path": str(second), "source": "second", "exists": True},
            ],
            ["A"],
        )
        self.assertEqual(result["root"], str(first / "ppt-master"))
        self.assertEqual(len(result["shadowed"]), 1)
        self.assertEqual(result["shadowed"][0]["source"], "second")

    def test_version_from_version_file(self):
        root = self.base / "skills"
        bundle = write_skill(
            root,
            "ppt-master",
            ["workflows/routing.md", "scripts/", "templates/decks/中国电子云/"],
        )
        (bundle / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        result = rs.resolve_skill(
            skill_definition(),
            [{"path": str(root), "source": "test", "exists": True}],
            ["A"],
        )
        self.assertEqual(result["version"], "9.9.9")


class ResolveTests(unittest.TestCase):
    def test_workspace_inside_skill_root_warns(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        result = rs.resolve(deps, [], [], rs.SKILL_ROOT, [])
        self.assertTrue(any("Skill 根目录" in warning for warning in result["warnings"]))

    def test_nonexistent_workspace_warns(self):
        deps = rs.load_deps(rs.DEFAULT_DEPS_FILE)
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            result = rs.resolve(deps, [], [], missing, [])
            self.assertTrue(any("工作区不存在" in warning for warning in result["warnings"]))


class CliTests(unittest.TestCase):
    def _write_fake_deps(self, directory: Path) -> Path:
        data = {
            "schemaVersion": 1,
            "skillName": "ppt-planner-maker",
            "skills": [
                {
                    "id": "fake-skill",
                    "source": "https://example.com/fake",
                    "license": "MIT",
                    "branches": ["A"],
                    "capabilities": {"skill": {"path": "SKILL.md", "required": True}},
                    "install": {
                        "type": "git",
                        "url": "https://example.com/fake.git",
                        "targetName": "fake-skill",
                    },
                }
            ],
        }
        path = directory / "deps.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_check_fails_for_missing_fake_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            deps = self._write_fake_deps(base)
            workspace = base / "ws"
            workspace.mkdir()
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = rs.main(
                    [
                        "--deps-file",
                        str(deps),
                        "--workspace",
                        str(workspace),
                        "--only",
                        "fake-skill",
                        "--check",
                    ]
                )
            self.assertEqual(code, 1)
            self.assertIn("fake-skill", buffer.getvalue())

    def test_json_output_is_parseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            deps = self._write_fake_deps(base)
            workspace = base / "ws"
            workspace.mkdir()
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = rs.main(
                    [
                        "--deps-file",
                        str(deps),
                        "--workspace",
                        str(workspace),
                        "--only",
                        "fake-skill",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["skills"]["fake-skill"]["status"], "missing")


class DriftTests(unittest.TestCase):
    COMMIT = "0e8d92c4e54b037b2b677f4fcaf3b01b63d38316"
    OTHER = "bc72031ab1e28ee882c452ca67f2b1e9280d197a"

    def _checkout(self, base: Path, head: str, ref_value: str = "", packed: str = "") -> Path:
        git_dir = base / ".git"
        (git_dir / "refs" / "heads").mkdir(parents=True)
        (git_dir / "HEAD").write_text(head + "\n", encoding="utf-8")
        if ref_value:
            (git_dir / "refs" / "heads" / "main").write_text(ref_value + "\n", encoding="utf-8")
        if packed:
            (git_dir / "packed-refs").write_text(
                f"# pack-refs\n{packed} refs/heads/main\n", encoding="utf-8"
            )
        return base

    def test_detached_head_matches_tested_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._checkout(Path(tmp), self.COMMIT)
            drift = rs.version_drift({"testedVersion": f"{self.COMMIT}（x）"}, root, None)
            self.assertEqual(drift["state"], "match")

    def test_branch_ref_and_packed_ref_report_drift(self):
        skill = {"testedVersion": self.COMMIT}
        with tempfile.TemporaryDirectory() as tmp:
            root = self._checkout(Path(tmp), "ref: refs/heads/main", ref_value=self.OTHER)
            self.assertEqual(rs.version_drift(skill, root, None)["state"], "drift")
        with tempfile.TemporaryDirectory() as tmp:
            root = self._checkout(Path(tmp), "ref: refs/heads/main", packed=self.OTHER)
            self.assertEqual(rs.version_drift(skill, root, None)["installed"], self.OTHER[:7])

    def test_release_comparison_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = {"testedVersion": self.COMMIT, "testedRelease": "6.8.0"}
            self.assertEqual(rs.version_drift(skill, Path(tmp), "6.7.3")["state"], "drift")
            self.assertEqual(rs.version_drift(skill, Path(tmp), "6.8.0")["state"], "match")

    def test_unreadable_version_is_unknown_not_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = {"testedVersion": self.COMMIT}
            self.assertEqual(rs.version_drift(skill, Path(tmp), None)["state"], "unknown")


if __name__ == "__main__":
    unittest.main()
