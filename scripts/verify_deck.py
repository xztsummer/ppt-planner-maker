#!/usr/bin/env python3
"""Read-only structural check of a finished PPTX or HTML deck.

Checks what a machine can prove before delivery: visible page count, leftover
placeholder text, image-only pages, hidden orphan slides, broken local
resources.  It never replaces looking at rendered pages.

Exit code: 0 pass (warnings allowed), 1 any FAIL, 2 usage or read error.

Examples::

    python scripts/verify_deck.py out.pptx --expected-pages 18
    python scripts/verify_deck.py out.html --brief
    python scripts/verify_deck.py out.pptx --pattern "示例公司" --json
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import unquote
from xml.etree import ElementTree

sys.dont_write_bytecode = True

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
R_ID = "{%s}id" % NS["r"]
SLIDE_PART_RE = re.compile(r"ppt/slides/slide\d+\.xml")
NOTES_REL = "/notesSlide"
FULL_PAGE_RATIO = 0.7

PLACEHOLDERS = [
    r"输入指标项",
    r"文字内容可根据",
    r"单击此处",
    r"点击(此处)?(输入|添加)",
    r"请(在此)?输入",
    r"此处(输入|添加)",
    r"项目名称",
    r"Lorem\s+ipsum",
    r"Vivamus",
    r"Click to (edit|add)",
    r"Key Words Here",
    r"\bx{3,}\b",
]
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//", re.I)
IGNORED_SCHEME_RE = re.compile(r"^(?:data|blob|mailto|tel|javascript|about):", re.I)
LOCAL_ABSOLUTE_RE = re.compile(r"^(?:file:|[a-z]:[\\/]|/)", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.I)
CSS_IMPORT_RE = re.compile(r"@import\s+(?:url\(\s*)?[\"']?([^\s\"')]+)", re.I)


def css_resources(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return CSS_URL_RE.findall(text) + CSS_IMPORT_RE.findall(text)


RESOURCE_ATTRS = {
    "img": ("src",),
    "script": ("src",),
    "source": ("src",),
    "video": ("src", "poster"),
    "audio": ("src",),
    "iframe": ("src",),
    "link": ("href",),
}


class Report:
    def __init__(self, path: Path, kind: str) -> None:
        self.path = path
        self.kind = kind
        self.pages: Optional[int] = None
        self.findings: List[Dict[str, Any]] = []
        self.extra: Dict[str, Any] = {}

    def add(self, level: str, code: str, message: str, page: Optional[int] = None) -> None:
        self.findings.append({"level": level, "code": code, "page": page, "message": message})

    def count(self, level: str) -> int:
        return sum(1 for item in self.findings if item["level"] == level)

    @property
    def status(self) -> str:
        return "FAIL" if self.count("FAIL") else "PASS"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "file": str(self.path),
            "type": self.kind,
            "status": self.status,
            "pages": self.pages,
            "findings": self.findings,
            "visualCheck": "not covered; inspect rendered pages separately",
            **self.extra,
        }


def _compile(extra: Sequence[str], allow: Sequence[str]) -> tuple:
    return (
        [re.compile(item, re.I) for item in PLACEHOLDERS + list(extra)],
        [re.compile(item, re.I) for item in allow],
    )


def _placeholder_hits(texts: Sequence[str], patterns, allow) -> List[str]:
    hits: List[str] = []
    for text in texts:
        if any(item.search(text) for item in allow):
            continue
        if any(item.search(text) for item in patterns) and text not in hits:
            hits.append(text)
    return hits


def _paragraph_texts(root: ElementTree.Element) -> List[str]:
    """Join runs per paragraph, so a placeholder split across runs still matches."""
    result: List[str] = []
    for paragraph in root.iter("{%s}p" % NS["a"]):
        text = "".join(node.text or "" for node in paragraph.iter("{%s}t" % NS["a"])).strip()
        if text:
            result.append(text)
    return result


def _rels(archive: zipfile.ZipFile, part: str) -> List[ElementTree.Element]:
    directory, name = posixpath.split(part)
    rels_path = f"{directory}/_rels/{name}.rels"
    if rels_path not in archive.namelist():
        return []
    return list(ElementTree.fromstring(archive.read(rels_path)))


def _target(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), target))


def _largest_picture_ratio(root: ElementTree.Element, slide_area: int) -> float:
    best = 0.0
    if slide_area <= 0:
        return best
    for picture in root.iter("{%s}pic" % NS["p"]):
        ext = picture.find(".//a:xfrm/a:ext", NS)
        if ext is None:
            continue
        try:
            area = int(ext.get("cx", "0")) * int(ext.get("cy", "0"))
        except ValueError:
            continue
        best = max(best, area / slide_area)
    return best


def check_pptx(path: Path, expected: Optional[int], patterns, allow) -> Report:
    report = Report(path, "pptx")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        report.add("FAIL", "not-pptx", "不是有效的 PPTX（无法按 zip 打开）")
        return report
    with archive:
        if "ppt/presentation.xml" not in archive.namelist():
            report.add("FAIL", "not-pptx", "缺少 ppt/presentation.xml，不是有效的 PPTX")
            return report
        presentation = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
        relations = {
            item.get("Id"): item.get("Target", "")
            for item in _rels(archive, "ppt/presentation.xml")
        }
        size = presentation.find("p:sldSz", NS)
        slide_area = 0
        if size is not None:
            slide_area = int(size.get("cx", "0")) * int(size.get("cy", "0"))

        visible: List[str] = []
        for slide_id in presentation.findall("p:sldIdLst/p:sldId", NS):
            target = relations.get(slide_id.get(R_ID))
            if target:
                visible.append(_target("ppt/presentation.xml", target))
        report.pages = len(visible)
        if not visible:
            report.add("FAIL", "no-pages", "没有可见幻灯片")

        notes = 0
        for number, part in enumerate(visible, 1):
            if part not in archive.namelist():
                report.add("FAIL", "broken-slide", f"幻灯片部件缺失：{part}", number)
                continue
            root = ElementTree.fromstring(archive.read(part))
            texts = _paragraph_texts(root)
            if root.get("show") == "0":
                report.add("WARN", "hidden-page", "该页设为隐藏放映", number)
            for hit in _placeholder_hits(texts, patterns, allow):
                report.add("FAIL", "placeholder", f"残留占位内容：{hit[:80]}", number)
            if not texts:
                has_picture = root.find(".//p:pic", NS) is not None
                has_frame = root.find(".//p:graphicFrame", NS) is not None
                if has_picture and _largest_picture_ratio(root, slide_area) >= FULL_PAGE_RATIO:
                    report.add("FAIL", "image-only", "整页是一张图且没有文本，不可编辑", number)
                elif not has_frame:
                    report.add("WARN", "no-text", "该页没有文本", number)
            if any(NOTES_REL in (item.get("Type") or "") for item in _rels(archive, part)):
                notes += 1
        report.extra["notesPages"] = notes

        parts = [name for name in archive.namelist() if SLIDE_PART_RE.fullmatch(name)]
        orphans = sorted(set(parts) - set(visible))
        report.extra["orphanSlides"] = len(orphans)
        if orphans:
            residual = 0
            for part in orphans:
                texts = _paragraph_texts(ElementTree.fromstring(archive.read(part)))
                if _placeholder_hits(texts, patterns, allow):
                    residual += 1
            report.add(
                "FAIL" if residual else "WARN",
                "orphan-slides",
                f"包内有 {len(orphans)} 个未显示的幻灯片部件（其中 {residual} 个含占位内容）；"
                "放映看不到，但内容仍留在文件里，请用 clean_deck.py 清理",
            )
    if expected is not None and report.pages != expected:
        report.add("FAIL", "page-count", f"可见页数 {report.pages}，确认稿为 {expected}")
    return report


class _DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resources: List[str] = []
        self.stylesheets: List[str] = []
        self.texts: List[str] = []
        self.slide_classes = 0
        self.sections = 0
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        values = dict(attrs)
        if tag == "link" and "stylesheet" in (values.get("rel") or "").lower().split() and values.get("href"):
            self.stylesheets.append(values["href"])
        if tag in {"script", "style"}:
            self._skip += 1
        if tag == "section":
            self.sections += 1
        if "slide" in (values.get("class") or "").split():
            self.slide_classes += 1
        for attr in RESOURCE_ATTRS.get(tag, ()):
            if values.get(attr):
                self.resources.append(values[attr])
        if values.get("style"):
            self.resources.extend(CSS_URL_RE.findall(values["style"]))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self.lasttag == "style":
            self.resources.extend(css_resources(data))
            self.stylesheets.extend(CSS_IMPORT_RE.findall(data))
        if not self._skip and data.strip():
            self.texts.append(data.strip())


def check_html(path: Path, raw: bytes, expected: Optional[int], patterns, allow) -> Report:
    report = Report(path, "html")
    parser = _DeckParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()

    pages = parser.slide_classes or parser.sections
    report.pages = pages or None
    if expected is not None:
        if not pages:
            report.add("WARN", "page-count-unknown", f"无法识别页数，确认稿为 {expected}，请在浏览器核对")
        elif pages != expected:
            report.add("FAIL", "page-count", f"识别到 {pages} 页，确认稿为 {expected}")

    for hit in _placeholder_hits(parser.texts, patterns, allow):
        report.add("FAIL", "placeholder", f"残留占位内容：{hit[:80]}")

    seen = set()
    pending = [(path.parent, r, r in parser.stylesheets) for r in parser.resources]
    while pending:
        base, resource, stylesheet = pending.pop()
        resource = resource.strip()
        key = (str(base.resolve()), resource, stylesheet)
        if not resource or key in seen or resource.startswith("#"):
            continue
        seen.add(key)
        if IGNORED_SCHEME_RE.match(resource):
            continue
        if EXTERNAL_RE.match(resource):
            report.add("WARN", "external-resource", f"外部资源，离线未验证：{resource[:100]}")
            continue
        if LOCAL_ABSOLUTE_RE.match(resource):
            report.add("FAIL", "absolute-path", f"本机绝对路径，换机器后失效：{resource[:100]}")
            continue
        relative = unquote(re.split(r"[?#]", resource, maxsplit=1)[0])
        target = (base / relative).resolve()
        if relative and not target.is_file():
            report.add("FAIL", "missing-resource", f"本地资源缺失：{resource[:100]}")
        elif relative and (stylesheet or target.suffix.lower() == ".css"):
            css = target.read_text(encoding="utf-8", errors="replace")
            imports = CSS_IMPORT_RE.findall(re.sub(r"/\*.*?\*/", "", css, flags=re.S))
            pending.extend((target.parent, r, r in imports) for r in css_resources(css))
    return report


def verify(path: Path, expected: Optional[int], extra: Sequence[str], allow: Sequence[str]) -> Report:
    patterns, allowed = _compile(extra, allow)
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix not in {".pptx", ".html", ".htm"}:
        raise ValueError(f"不支持的文件类型：{suffix or '(无扩展名)'}；只接受 .pptx / .html / .htm")

    head = raw[:2048].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    looks_html = head.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))
    if suffix == ".pptx":
        if looks_html:
            report = Report(path, "html")
            report.add(
                "FAIL",
                "wrong-extension",
                "内容是 HTML，却使用 .pptx 扩展名；它不能在 PowerPoint 中编辑",
            )
            return report
        return check_pptx(path, expected, patterns, allowed)

    if raw[:2] == b"PK":
        report = Report(path, "pptx")
        report.add("FAIL", "wrong-extension", "内容是压缩包（可能是 PPTX），却使用 HTML 扩展名")
        return report
    report = check_html(path, raw, expected, patterns, allowed)
    if not looks_html and b"<html" not in raw[:65536].lower():
        report.add("FAIL", "not-html", "文件内容不是 HTML 文档")
    return report


def _brief(report: Report) -> str:
    pages = report.pages if report.pages is not None else "?"
    line = (
        f"verify_deck: {report.status} {report.kind} pages={pages} "
        f"fail={report.count('FAIL')} warn={report.count('WARN')}"
    )
    if report.kind == "pptx":
        line += (
            f" orphans={report.extra.get('orphanSlides', 0)}"
            f" notes={report.extra.get('notesPages', 0)}"
        )
    first = next((item for item in report.findings if item["level"] == "FAIL"), None)
    if first:
        where = f"P{first['page']} " if first["page"] else ""
        line += f"; first: {where}{first['message']}"
    return line + "; 视觉检查未覆盖"


def _print_human(report: Report) -> None:
    pages = report.pages if report.pages is not None else "未识别"
    print(f"{report.path}\n类型: {report.kind}  可见页数: {pages}")
    if report.kind == "pptx":
        print(
            f"未显示的幻灯片部件: {report.extra.get('orphanSlides', 0)}  "
            f"演讲备注页: {report.extra.get('notesPages', 0)}"
        )
    for item in report.findings:
        where = f"P{item['page']} " if item["page"] else ""
        print(f"  {item['level']}: {where}{item['message']}")
    print(f"结论: {report.status}（FAIL {report.count('FAIL')} / WARN {report.count('WARN')}）")
    print("本检查不能替代逐页视觉检查。")


def main(argv: Optional[Sequence[str]] = None) -> int:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Read-only structural check of a finished deck.")
    parser.add_argument("file", help="成品 .pptx / .html 路径")
    parser.add_argument("--expected-pages", type=int, default=None, help="确认稿页数；不符时 FAIL。")
    parser.add_argument("--pattern", action="append", default=[], help="追加占位词（正则），可重复。")
    parser.add_argument("--allow", action="append", default=[], help="命中此正则的文本不算占位，可重复。")
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    parser.add_argument("--brief", action="store_true", help="输出一行摘要。")
    args = parser.parse_args(argv)

    path = Path(args.file).expanduser()
    if not path.is_file():
        print(f"verify_deck: 文件不存在：{path}", file=sys.stderr)
        return 2
    try:
        report = verify(path, args.expected_pages, args.pattern, args.allow)
    except (OSError, ValueError, re.error, ElementTree.ParseError) as exc:
        print(f"verify_deck: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    elif args.brief:
        print(_brief(report))
    else:
        _print_human(report)
    return 1 if report.status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
