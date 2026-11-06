from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_skill  # type: ignore  # noqa: E402


class FrontmatterTests(unittest.TestCase):
    def test_folded_description(self):
        text = "---\nname: ppt-planner-maker\ndescription: >-\n  line one\n  line two\n---\n\nbody\n"
        data = check_skill.parse_frontmatter(text)
        self.assertEqual(data["name"], "ppt-planner-maker")
        self.assertEqual(data["description"], "line one line two")

    def test_missing_frontmatter(self):
        self.assertEqual(check_skill.parse_frontmatter("no frontmatter\n"), {})

    def test_unclosed_frontmatter(self):
        self.assertEqual(check_skill.parse_frontmatter("---\nname: x\n"), {})


class TableTests(unittest.TestCase):
    def test_table_cells(self):
        self.assertEqual(check_skill.table_cells("| A | b | c |"), ["A", "b", "c"])

    def test_branch_table(self):
        text = (
            "| 分支 | 条件 | Skill |\n"
            "|---|---|---|\n"
            "| A | company | `ppt-master` |\n"
            "| B | html | `html-ppt` |\n"
        )
        mapping = check_skill.branch_table(text, {"ppt-master", "html-ppt"})
        self.assertEqual(mapping, {"A": {"ppt-master"}, "B": {"html-ppt"}})

    def test_production_table(self):
        text = (
            "### A. company\n"
            "- Skill：`{skill:ppt-master}/SKILL.md`。\n"
            "### B. html\n"
            "- Skill：`{skill:html-ppt}/SKILL.md`。\n"
        )
        mapping = check_skill.production_table(text, {"ppt-master", "html-ppt"})
        self.assertEqual(mapping, {"A": {"ppt-master"}, "B": {"html-ppt"}})

    def test_strip_fenced_code(self):
        text = "before\n```\n[bad](missing.md)\n```\nafter [good](README.md)\n"
        stripped = check_skill.strip_fenced_code(text)
        self.assertNotIn("bad", stripped)
        self.assertIn("good", stripped)


class RepositoryTests(unittest.TestCase):
    def test_repository_passes_static_checks(self):
        errors, warnings = check_skill.run_checks()
        self.assertEqual(errors, [], msg="\n".join(errors))
        runtime_dir_warnings = {
            f"仓库内出现运行目录 {name}/；产物应写到目标工作区"
            for name in ("projects", "output", "_build")
        }
        unexpected = [item for item in warnings if item not in runtime_dir_warnings]
        self.assertEqual(unexpected, [], msg="\n".join(unexpected))

    def test_runtime_directory_warning_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "output").mkdir()
            with mock.patch.object(check_skill, "ROOT", root):
                errors, warnings = [], []
                check_skill.check_structure(errors, warnings)
            self.assertEqual(errors, [])
            self.assertIn(
                "仓库内出现运行目录 output/；产物应写到目标工作区", warnings
            )
            self.assertTrue((root / "output").is_dir())


if __name__ == "__main__":
    unittest.main()
