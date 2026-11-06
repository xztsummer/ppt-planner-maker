#!/usr/bin/env python3
"""Static checks for the ppt-planner-maker skill package.

Checks frontmatter, relative links, forbidden hardcoded paths, routing-table
consistency across SKILL.md / production.md / README / deps.json, required
files, version/changelog, and the local eval branch labels.

Exit code: 0 when there are no errors; 1 when any error (or any warning under
``--strict``) is found.  Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

# Keep the skill package free of __pycache__ when this checker imports the resolver.
sys.dont_write_bytecode = True

SKILL_NAME = "ppt-planner-maker"
ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"
REFERENCES = ROOT / "references"
DOCS = ROOT / "docs"
DEPS_FILE = ROOT / "scripts" / "deps.json"
VERSION_FILE = ROOT / "VERSION"
CHANGELOG = ROOT / "CHANGELOG.md"

BRANCHES = set("ABCDEF")

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "README.en.md",
    "AGENTS.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "CHANGELOG.md",
    "references/confirmation.md",
    "references/dependencies.md",
    "references/edit.md",
    "references/intake.md",
    "references/planning.md",
    "references/production.md",
    "scripts/deps.json",
    "scripts/resolve_skills.py",
    "scripts/check_runtime.py",
    "scripts/doctor.py",
    "scripts/setup.py",
    "scripts/verify_deck.py",
    "scripts/clean_deck.py",
    "scripts/check_skill.py",
    "docs/design.md",
    "docs/install.md",
    "docs/migration.md",
]

BANNED_DEPENDENCY_PATHS = [
    "{工作区}/skills",
    "skills/ppt-master",
    "skills/gorden-ppt-skill",
    "skills/html-ppt",
    "skills/guizang-ppt-skill",
]
STALE_TERMS = [
    "使用性质",
    "内容偏好",
    "必须使用公司模板",
    "只有一套就直接用",
    "只是视觉密度，不决定分支",
    "视觉密度只影响版式，不参与分支判断",
    "视觉密度只影响版式，不改变分支",
    "不以其原创模式承接本分支",
    "不确定就选从零设计",
]
OLD_BRAND = "ppt-agent-kit"
OLD_BRAND_EXEMPT = {"CHANGELOG.md", "migration.md"}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
BRANCH_ROW_RE = re.compile(r"^\|\s*([A-F])\s*\|")
WINDOWS_ABS_RE = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|/Users/|/home/)")
PLACEHOLDER_RE = re.compile(r"\{skill:([a-z0-9][a-z0-9-]*)\}")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def markdown_files() -> List[Path]:
    files = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "README.en.md",
             ROOT / "AGENTS.md", ROOT / "THIRD_PARTY_NOTICES.md", ROOT / "CHANGELOG.md"]
    files += sorted(REFERENCES.glob("*.md"))
    files += sorted(DOCS.glob("*.md"))
    return [path for path in files if path.is_file()]


def strip_fenced_code(text: str) -> str:
    lines: List[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            lines.append(line)
    return "\n".join(lines)


def parse_frontmatter(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}
    data: Dict[str, str] = {}
    index = 1
    while index < end:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in (">-", ">", "|", "|-"):
            block: List[str] = []
            index += 1
            while index < end and (lines[index].startswith((" ", "\t")) or not lines[index].strip()):
                block.append(lines[index].strip())
                index += 1
            value = " ".join(item for item in block if item) if value.startswith(">") else "\n".join(block).strip()
        data[key] = value
        index += 1
    return data


def table_cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def branch_table(text: str, dep_ids: Set[str]) -> Dict[str, Set[str]]:
    mapping: Dict[str, Set[str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = table_cells(stripped)
        if not cells or cells[0] not in BRANCHES or len(cells) < 3:
            continue
        ids = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", " ".join(cells[1:]))) & dep_ids
        if ids:
            mapping.setdefault(cells[0], set()).update(ids)
    return mapping


def production_table(text: str, dep_ids: Set[str]) -> Dict[str, Set[str]]:
    mapping: Dict[str, Set[str]] = {}
    matches = list(re.finditer(r"(?m)^### ([A-F])\.", text))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[start:end]
        skill_line = re.search(r"(?m)^- Skill：\s*(.+)$", section)
        if not skill_line:
            continue
        ids = set(PLACEHOLDER_RE.findall(skill_line.group(1))) & dep_ids
        if not ids:
            ids = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", skill_line.group(1))) & dep_ids
        mapping[match.group(1)] = ids
    return mapping


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def check_required_files(errors: List[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"缺少必需文件：{relative}")


def check_frontmatter(errors: List[str], warnings: List[str]) -> None:
    if not SKILL_MD.is_file():
        return
    text = read_text(SKILL_MD)
    frontmatter = parse_frontmatter(text)
    if not frontmatter:
        errors.append("SKILL.md 缺少合法 frontmatter（--- 包裹）")
        return
    name = frontmatter.get("name", "")
    if name != SKILL_NAME:
        errors.append(f"frontmatter.name 应为 {SKILL_NAME}，实际为 {name!r}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name or ""):
        errors.append(f"frontmatter.name 不是 kebab-case：{name!r}")
    description = frontmatter.get("description", "").strip()
    if not description:
        errors.append("frontmatter.description 不能为空")
    elif len(description) > 500:
        errors.append(f"frontmatter.description 超过 500 字符（当前 {len(description)}）")
    elif len(description) > 450:
        warnings.append(f"frontmatter.description 接近 500 字符上限（当前 {len(description)}）")


def check_links(errors: List[str]) -> None:
    for path in markdown_files():
        text = strip_fenced_code(read_text(path))
        for match in LINK_RE.finditer(text):
            destination = match.group(1).strip()
            if destination.startswith("<") and destination.endswith(">"):
                destination = destination[1:-1]
            destination = destination.split()[0] if destination.split() else ""
            if not destination:
                continue
            if destination.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                continue
            destination = destination.split("#", 1)[0]
            if not destination:
                continue
            target = (path.parent / destination).resolve()
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)} 链接目标不存在：{destination}")


def check_banned_patterns(errors: List[str]) -> None:
    files = [SKILL_MD] + sorted(REFERENCES.glob("*.md"))
    for path in files:
        if not path.is_file():
            continue
        text = read_text(path)
        relative = path.relative_to(ROOT)
        for term in BANNED_DEPENDENCY_PATHS:
            if term in text:
                errors.append(f"{relative} 残留写死的依赖路径：{term}")
        for term in STALE_TERMS:
            if term in text:
                errors.append(f"{relative} 残留陈旧口径：{term}")
        if path.name != "dependencies.md" and WINDOWS_ABS_RE.search(text):
            errors.append(f"{relative} 含 Windows/用户绝对路径")

    for path in markdown_files():
        if path.name in OLD_BRAND_EXEMPT or path.parent.name == "docs" and path.name == "migration.md":
            continue
        if OLD_BRAND in read_text(path):
            errors.append(f"{path.relative_to(ROOT)} 残留旧品牌：{OLD_BRAND}")
    license_file = ROOT / "LICENSE"
    if license_file.is_file() and OLD_BRAND in read_text(license_file):
        errors.append("LICENSE 残留旧品牌或旧仓库 URL")


def check_dependency_catalog(errors: List[str], warnings: List[str]) -> Tuple[Dict, Set[str]]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from resolve_skills import load_deps  # type: ignore

        deps = load_deps(DEPS_FILE)
    except Exception as exc:  # noqa: BLE001 - report a readable static-check error
        errors.append(f"无法加载 scripts/deps.json：{exc}")
        return {}, set()

    dep_ids = {skill["id"] for skill in deps["skills"]}
    if not dep_ids:
        errors.append("scripts/deps.json 没有依赖条目")
    dependencies_md = REFERENCES / "dependencies.md"
    if dependencies_md.is_file():
        text = read_text(dependencies_md)
        for dep_id in sorted(dep_ids):
            if f"`{dep_id}`" not in text:
                errors.append(f"references/dependencies.md 未列出依赖 {dep_id}")
    for skill in deps["skills"]:
        if not skill.get("source"):
            warnings.append(f"{skill['id']} 缺少 source")
        if not skill.get("license"):
            warnings.append(f"{skill['id']} 缺少 license")
        if not skill.get("testedVersion"):
            warnings.append(f"{skill['id']} 缺少 testedVersion")
        if not isinstance(skill.get("runtime"), dict):
            warnings.append(f"{skill['id']} 缺少 runtime 清单（check_runtime.py 无法检查）")
    return deps, dep_ids


def check_routing(
    errors: List[str],
    deps: Dict,
    dep_ids: Set[str],
) -> None:
    if not dep_ids:
        return
    skill_text = read_text(SKILL_MD)
    production_text = read_text(REFERENCES / "production.md")
    readme_zh = read_text(ROOT / "README.md")
    readme_en = read_text(ROOT / "README.en.md")

    skill_map = branch_table(skill_text, dep_ids)
    prod_map = production_table(production_text, dep_ids)
    zh_map = branch_table(readme_zh, dep_ids)
    en_map = branch_table(readme_en, dep_ids)

    deps_branch_map: Dict[str, str] = {}
    for skill in deps["skills"]:
        for branch in skill.get("branches", []):
            if branch in deps_branch_map and deps_branch_map[branch] != skill["id"]:
                errors.append(f"deps.json 分支 {branch} 对应多个依赖：{deps_branch_map[branch]} / {skill['id']}")
            deps_branch_map[branch] = skill["id"]

    for label, mapping in (
        ("SKILL.md", skill_map),
        ("production.md", prod_map),
        ("README.md", zh_map),
        ("README.en.md", en_map),
        ("deps.json", {branch: {dep_id} for branch, dep_id in deps_branch_map.items()}),
    ):
        missing = BRANCHES - set(mapping)
        if missing:
            errors.append(f"{label} 缺少分支：{', '.join(sorted(missing))}")
        unexpected = set(mapping) - BRANCHES
        if unexpected:
            errors.append(f"{label} 出现非法分支：{', '.join(sorted(unexpected))}")

    for branch in sorted(BRANCHES):
        expected = {deps_branch_map[branch]} if branch in deps_branch_map else None
        if not expected:
            continue
        for label, mapping in (("SKILL.md", skill_map), ("production.md", prod_map),
                               ("README.md", zh_map), ("README.en.md", en_map)):
            actual = mapping.get(branch, set())
            if actual != expected:
                errors.append(
                    f"{label} 分支 {branch} 的 Skill 应为 {sorted(expected)}，实际为 {sorted(actual)}"
                )

    for path in [SKILL_MD] + sorted(REFERENCES.glob("*.md")):
        text = read_text(path)
        for dep_id in PLACEHOLDER_RE.findall(text):
            if dep_id not in dep_ids:
                errors.append(f"{path.relative_to(ROOT)} 的 {{skill:{dep_id}}} 未在 deps.json 中定义")


def check_version(errors: List[str]) -> None:
    if not VERSION_FILE.is_file():
        return
    version = read_text(VERSION_FILE).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"VERSION 不是 semver：{version!r}")
        return
    if CHANGELOG.is_file() and version not in read_text(CHANGELOG):
        errors.append(f"CHANGELOG.md 未提到当前版本 {version}")


def check_structure(errors: List[str], warnings: List[str]) -> None:
    for dirname in ("projects", "output", "_build"):
        if (ROOT / dirname).exists():
            warnings.append(f"仓库内出现运行目录 {dirname}/；产物应写到目标工作区")

    for pycache in ROOT.rglob("__pycache__"):
        if ".git" in pycache.parts:
            continue
        warnings.append(
            f"仓库内出现字节码目录 {pycache.relative_to(ROOT)}；Skill 包应只读，"
            "请清理并在运行脚本时设置 sys.dont_write_bytecode 或使用 python -B"
        )

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            name for name in dirnames
            if name not in {".git", "evals", "projects", "output", "_build", "__pycache__", "node_modules"}
        ]
        if Path(dirpath) == ROOT:
            continue
        if "SKILL.md" in filenames:
            errors.append(f"发现嵌套 SKILL.md：{Path(dirpath).relative_to(ROOT)}/SKILL.md")


def check_evals(errors: List[str], warnings: List[str]) -> None:
    cases = ROOT / "evals" / "cases.md"
    if not cases.is_file():
        return
    text = read_text(cases)
    if "使用性质" in text:
        warnings.append("evals/cases.md 仍提到“使用性质”，请同步新口径")
    if "内容偏好" in text:
        warnings.append("evals/cases.md 仍提到“内容偏好”，请改为制作路线 / 视觉密度")
    if "必须使用公司模板" in text:
        warnings.append("evals/cases.md 仍提到“必须使用公司模板”，请改为制作路线")
    for match in re.finditer(r"(?m)^\|\s*分支\s*\|\s*M\s*\|\s*([A-Za-z])\s*\|", text):
        if match.group(1).upper() not in BRANCHES:
            errors.append(f"evals/cases.md 出现非法分支：{match.group(1)}")


def run_checks() -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    check_required_files(errors)
    check_frontmatter(errors, warnings)
    check_links(errors)
    check_banned_patterns(errors)
    deps, dep_ids = check_dependency_catalog(errors, warnings)
    check_routing(errors, deps, dep_ids)
    check_version(errors)
    check_structure(errors, warnings)
    check_evals(errors, warnings)
    return errors, warnings


def _utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main(argv: Sequence[str] | None = None) -> int:
    _utf8_stdout()
    parser = argparse.ArgumentParser(description="Static checks for ppt-planner-maker.")
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    parser.add_argument("--strict", action="store_true", help="警告也按失败处理。")
    args = parser.parse_args(argv)

    errors, warnings = run_checks()
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        print(f"check_skill: {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
