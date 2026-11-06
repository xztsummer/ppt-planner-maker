from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
DOCTOR = REPO / "scripts" / "doctor.py"


class DoctorCliTests(unittest.TestCase):
    def _prepare(
        self, base: Path, with_skill: bool = True, with_deck_probe: bool = False
    ) -> tuple[Path, Path]:
        workspace = base / "ws"
        workspace.mkdir()
        skills = base / "skills"
        bundle = skills / "fake-skill"
        bundle.mkdir(parents=True)
        if with_skill:
            (bundle / "SKILL.md").write_text(
                "---\nname: fake-skill\ndescription: test\n---\n",
                encoding="utf-8",
            )
        deps = base / "deps.json"
        capabilities = {"skill": {"path": "SKILL.md", "required": True}}
        if with_deck_probe:
            capabilities.update(
                {
                    "decks": {
                        "path": "templates/decks",
                        "for": ["A"],
                        "requireAnyChild": True,
                    },
                    "deck-index": {
                        "path": "templates/decks/decks_index.json",
                        "for": ["A"],
                    },
                }
            )
        deps.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "skillName": "ppt-planner-maker",
                    "skills": [
                        {
                            "id": "fake-skill",
                            "branches": ["A"],
                            "capabilities": capabilities,
                            "runtime": {"python": ["json"], "install": "pip install nothing"},
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return workspace, deps

    def _run(
        self,
        workspace: Path,
        deps: Path,
        skills: Path,
        company_template_file: bool = False,
    ):
        command = [
                sys.executable,
                str(DOCTOR),
                "--workspace",
                str(workspace),
                "--deps-file",
                str(deps),
                "--skills-dir",
                str(skills),
                "--branches",
                "A",
                "--brief",
        ]
        if company_template_file:
            command.append("--company-template-file")
        return subprocess.run(
            command,
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )

    def test_ready_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace, deps = self._prepare(base)
            completed = self._run(workspace, deps, base / "skills")
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("fake-skill=ok", completed.stdout)
            self.assertIn("ready=1/1", completed.stdout)

    def test_host_scanned_install_gets_bypass_hint_and_private_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace, deps = self._prepare(base)
            common = [
                sys.executable, str(DOCTOR), "--workspace", str(workspace),
                "--deps-file", str(deps), "--branches", "A",
            ]
            project_root = workspace / ".dsh" / "skills"
            project_root.mkdir(parents=True)
            shutil.copytree(base / "skills" / "fake-skill", project_root / "fake-skill")
            env = {**os.environ, "PPT_PLANNER_HOME": str(base / "private"), "PYTHONIOENCODING": "utf-8"}
            env.pop("PPT_PLANNER_SKILLS_DIR", None)
            scanned = subprocess.run(common, capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertIn("宿主可能绕过编排层", scanned.stdout)

            shutil.rmtree(project_root / "fake-skill")
            private_root = base / "private" / "skills"
            private_root.mkdir(parents=True)
            shutil.copytree(base / "skills" / "fake-skill", private_root / "fake-skill")
            hidden = subprocess.run(common, capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertNotIn("宿主可能绕过编排层", hidden.stdout)
            self.assertIn("路径: OK", hidden.stdout)

    def test_missing_skill_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace, deps = self._prepare(base, with_skill=False)
            completed = self._run(workspace, deps, base / "skills")
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("fake-skill=missing", completed.stdout)

    def test_company_template_file_bypasses_deck_but_default_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace, deps = self._prepare(base, with_deck_probe=True)
            default = self._run(workspace, deps, base / "skills")
            self.assertEqual(default.returncode, 1)
            self.assertIn("decks", default.stdout)
            raw_template = self._run(
                workspace, deps, base / "skills", company_template_file=True
            )
            self.assertEqual(
                raw_template.returncode, 0, raw_template.stderr + raw_template.stdout
            )
            self.assertIn("ready=1/1", raw_template.stdout)

    def test_doctor_does_not_write_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace, deps = self._prepare(base)
            scripts = base / "scripts"
            scripts.mkdir()
            for name in ("doctor.py", "resolve_skills.py", "check_runtime.py", "deps.json"):
                (scripts / name).write_bytes((REPO / "scripts" / name).read_bytes())
            completed = subprocess.run(
                [
                    sys.executable,
                    str(scripts / "doctor.py"),
                    "--workspace",
                    str(workspace),
                    "--deps-file",
                    str(deps),
                    "--skills-dir",
                    str(base / "skills"),
                    "--branches",
                    "A",
                    "--brief",
                ],
                cwd=str(workspace),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertFalse((scripts / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
