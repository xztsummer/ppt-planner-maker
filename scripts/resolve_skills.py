#!/usr/bin/env python3
"""Resolve the external production skills used by ppt-planner-maker.

The orchestrator never hardcodes a workspace ``skills/`` path.  This script
checks the documented roots, probes each dependency's capabilities, and emits
either a human-readable report or JSON.  It only reads the filesystem; nothing
is written unless ``--out`` is explicitly passed.

Examples::

    python scripts/resolve_skills.py --workspace . --branches A,F
    python scripts/resolve_skills.py --check --branches A,B,C,D,E,F
    python scripts/resolve_skills.py --workspace . --branches A --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SKILL_NAME = "ppt-planner-maker"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEPS_FILE = SKILL_ROOT / "scripts" / "deps.json"

VALID_BRANCHES = tuple("ABCDEF")


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _utf8_stdout() -> None:
    """Best-effort UTF-8 stdout/stderr so Chinese paths survive Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def _split_list(value: Optional[str]) -> List[str]:
    """Split a comma/Chinese-comma separated option value."""
    if not value:
        return []
    parts = re.split(r"[,，]", value)
    return [part.strip() for part in parts if part.strip()]


def _split_paths(values: Iterable[str]) -> List[Path]:
    """Split ``;``/``:``/newline separated path lists."""
    result: List[Path] = []
    for value in values:
        if not value:
            continue
        for part in value.replace("\n", os.pathsep).split(os.pathsep):
            part = part.strip().strip('"').strip("'")
            if part:
                result.append(Path(os.path.expandvars(os.path.expanduser(part))))
    return result


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _read_version(root: Path) -> Optional[str]:
    for name in ("VERSION", "VERSION.txt"):
        candidate = root / name
        if candidate.is_file():
            try:
                lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            if lines and lines[0].strip():
                return lines[0].strip()
    manifest = root / "manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            return None
        if isinstance(data, dict):
            version = data.get("version")
            if version:
                return str(version)
    return None


# ---------------------------------------------------------------------------
# dependency manifest
# ---------------------------------------------------------------------------


def load_deps(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"无法读取依赖清单 {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"依赖清单不是合法 JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"依赖清单顶层必须是对象: {path}")
    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ValueError(f"依赖清单缺少非空 skills 数组: {path}")
    seen = set()
    for skill in skills:
        if not isinstance(skill, dict):
            raise ValueError("skills 中的每一项必须是对象")
        skill_id = skill.get("id")
        if not isinstance(skill_id, str) or not skill_id:
            raise ValueError("每个依赖都需要字符串 id")
        if skill_id in seen:
            raise ValueError(f"重复的依赖 id: {skill_id}")
        seen.add(skill_id)
        branches = skill.get("branches")
        if not isinstance(branches, list) or any(b not in VALID_BRANCHES for b in branches):
            raise ValueError(f"{skill_id}: branches 必须是 A-F 的子集")
        capabilities = skill.get("capabilities")
        if not isinstance(capabilities, dict) or not capabilities:
            raise ValueError(f"{skill_id}: capabilities 不能为空")
        for cap_id, cap in capabilities.items():
            if not isinstance(cap, dict) or not isinstance(cap.get("path"), str):
                raise ValueError(f"{skill_id}: capability {cap_id} 缺少字符串 path")
            for branch in cap.get("for", []):
                if branch not in VALID_BRANCHES:
                    raise ValueError(f"{skill_id}: capability {cap_id} 的 for 含非法分支 {branch}")
    return data


def select_skills(
    deps: Dict[str, Any],
    only: Sequence[str],
    branches: Sequence[str],
) -> List[Dict[str, Any]]:
    skills = list(deps["skills"])
    known = {skill["id"] for skill in skills}
    if only:
        unknown = [skill_id for skill_id in only if skill_id not in known]
        if unknown:
            raise ValueError(f"未知依赖 id: {', '.join(unknown)}")
        skills = [skill for skill in skills if skill["id"] in only]
    if branches:
        wanted = set(branches)
        skills = [skill for skill in skills if wanted & set(skill.get("branches", []))]
    return skills


# ---------------------------------------------------------------------------
# roots and resolution
# ---------------------------------------------------------------------------


def build_roots(
    workspace: Path,
    explicit: Sequence[Path],
    dsh_home: Path,
    agents_home: Path,
) -> List[Dict[str, Any]]:
    raw: List[Tuple[str, Path]] = []
    for path in explicit:
        raw.append(("explicit", path))
    raw.extend(
        [
            ("project-dsh", workspace / ".dsh" / "skills"),
            ("project-agents", workspace / ".agents" / "skills"),
            ("legacy-workspace", workspace / "skills"),
            ("user-dsh", dsh_home / "skills"),
            ("user-agents", agents_home / "skills"),
            ("claude-user", Path.home() / ".claude" / "skills"),
        ]
    )

    roots: List[Dict[str, Any]] = []
    seen = set()
    for source, raw_path in raw:
        try:
            path = raw_path.expanduser().resolve()
        except OSError:
            path = raw_path.absolute()
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        roots.append(
            {
                "rank": len(roots) + 1,
                "source": source,
                "path": str(path),
                "exists": path.is_dir(),
            }
        )
    return roots


