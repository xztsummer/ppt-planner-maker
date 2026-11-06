from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import setup as st  # type: ignore  # noqa: E402

MISSING = "definitely_missing_pkg_for_tests_123"


def fake_deps(directory: Path, runtime_python=None, tested_version="") -> Path:
    data = {
        "schemaVersion": 1,
        "skillName": "ppt-planner-maker",
        "skills": [
            {
                "id": "fake-skill",
                "title": "test",
                "source": "https://example.com/fake",
                "license": "MIT",
                "testedVersion": tested_version,
                "branches": ["A"],
                "capabilities": {"skill": {"path": "SKILL.md", "required": True}},
                "runtime": {"python": runtime_python or []},
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


class ExtractCommitTests(unittest.TestCase):
    def test_finds_leading_commit(self):
        version = "0e8d92c4e54b037b2b677f4fcaf3b01b63d38316（fork main，2026-10-21）"
        self.assertEqual(
            st.tested_commit(version),
            "0e8d92c4e54b037b2b677f4fcaf3b01b63d38316",
        )

    def test_finds_commit_after_parenthesis(self):
        version = "1.0.20（7d4a61cbd8363b92e4a30784f8ca460a0a2b0a33，2026-06-22）"
        self.assertEqual(
            st.tested_commit(version),
            "7d4a61cbd8363b92e4a30784f8ca460a0a2b0a33",
        )

    def test_returns_none_for_semver(self):
        self.assertIsNone(st.tested_commit("1.0.20"))

    def test_real_manifest_versions_are_pinnable(self):
        from resolve_skills import load_deps, DEFAULT_DEPS_FILE  # type: ignore

        deps = load_deps(DEFAULT_DEPS_FILE)
        for skill in deps["skills"]:
            self.assertIsNotNone(
                st.tested_commit(skill.get("testedVersion", "")),
                skill["id"],
            )


class PipNameTests(unittest.TestCase):
    def test_known_mappings(self):
        self.assertEqual(st._pip_name("yaml"), "PyYAML")
        self.assertEqual(st._pip_name("pptx"), "python-pptx")
        self.assertEqual(st._pip_name("pathops"), "skia-pathops")
        self.assertEqual(st._pip_name("xlsxwriter"), "XlsxWriter")
        self.assertEqual(st._pip_name("uharfbuzz"), "uharfbuzz")
        self.assertEqual(st._pip_name("edge_tts"), "edge-tts")
        self.assertEqual(st._pip_name("fitz"), "PyMuPDF")

    def test_every_manifest_runtime_import_maps_to_pip_name(self):
        from resolve_skills import DEFAULT_DEPS_FILE, load_deps  # type: ignore

        deps = load_deps(DEFAULT_DEPS_FILE)
        for skill in deps["skills"]:
            runtime = skill.get("runtime") or {}
            for key in ("python", "optionalPython"):
                for import_name in runtime.get(key, []):
                    with self.subTest(skill=skill["id"], import_name=import_name):
                        self.assertTrue(import_name)
                        self.assertIn(import_name, st.IMPORT_TO_PIP)
                        self.assertNotIn("skia", runtime.get(key, []))

    def test_unknown_passthrough(self):
        self.assertEqual(st._pip_name("requests"), "requests")


class PipFailureHintTests(unittest.TestCase):
    def test_skia_hint(self):
        cmd = [sys.executable, "-m", "pip", "install", "skia-pathops"]
        hint = st._pip_failure_hint(cmd)
        self.assertIsNotNone(hint)
        self.assertIn("3.11/3.12", hint)

    def test_unrelated_command_has_no_hint(self):
        self.assertIsNone(
            st._pip_failure_hint([sys.executable, "-m", "pip", "install", "requests"])
        )
        self.assertIsNone(st._pip_failure_hint(["git", "clone", "https://example.com"]))


class ChooseRootTests(unittest.TestCase):
    def test_explicit_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            existing = base / "exists"
            existing.mkdir()
            chosen = st.choose_target_root([str(base / "new")], [{"source": "user-dsh", "path": str(existing), "exists": True}])
            self.assertEqual(chosen, base / "new")

    def test_default_is_private_root_not_existing_host_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with mock.patch.dict(os.environ, {"PPT_PLANNER_HOME": str(base / "private")}):
                chosen = st.choose_target_root(
                    [], [{"source": "user-dsh", "path": str(base / "dsh"), "exists": True}]
                )
            self.assertEqual(chosen, base / "private" / "skills")


class RunActionsTests(unittest.TestCase):
    def test_failed_clone_skips_checkout(self):
        plan = {
            "clone": [{"id": "a", "cmd": ["git", "clone", "u", "t"]}],
            "pip": [],
            "pin": [{"id": "a", "cmd": ["git", "-C", "t", "checkout", "c"], "commit": "c"}],
            "manual": [],
        }
        with mock.patch.object(st.subprocess, "run") as run, redirect_stdout(io.StringIO()):
            run.return_value = mock.Mock(returncode=128)
            self.assertFalse(st._run_actions(plan))
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args[0][0][1], "clone")

    def test_successful_clone_runs_checkout(self):
        plan = {
            "clone": [{"id": "a", "cmd": ["git", "clone", "u", "t"]}],
            "pip": [],
            "pin": [{"id": "a", "cmd": ["git", "-C", "t", "checkout", "c"], "commit": "c"}],
            "manual": [],
        }
        with mock.patch.object(st.subprocess, "run") as run, redirect_stdout(io.StringIO()):
            run.return_value = mock.Mock(returncode=0)
            self.assertTrue(st._run_actions(plan))
        self.assertEqual(run.call_count, 2)


class PinDefaultTests(unittest.TestCase):
    COMMIT = "0e8d92c4e54b037b2b677f4fcaf3b01b63d38316"

    def _plan(self, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "ws"
            workspace.mkdir()
            deps = fake_deps(base, tested_version=f"{self.COMMIT}（test）")
            out = io.StringIO()
            env = {"PPT_PLANNER_HOME": str(base / "private"), "PPT_PLANNER_SKILLS_DIR": ""}
            with mock.patch.dict(os.environ, env), redirect_stdout(out):
                code = st.main(
                    ["--workspace", str(workspace), "--deps-file", str(deps), "--json", *flags]
                )
            self.assertEqual(code, 0)
            return json.loads(out.getvalue()), base

    def test_pinned_by_default_into_private_root(self):
        plan, base = self._plan()
        self.assertEqual(plan["pin"][0]["commit"], self.COMMIT)
        self.assertEqual(Path(plan["targetRoot"]), base / "private" / "skills")

    def test_latest_skips_pin(self):
        plan, _ = self._plan("--latest")
        self.assertEqual(plan["pin"], [])
        self.assertEqual(len(plan["clone"]), 1)

    def test_pin_flag_stays_accepted(self):
        plan, _ = self._plan("--pin")
        self.assertEqual(plan["pin"][0]["commit"], self.COMMIT)


class OutsideSkillTests(unittest.TestCase):
    def test_refuses_skill_root(self):
        message = st._ensure_outside_skill(st.SKILL_ROOT / "scripts")
        self.assertIsNotNone(message)

    def test_allows_external(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(st._ensure_outside_skill(Path(tmp)))


class BuildPlanTests(unittest.TestCase):
    def _prepare(self, with_skill: bool, runtime_python=None):
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        root = Path(base.name)
        workspace = root / "ws"
        workspace.mkdir()
        skills = root / "skills"
        if with_skill:
            (skills / "fake-skill").mkdir(parents=True)
            (skills / "fake-skill" / "SKILL.md").write_text(
                "---\nname: fake-skill\n---\n", encoding="utf-8"
            )
        deps = fake_deps(root, runtime_python=runtime_python)
        return root, workspace, skills, deps

    def test_missing_dependency_plans_clone_and_pip(self):
        root, workspace, skills, deps = self._prepare(
            with_skill=False, runtime_python=[MISSING]
        )
        # give testedVersion a commit so --pin produces a checkout step
        deps.write_text(
            deps.read_text(encoding="utf-8").replace(
                '"testedVersion": ""',
                '"testedVersion": "0e8d92c4e54b037b2b677f4fcaf3b01b63d38316（test）"',
            ),
            encoding="utf-8",
        )
        from resolve_skills import build_roots, load_deps, select_skills  # type: ignore

        deps_data = load_deps(deps)
        selected = select_skills(deps_data, [], ["A"])
        roots = build_roots(workspace, [skills], Path(root / "h1"), Path(root / "h2"), Path(root / "h3"))
        target = skills
        plan = st.build_plan_for_run(
            deps_data, selected, roots, workspace, ["A"], target, pin=True
        )
        self.assertEqual(len(plan["clone"]), 1)
        self.assertEqual(plan["clone"][0]["cmd"][0], "git")
        self.assertIn("checkout", plan["pin"][0]["cmd"])
        self.assertEqual(len(plan["pin"]), 1)
        self.assertEqual(len(plan["pip"]), 1)
        self.assertIn("-r", plan["pip"][0]["cmd"])

    def test_ready_dependency_with_missing_package_plans_requirements(self):
        root, workspace, skills, deps = self._prepare(
            with_skill=True, runtime_python=[MISSING]
        )
        (skills / "fake-skill" / "requirements.txt").write_text(
            f"{MISSING}\n", encoding="utf-8"
        )
        from resolve_skills import build_roots, load_deps, select_skills  # type: ignore

        deps_data = load_deps(deps)
        selected = select_skills(deps_data, [], ["A"])
        roots = build_roots(workspace, [skills], Path(root / "h1"), Path(root / "h2"), Path(root / "h3"))
        with mock.patch("resolve_skills.version_drift", return_value={"state": "match"}):
            plan = st.build_plan_for_run(
            deps_data, selected, roots, workspace, ["A"], skills, pin=False
        )
        self.assertEqual(plan["clone"], [])
        self.assertEqual(len(plan["pip"]), 1)
        self.assertIn("-r", plan["pip"][0]["cmd"])
        self.assertIn("fake-skill", plan["ready"][0] if plan["ready"] else "")

    def test_flat_invalid_is_manual(self):
        root, workspace, skills, deps = self._prepare(with_skill=False)
        (skills).mkdir(parents=True, exist_ok=True)
        (skills / "fake-skill.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        from resolve_skills import build_roots, load_deps, select_skills  # type: ignore

        deps_data = load_deps(deps)
        selected = select_skills(deps_data, [], ["A"])
        roots = build_roots(workspace, [skills], Path(root / "h1"), Path(root / "h2"), Path(root / "h3"))
        plan = st.build_plan_for_run(
            deps_data, selected, roots, workspace, ["A"], skills, pin=False
        )
        self.assertEqual(plan["clone"], [])
        self.assertEqual(len(plan["manual"]), 1)


class CliTests(unittest.TestCase):
    def test_plan_mode_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "ws"
            workspace.mkdir()
            skills = base / "skills"
            (skills / "fake-skill").mkdir(parents=True)
            (skills / "fake-skill" / "SKILL.md").write_text(
                "---\nname: fake-skill\n---\n", encoding="utf-8"
            )
            deps = fake_deps(base)
            before = sorted(p.name for p in skills.rglob("*"))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "scripts" / "setup.py"),
                    "--workspace",
                    str(workspace),
                    "--deps-file",
                    str(deps),
                    "--skills-dir",
                    str(skills),
                    "--branches",
                    "A",
                ],
                cwd=str(workspace),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("需要手动处理", completed.stdout)
            after = sorted(p.name for p in skills.rglob("*"))
            self.assertEqual(before, after)

    def test_json_plan_is_parseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "ws"
            workspace.mkdir()
            deps = fake_deps(base, runtime_python=["json"])
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "scripts" / "setup.py"),
                    "--workspace",
                    str(workspace),
                    "--deps-file",
                    str(deps),
                    "--skills-dir",
                    str(base / "skills"),
                    "--branches",
                    "A",
                    "--json",
                ],
                cwd=str(workspace),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIn("targetRoot", payload)
            planned_ids = {action["id"] for action in payload["clone"] + payload["manual"]}
            self.assertIn("fake-skill", planned_ids)

    def test_no_bytecode_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            scripts = base / "scripts"
            scripts.mkdir()
            for name in (
                "setup.py",
                "resolve_skills.py",
                "check_runtime.py",
                "doctor.py",
                "deps.json",
            ):
                (scripts / name).write_bytes((REPO / "scripts" / name).read_bytes())
            workspace = base / "ws"
            workspace.mkdir()
            completed = subprocess.run(
                [sys.executable, str(scripts / "setup.py"), "--branches", "A", "--json"],
                cwd=str(workspace),
                capture_output=True,
                text=True,
            )
            self.assertIn(completed.returncode, (0, 1, 2))
            self.assertFalse((scripts / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
