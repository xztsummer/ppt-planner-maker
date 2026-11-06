from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import verify_deck as vd  # noqa: E402

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
REL_NS = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'


def text_slide(*paragraphs: str) -> str:
    """Build a slide; '|' splits a paragraph into separate runs."""
    body = "".join(
        "<a:p>" + "".join(f"<a:r><a:t>{run}</a:t></a:r>" for run in para.split("|")) + "</a:p>"
        for para in paragraphs
    )
    return (
        f"<p:sld {A} {P}><p:cSld><p:spTree><p:sp><p:txBody>{body}</p:txBody></p:sp>"
        "</p:spTree></p:cSld></p:sld>"
    )


def picture_slide(cx: int, cy: int) -> str:
    return (
        f"<p:sld {A} {P}><p:cSld><p:spTree><p:pic><p:spPr><a:xfrm>"
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr></p:pic></p:spTree></p:cSld></p:sld>'
    )


def build_pptx(path: Path, visible: list, orphans: tuple = (), notes: tuple = ()) -> None:
    ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(len(visible)))
    rels = "".join(
        f'<Relationship Id="rId{i + 1}" Type="slide" Target="slides/slide{i + 1}.xml"/>'
        for i in range(len(visible))
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "ppt/presentation.xml",
            f"<p:presentation {P} {R}><p:sldIdLst>{ids}</p:sldIdLst>"
            '<p:sldSz cx="100" cy="100"/></p:presentation>',
        )
        archive.writestr(
            "ppt/_rels/presentation.xml.rels",
            f"<Relationships {REL_NS}>{rels}</Relationships>",
        )
        for i, slide in enumerate(visible, 1):
            archive.writestr(f"ppt/slides/slide{i}.xml", slide)
            if i in notes:
                archive.writestr(
                    f"ppt/slides/_rels/slide{i}.xml.rels",
                    f'<Relationships {REL_NS}><Relationship Id="n" '
                    'Type="http://x/relationships/notesSlide" '
                    'Target="../notesSlides/n.xml"/></Relationships>',
                )
        for i, slide in enumerate(orphans, len(visible) + 1):
            archive.writestr(f"ppt/slides/slide{i}.xml", slide)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def codes(self, report, level: str) -> list:
        return [item["code"] for item in report.findings if item["level"] == level]


class PptxTests(Base):
    def run_pptx(self, visible, expected=None, extra=(), allow=(), **kwargs):
        path = self.dir / "deck.pptx"
        build_pptx(path, visible, **kwargs)
        return vd.verify(path, expected, extra, allow)

    def test_clean_deck_passes_and_counts_notes(self):
        report = self.run_pptx([text_slide("标题"), text_slide("正文")], expected=2, notes=(2,))
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.pages, 2)
        self.assertEqual(report.extra["notesPages"], 1)
        self.assertEqual(report.findings, [])

    def test_page_count_mismatch_fails(self):
        self.assertIn("page-count", self.codes(self.run_pptx([text_slide("a")], expected=2), "FAIL"))

    def test_placeholder_on_visible_page_fails_even_split_across_runs(self):
        report = self.run_pptx([text_slide("文字内容|可根据需求修改")])
        self.assertIn("placeholder", self.codes(report, "FAIL"))
        self.assertEqual(report.findings[0]["page"], 1)

    def test_orphan_slides_with_placeholders_fail(self):
        report = self.run_pptx([text_slide("真实内容")], orphans=(text_slide("输入指标项"),))
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.pages, 1)
        self.assertEqual(report.extra["orphanSlides"], 1)
        self.assertIn("orphan-slides", self.codes(report, "FAIL"))
        self.assertIn("其中 1 个含占位内容", report.findings[0]["message"])

    def test_full_page_image_without_text_fails(self):
        self.assertIn("image-only", self.codes(self.run_pptx([picture_slide(100, 100)]), "FAIL"))

    def test_small_image_without_text_only_warns(self):
        report = self.run_pptx([picture_slide(30, 30)])
        self.assertEqual(report.status, "PASS")
        self.assertIn("no-text", self.codes(report, "WARN"))

    def test_custom_pattern_and_allow(self):
        report = self.run_pptx([text_slide("示例公司")], extra=["示例公司"])
        self.assertIn("placeholder", self.codes(report, "FAIL"))
        report = self.run_pptx([text_slide("项目名称：可信数据空间")], allow=["可信数据空间"])
        self.assertEqual(report.status, "PASS")

    def test_not_a_zip_fails(self):
        path = self.dir / "bad.pptx"
        path.write_bytes(b"not a zip")
        self.assertIn("not-pptx", self.codes(vd.verify(path, None, (), ()), "FAIL"))

    def test_html_renamed_to_pptx_fails(self):
        path = self.dir / "fake.pptx"
        path.write_text("<!doctype html><html></html>", encoding="utf-8")
        self.assertIn("wrong-extension", self.codes(vd.verify(path, None, (), ()), "FAIL"))


