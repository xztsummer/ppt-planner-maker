from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import resolve_skills as rs  # noqa: E402


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

            roots = rs.build_roots(workspace, [explicit], dsh_home, agents_home)
            self.assertEqual(
                [root["source"] for root in roots[:6]],
                [
                    "explicit",
                    "project-dsh",
                    "project-agents",
                    "legacy-workspace",
                    "user-dsh",
                    "user-agents",
                ],
            )
            self.assertEqual(roots[-1]["source"], "claude-user")

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


if __name__ == "__main__":
    unittest.main()
