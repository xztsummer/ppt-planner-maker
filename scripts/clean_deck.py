#!/usr/bin/env python
"""Remove unreachable OPC parts, preserving retained payload bytes unless metadata needs repair."""
from __future__ import annotations
import argparse
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True


def reachable_parts(archive, replacements=None):
    names = set(archive.namelist())
    reached = set()
    pending = [""]
    while pending:
        part = pending.pop()
        if part in reached:
            continue
        if part:
            if part not in names:
                raise ValueError(f"关系目标缺失：{part}")
            reached.add(part)
        directory, name = posixpath.split(part)
        rel = f"{directory + '/' if directory else ''}_rels/{name}.rels" if part else "_rels/.rels"
        if rel not in names:
            if not part:
                raise ValueError("缺少包根 _rels/.rels")
            continue
        reached.add(rel)
        for node in ET.fromstring((replacements or {}).get(rel, archive.read(rel))):
            if node.get("TargetMode") == "External":
                continue
            target = unquote(node.get("Target", "").split("#")[0])
            target = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join(directory, target))
            pending.append(target)
    reached.add("[Content_Types].xml")
    return reached


def clean(source: Path, out: Path):
    if source.resolve() == out.resolve() or (out.exists() and source.samefile(out)):
        raise ValueError("拒绝覆盖输入文件")
    with zipfile.ZipFile(source) as archive:
        presentation = archive.read("ppt/presentation.xml")
        root = ET.fromstring(presentation)
        ns = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
        rel_id = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        active_rels = {n.get(rel_id) for n in root.findall(f"{ns}sldIdLst/{ns}sldId")}
        changed = {}
        presentation_rels = "ppt/_rels/presentation.xml.rels"
        # A removed playlist entry can still have a stale slide relationship.
        # Synchronize this relationship file before computing reachability.
        if presentation_rels in archive.namelist():
            rels = archive.read(presentation_rels)
            def filter_relation(match):
                tag = match.group()
                typ = re.search(rb'\bType=["\x27]([^"\x27]+)', tag)
                ident = re.search(rb'\bId=["\x27]([^"\x27]+)', tag)
                if typ and typ.group(1).endswith(b'/slide') and ident and ident.group(1).decode() not in active_rels:
                    return b''
                return tag
            fixed_rels = re.sub(rb'<(?:\w+:)?Relationship\b[^>]*/>', filter_relation, rels)
            if fixed_rels != rels:
                changed[presentation_rels] = fixed_rels
        retained = reachable_parts(archive, changed)
        removed = sorted(n for n in archive.namelist() if n not in retained and not n.endswith("/"))
        ct = archive.read("[Content_Types].xml")
        def keep_override(match):
            node = ET.fromstring(match.group())
            return b"" if unquote(node.get("PartName", "").lstrip("/")) in removed else match.group()
        ct = re.sub(rb'<(?:\w+:)?Override\b[^>]*/>', keep_override, ct)
        changed["[Content_Types].xml"] = ct
        presentation = archive.read("ppt/presentation.xml")
        root = ET.fromstring(presentation)
        ns = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
        ids = {n.get("id") for n in root.findall(f"{ns}sldIdLst/{ns}sldId")}
        # Section slide IDs are numeric; remove only stale references, without reserializing XML.
        # Match IDs directly to avoid namespace dependencies in isolated XML fragments.
        def filter_section(match):
            def one(m):
                ident = re.search(rb'\bid=["\x27]([^"\x27]+)', m.group())
                return m.group() if ident and ident.group(1).decode() in ids else b''
            return re.sub(rb'<(?:\w+:)?sldId\b[^>]*/>', one, match.group())
        fixed = re.sub(rb'<(?:\w+:)?sectionLst\b.*?</(?:\w+:)?sectionLst>', filter_section, presentation, flags=re.S)
        if fixed != presentation:
            changed["ppt/presentation.xml"] = fixed
        if "docProps/app.xml" in retained:
            app = archive.read("docProps/app.xml")
            count = len(ids)
            # Optional cached title lists can contain removed titles. Drop both paired caches.
            if removed:
                app = re.sub(rb'<(?:\w+:)?(?:HeadingPairs|TitlesOfParts)\b[^>]*>.*?</(?:\w+:)?(?:HeadingPairs|TitlesOfParts)>', b'', app, flags=re.S)
            app = re.sub(rb'(<(?:\w+:)?Slides>)\d+(</(?:\w+:)?Slides>)', lambda m: m[1] + str(count).encode() + m[2], app)
            app = re.sub(rb'(<(?:\w+:)?Notes>)\d+(</(?:\w+:)?Notes>)', lambda m: m[1] + str(sum(bool(re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', n)) for n in retained)).encode() + m[2], app)
            if app != archive.read("docProps/app.xml"):
                changed["docProps/app.xml"] = app
        with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as dest:
            for info in archive.infolist():
                if info.filename in retained:
                    dest.writestr(info, changed.get(info.filename, archive.read(info.filename)))
    return {"input": str(source), "output": str(out), "removed": removed, "changed": sorted(k for k, v in changed.items() if k != "[Content_Types].xml" or removed), "beforeBytes": source.stat().st_size, "afterBytes": out.stat().st_size}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--brief", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = clean(Path(args.file), Path(args.out))
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"clean_deck: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"clean_deck: removed={len(result['removed'])}; {result['beforeBytes']} -> {result['afterBytes']} bytes")
        if not args.brief:
            print("\n".join(result["removed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