def _install_hint(skill: Dict[str, Any]) -> Optional[str]:
    install = skill.get("install")
    if not isinstance(install, dict):
        return None
    if install.get("type") == "git":
        target = install.get("targetName") or skill["id"]
        return f"git clone {install.get('url', '<repo-url>')} <skills-dir>/{target}"
    return None


def _probe_capabilities(
    skill: Dict[str, Any],
    root: Path,
    active_branches: Iterable[str],
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    branches = set(active_branches)
    capabilities: Dict[str, Dict[str, Any]] = {}
    missing_required: List[str] = []
    for cap_id, cap in skill["capabilities"].items():
        relative = cap["path"]
        target = root / relative
        status = "ok" if target.exists() else "missing"
        required = bool(cap.get("required", False))
        if not required and set(cap.get("for", [])) & branches:
            required = True
        capabilities[cap_id] = {
            "path": str(target),
            "relativePath": relative,
            "status": status,
            "required": required,
        }
        if required and status != "ok":
            missing_required.append(cap_id)
    return capabilities, missing_required


def resolve_skill(
    skill: Dict[str, Any],
    roots: Sequence[Dict[str, Any]],
    branches: Sequence[str],
) -> Dict[str, Any]:
    skill_id = skill["id"]
    candidates: List[Dict[str, Any]] = []
    for root in roots:
        base = Path(root["path"])
        if not base.is_dir():
            continue
        bundle = base / skill_id
        if (bundle / "SKILL.md").is_file():
            candidates.append(
                {
                    "kind": "bundle",
                    "root": str(bundle),
                    "skillFile": str(bundle / "SKILL.md"),
                    "source": root["source"],
                    "base": str(base),
                }
            )
            continue
        flat = base / f"{skill_id}.md"
        if flat.is_file():
            candidates.append(
                {
                    "kind": "flat",
                    "root": None,
                    "skillFile": str(flat),
                    "source": root["source"],
                    "base": str(base),
                }
            )

    active_branches = set(branches) if branches else set(skill.get("branches", []))
    base_result: Dict[str, Any] = {
        "id": skill_id,
        "title": skill.get("title", ""),
        "source": skill.get("source", ""),
        "license": skill.get("license", ""),
        "branches": list(skill.get("branches", [])),
        "testedVersion": skill.get("testedVersion", ""),
        "install": _install_hint(skill),
        "status": "missing",
        "root": None,
        "skillFile": None,
        "resolvedFrom": None,
        "version": None,
        "shadowed": [],
        "capabilities": {},
        "missingRequired": [],
        "warnings": [],
    }

    if not candidates:
        return base_result

    chosen = candidates[0]
    base_result["resolvedFrom"] = chosen["source"]
    base_result["shadowed"] = [
        {"root": other["root"], "skillFile": other["skillFile"], "source": other["source"]}
        for other in candidates[1:]
    ]

    if chosen["kind"] == "flat":
        base_result["status"] = "invalid"
        base_result["skillFile"] = chosen["skillFile"]
        base_result["warnings"].append(
            "只找到扁平 <id>.md，缺少资源目录；本编排 Skill 需要目录型依赖（<id>/SKILL.md）。"
        )
        return base_result

    root = Path(chosen["root"])
    base_result["root"] = str(root)
    base_result["skillFile"] = chosen["skillFile"]
    base_result["version"] = _read_version(root)
    capabilities, missing_required = _probe_capabilities(skill, root, active_branches)
    base_result["capabilities"] = capabilities
    base_result["missingRequired"] = missing_required
    base_result["status"] = "ok" if not missing_required else "incomplete"
    if base_result["shadowed"]:
        base_result["warnings"].append("同名依赖出现在多个根目录，已按优先级使用第一个。")
    return base_result


def resolve(
    deps: Dict[str, Any],
    selected: Sequence[Dict[str, Any]],
    roots: Sequence[Dict[str, Any]],
    workspace: Path,
    branches: Sequence[str],
) -> Dict[str, Any]:
    warnings: List[str] = []
    if not workspace.is_dir():
        warnings.append(f"工作区不存在或不是目录：{workspace}")
    if workspace.resolve() == SKILL_ROOT:
        warnings.append(
            "当前工作区就是 Skill 根目录；运行产物不能写入 Skill 包，请让用户指定工作区。"
        )
    elif _is_inside(workspace, SKILL_ROOT):
        warnings.append(
            "当前工作区位于 Skill 根目录内；运行产物不能写入 Skill 包，请确认目标工作区。"
        )
    if not any(root["exists"] for root in roots):
        warnings.append("所有候选 skills 根目录都不存在；请安装依赖或设置 PPT_PLANNER_SKILLS_DIR。")

    resolved: Dict[str, Dict[str, Any]] = {}
    for skill in selected:
        resolved[skill["id"]] = resolve_skill(skill, roots, branches)

    ok_count = sum(1 for item in resolved.values() if item["status"] == "ok")
    return {
        "schemaVersion": 1,
        "skillName": deps.get("skillName", SKILL_NAME),
        "skillRoot": str(SKILL_ROOT),
        "workspace": str(workspace.resolve()),
        "branches": list(branches),
        "searchedRoots": list(roots),
        "installRootHint": deps.get("installRootHint", ""),
        "skills": resolved,
        "summary": {
            "selected": len(resolved),
            "ok": ok_count,
            "notOk": len(resolved) - ok_count,
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------


def _print_human(result: Dict[str, Any]) -> None:
    print(f"workspace: {result['workspace']}")
    print(f"skill root: {result['skillRoot']}")
    print("roots:")
    for root in result["searchedRoots"]:
        suffix = "" if root["exists"] else "  (missing)"
        print(f"  {root['rank']:>2}. {root['source']:<16} {root['path']}{suffix}")

    branch_text = ",".join(result["branches"]) if result["branches"] else "all"
    print(f"\nskills (branches: {branch_text}):")
    for skill_id, item in result["skills"].items():
        root = item.get("root") or "-"
        print(
            f"  {skill_id:<20} {item['status'].upper():<11} "
            f"{','.join(item.get('branches', [])):<8} {root}"
        )
        if item.get("version"):
            print(f"      version: {item['version']}")
        if item["status"] != "ok":
            if item.get("missingRequired"):
                print(f"      missing required: {', '.join(item['missingRequired'])}")
            if item.get("skillFile"):
                print(f"      skill file: {item['skillFile']}")
            if item.get("install"):
                print(f"      install: {item['install']}")
        for warning in item.get("warnings", []):
            print(f"      warning: {warning}")

    if result["warnings"]:
        print("\nwarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve external production skills for ppt-planner-maker."
    )
    parser.add_argument(
        "--workspace",
        default=None,
        help="目标工作区；默认取 PPT_PLANNER_WORKSPACE 或当前目录。",
    )
    parser.add_argument(
        "--skills-dir",
        action="append",
        default=[],
        help="额外的 skills 根目录；可重复，优先级最高。",
    )
    parser.add_argument(
        "--deps-file",
        default=str(DEFAULT_DEPS_FILE),
        help="依赖清单路径；默认 scripts/deps.json。",
    )
    parser.add_argument(
        "--branches",
        default="",
        help="只解析这些分支的依赖，例如 A,F；默认全部。",
    )
    parser.add_argument(
        "--only",
        default="",
        help="只解析这些依赖 id，例如 ppt-master,html-ppt。",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    parser.add_argument(
        "--check",
        action="store_true",
        help="所选依赖不是 ok 时以退出码 1 结束。",
    )
    parser.add_argument("--out", default=None, help="把 JSON 结果写到指定文件。")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _utf8_stdout()
    args = parse_args(argv)

    try:
        branches = [b.upper() for b in _split_list(args.branches)]
        invalid = [b for b in branches if b not in VALID_BRANCHES]
        if invalid:
            raise ValueError(f"非法分支：{', '.join(invalid)}（只接受 A-F）")
        only = _split_list(args.only)

        workspace_raw = (
            args.workspace
            or os.environ.get("PPT_PLANNER_WORKSPACE")
            or os.getcwd()
        )
        workspace = Path(workspace_raw).expanduser().resolve()
        dsh_home = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))
        agents_home = Path(
            os.environ.get("DSH_AGENTS_HOME") or (Path.home() / ".agents")
        )

        explicit_values = list(args.skills_dir)
        env_dirs = os.environ.get("PPT_PLANNER_SKILLS_DIR")
        if env_dirs:
            explicit_values.append(env_dirs)
        explicit = _split_paths(explicit_values)

        deps = load_deps(Path(args.deps_file).expanduser())
        selected = select_skills(deps, only, branches)
        if not selected:
            raise ValueError("没有匹配的依赖；请检查 --branches 或 --only。")

        roots = build_roots(workspace, explicit, dsh_home, agents_home)
        result = resolve(deps, selected, roots, workspace, branches)
    except (OSError, ValueError) as exc:
        print(f"resolve_skills: {exc}", file=sys.stderr)
        return 2

    if args.out:
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human(result)

    if args.check:
        bad = [
            skill_id
            for skill_id, item in result["skills"].items()
            if item["status"] != "ok"
        ]
        if bad:
            print(
                f"resolve_skills: 依赖未就绪：{', '.join(bad)}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
