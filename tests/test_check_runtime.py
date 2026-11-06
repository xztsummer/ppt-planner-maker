from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_runtime as cr  # noqa: E402


def fake_finder(present):
    return lambda name: object() if name in present else None


def no_command(name):
    return None


MISSING = "definitely_missing_pkg_for_tests_123"


def skill_with_runtime(runtime):
    return {
        "id": "fake-skill",
        "branches": ["A"],
        "capabilities": {"skill": {"path": "SKILL.md", "required": True}},
        "runtime": runtime,
    }


class PackageTests(unittest.TestCase):
    def test_present_and_missing(self):
        result = cr.check_packages(["json", MISSING], fake_finder({"json"}))
        self.assertTrue(result["json"]["ok"])
        self.assertFalse(result[MISSING]["ok"])

    def test_duplicates_are_collapsed(self):
        result = cr.check_packages(["json", "json"], fake_finder({"json"}))
        self.assertEqual(list(result), ["json"])

    def test_broken_import_is_reported_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "broken_probe_for_tests.py"
            module.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
            sys.path.insert(0, tmp)
            import importlib

            importlib.invalidate_caches()
            try:
                self.assertIsNone(cr.default_finder("broken_probe_for_tests"))
            finally:
                sys.path.remove(tmp)
                sys.modules.pop("broken_probe_for_tests", None)

    def test_running_script_does_not_write_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            shutil.copytree(REPO / "scripts", scripts)
            pycache = scripts / "__pycache__"
            if pycache.exists():
                shutil.rmtree(pycache)
            completed = subprocess.run(
                [sys.executable, str(scripts / "check_runtime.py"), "--branches", "D", "--brief"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(pycache.exists(), "check_runtime 不应向 Skill 包写入 __pycache__")


class CommandTests(unittest.TestCase):
    def test_on_path(self):
        result = cr.find_command(
            "soffice", which=lambda name: "/usr/bin/soffice", common_paths=[]
        )
        self.assertEqual(result, {"ok": True, "path": "/usr/bin/soffice", "onPath": True})

    def test_common_path_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "soffice.exe"
            candidate.write_text("x", encoding="utf-8")
            result = cr.find_command("soffice", which=no_command, common_paths=[candidate])
        self.assertTrue(result["ok"])
        self.assertFalse(result["onPath"])

    def test_missing(self):
        result = cr.find_command("soffice", which=no_command, common_paths=[])
        self.assertFalse(result["ok"])
        self.assertIsNone(result["path"])


class EvaluateTests(unittest.TestCase):
    def test_required_missing_is_incomplete(self):
        skill = skill_with_runtime(
            {"python": ["json", MISSING], "optionalPython": ["json"]}
        )
        result = cr.evaluate_skill(
            skill, finder=fake_finder({"json"}), which=no_command, common_paths=[]
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missingRequired"], [MISSING])
        self.assertEqual(result["missingOptional"], [])

    def test_optional_missing_does_not_block(self):
        skill = skill_with_runtime(
            {"python": ["json"], "optionalPython": [MISSING], "optionalCommands": ["soffice"]}
        )
        result = cr.evaluate_skill(
            skill, finder=fake_finder({"json"}), which=no_command, common_paths=[]
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["missingOptional"], [MISSING])
        self.assertEqual(result["missingOptionalCommands"], ["soffice"])

    def test_required_command_missing_is_incomplete(self):
        skill = skill_with_runtime({"commands": ["soffice"]})
        result = cr.evaluate_skill(skill, which=no_command, common_paths=[])
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missingCommands"], ["soffice"])

    def test_any_commands_ok_when_one_browser_found(self):
        skill = skill_with_runtime({"anyCommands": ["msedge", "chrome"]})
        result = cr.evaluate_skill(
            skill,
            which=lambda name: "/usr/bin/chrome" if name == "chrome" else None,
            common_paths=[],
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["anyCommandsOk"], ["chrome"])
        self.assertEqual(result["missingAnyCommands"], [])

    def test_any_commands_missing_blocks_nothing_but_is_reported(self):
        skill = skill_with_runtime({"anyCommands": ["msedge", "chrome", "firefox"]})
        result = cr.evaluate_skill(skill, which=no_command, common_paths=[])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["anyCommandsOk"], [])
        self.assertEqual(result["missingAnyCommands"], ["msedge", "chrome", "firefox"])

    def test_browser_common_path_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "msedge.exe"
            candidate.write_text("x", encoding="utf-8")
            old = dict(cr.COMMON_COMMAND_PATHS)
            cr.COMMON_COMMAND_PATHS["msedge"] = [candidate]
            try:
                result = cr.find_command("msedge", which=no_command)
            finally:
                cr.COMMON_COMMAND_PATHS.clear()
                cr.COMMON_COMMAND_PATHS.update(old)
        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], str(candidate))
        self.assertFalse(result["onPath"])

    def test_no_runtime_is_ok(self):
        result = cr.evaluate_skill({"id": "x"}, which=no_command, common_paths=[])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["missingRequired"], [])


class ManifestTests(unittest.TestCase):
    def test_real_manifest_declares_runtime(self):
        deps = cr.load_deps(cr.DEFAULT_DEPS_FILE)
        for skill in deps["skills"]:
            self.assertIsInstance(skill.get("runtime"), dict, skill["id"])
            for key in ("python", "optionalPython", "commands", "optionalCommands"):
                self.assertIsInstance(skill["runtime"].get(key, []), list)

    def test_ppt_master_runtime_has_core_packages(self):
        deps = cr.load_deps(cr.DEFAULT_DEPS_FILE)
        ppt_master = next(skill for skill in deps["skills"] if skill["id"] == "ppt-master")
        self.assertIn("pptx", ppt_master["runtime"]["python"])
        self.assertIn("pathops", ppt_master["runtime"]["python"])
        self.assertNotIn("skia", ppt_master["runtime"]["python"])
        self.assertIn("soffice", ppt_master["runtime"]["optionalCommands"])


class CliTests(unittest.TestCase):
    def _write_deps(self, directory: Path, package: str) -> Path:
        data = {
            "schemaVersion": 1,
            "skillName": "ppt-planner-maker",
            "skills": [
                {
                    "id": "fake-skill",
                    "branches": ["A"],
                    "capabilities": {"skill": {"path": "SKILL.md", "required": True}},
                    "runtime": {"python": [package], "install": "pip install example"},
                }
            ],
        }
        path = directory / "deps.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_check_passes_with_present_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            deps = self._write_deps(Path(tmp), "json")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cr.main(
                    ["--deps-file", str(deps), "--only", "fake-skill", "--check"]
                )
            self.assertEqual(code, 0)
            self.assertIn("OK", buffer.getvalue())

    def test_check_fails_with_missing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            deps = self._write_deps(Path(tmp), MISSING)
            buffer = io.StringIO()
            error = io.StringIO()
            with redirect_stdout(buffer), redirect_stderr(error):
                code = cr.main(
                    ["--deps-file", str(deps), "--only", "fake-skill", "--json", "--check"]
                )
            self.assertEqual(code, 1)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["checks"]["fake-skill"]["status"], "incomplete")

    def test_brief_output_is_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            deps = self._write_deps(Path(tmp), "json")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cr.main(
                    ["--deps-file", str(deps), "--only", "fake-skill", "--brief"]
                )
            self.assertEqual(code, 0)
            lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
            self.assertEqual(len(lines), 1)
            self.assertIn("fake-skill=ok", lines[0])

    def test_invalid_branch_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            deps = self._write_deps(Path(tmp), "json")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = cr.main(["--deps-file", str(deps), "--branches", "Z"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