class HtmlTests(Base):
    def run_html(self, body: str, expected=None):
        path = self.dir / "deck.html"
        path.write_text(f"<!doctype html><html><body>{body}</body></html>", encoding="utf-8")
        return vd.verify(path, expected, (), ())

    def test_clean_deck_counts_slide_sections(self):
        (self.dir / "a.png").write_bytes(b"x")
        report = self.run_html(
            '<section class="slide light"><img src="a.png?v=1"></section>'
            '<section class="slide">二</section>',
            expected=2,
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.pages, 2)

    def test_page_mismatch_fails_and_unknown_warns(self):
        self.assertIn("page-count", self.codes(self.run_html('<div class="slide">a</div>', 2), "FAIL"))
        self.assertIn("page-count-unknown", self.codes(self.run_html("<div>a</div>", 2), "WARN"))

    def test_missing_local_resource_fails(self):
        report = self.run_html('<img src="images/none.png">')
        self.assertIn("missing-resource", self.codes(report, "FAIL"))

    def test_css_url_in_style_attribute_is_checked(self):
        report = self.run_html("<div style=\"background:url('none.jpg')\">a</div>")
        self.assertIn("missing-resource", self.codes(report, "FAIL"))

    def test_external_resource_warns(self):
        report = self.run_html(
            '<script src="https://cdn.example.com/a.js"></script><img src="//x.io/a.png">'
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(self.codes(report, "WARN").count("external-resource"), 2)

    def test_absolute_local_path_fails(self):
        report = self.run_html('<img src="C:\\tmp\\a.png">')
        self.assertIn("absolute-path", self.codes(report, "FAIL"))

    def test_data_uri_and_placeholder_in_script_are_ignored(self):
        report = self.run_html(
            '<img src="data:image/png;base64,AA"><script>var t="Lorem ipsum";</script>'
        )
        self.assertEqual(report.findings, [])

    def test_visible_placeholder_fails(self):
        self.assertIn("placeholder", self.codes(self.run_html("<p>Lorem ipsum dolor</p>"), "FAIL"))

    def test_zip_named_html_fails(self):
        path = self.dir / "fake.html"
        path.write_bytes(b"PK\x03\x04rest")
        self.assertIn("wrong-extension", self.codes(vd.verify(path, None, (), ()), "FAIL"))

    def test_plain_text_named_html_fails(self):
        path = self.dir / "fake.html"
        path.write_text("just text", encoding="utf-8")
        self.assertIn("not-html", self.codes(vd.verify(path, None, (), ()), "FAIL"))


class CliTests(Base):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(REPO / "scripts" / "verify_deck.py"), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_exit_codes_and_brief(self):
        good = self.dir / "good.pptx"
        build_pptx(good, [text_slide("内容")])
        passed = self.run_cli(str(good), "--brief")
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn("verify_deck: PASS pptx pages=1", passed.stdout)
        self.assertIn("视觉检查未覆盖", passed.stdout)

        self.assertEqual(self.run_cli(str(good), "--expected-pages", "3").returncode, 1)
        self.assertEqual(self.run_cli(str(self.dir / "none.pptx")).returncode, 2)
        other = self.dir / "a.txt"
        other.write_text("x", encoding="utf-8")
        self.assertEqual(self.run_cli(str(other)).returncode, 2)


if __name__ == "__main__":
    unittest.main()
