#!/usr/bin/env python3
"""Check runtime dependencies for the selected production branches.

``resolve_skills.py`` answers "is the skill installed and does it have the
expected files?"  This script answers "can the selected branch actually run?"
by probing importable Python modules and external commands.  It only reads the
manifest and the local environment: nothing is installed, nothing is written,
and only the Python standard library is used.

Examples::

    python scripts/check_runtime.py --branches A,B
    python scripts/check_runtime.py --check --branches B
    python scripts/check_runtime.py --branches C --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEPS_FILE = SKILL_ROOT / "scripts" / "deps.json"
VALID_BRANCHES = tuple("ABCDEF")

# LibreOffice is often installed outside PATH on Windows.
SOFFICE_COMMON_PATHS = [
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    Path(r"D:\Program Files\LibreOffice\program\soffice.exe"),
    Path("/usr/bin/soffice"),
    Path("/usr/local/bin/soffice"),
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
]

# Browsers used for HTML visual checks; at least one of anyCommands is enough.
BROWSER_COMMON_PATHS = {
    "msedge": [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path("/usr/bin/microsoft-edge"),
        Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    ],
    "chrome": [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"D:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ],
    "firefox": [
        Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
        Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
        Path("/usr/bin/firefox"),
        Path("/Applications/Firefox.app/Contents/MacOS/firefox"),
    ],
}

COMMON_COMMAND_PATHS = {"soffice": SOFFICE_COMMON_PATHS, **BROWSER_COMMON_PATHS}

# The skill package is read-only.  Keep this import from writing __pycache__
# into scripts/ before we even reach the actual checks.
sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_skills import load_deps, select_skills  # noqa: E402

Finder = Callable[[str], Any]
Which = Callable[[str], Optional[str]]


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def _split_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace("，", ",").split(",") if part.strip()]


def default_finder(name: str) -> Any:
    """Return a truthy value only when the module actually imports.

    ``find_spec`` would report a package as present even when a native DLL is
    missing or its ``__init__`` raises.  That difference is exactly what makes
    a preflight useful, so import the module for real.
    """
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return None


def check_packages(
    names: Sequence[str], finder: Finder = default_finder
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for name in names:
        if name in result:
            continue
        result[name] = {"ok": finder(name) is not None}
    return result


def find_command(
    name: str,
    which: Which = shutil.which,
    common_paths: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    if common_paths is None:
        common_paths = COMMON_COMMAND_PATHS.get(name, [])
    found = which(name)
    if found:
        return {"ok": True, "path": str(found), "onPath": True}
    for candidate in common_paths:
        try:
            if Path(candidate).is_file():
                return {"ok": True, "path": str(candidate), "onPath": False}
        except OSError:
            continue
    return {"ok": False, "path": None, "onPath": False}


def evaluate_skill(
    skill: Dict[str, Any],
    finder: Finder = default_finder,
    which: Which = shutil.which,
    common_paths: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    runtime = skill.get("runtime") or {}
    # runtime.python contains import names, not PyPI distribution names
    # (for example: pathops is supplied by skia-pathops).
    required = list(runtime.get("python") or [])
    optional = list(runtime.get("optionalPython") or [])
    commands = list(runtime.get("commands") or [])
    optional_commands = list(runtime.get("optionalCommands") or [])
    any_commands = list(runtime.get("anyCommands") or [])

    packages = check_packages(required + optional, finder)
    command_results = {
        name: find_command(name, which=which, common_paths=common_paths)
        for name in commands + optional_commands + any_commands
    }

    missing_required = [name for name in required if not packages[name]["ok"]]
    missing_optional = [name for name in optional if not packages[name]["ok"]]
    missing_commands = [name for name in commands if not command_results[name]["ok"]]
    missing_optional_commands = [
        name for name in optional_commands if not command_results[name]["ok"]
    ]
    any_ok = [name for name in any_commands if command_results[name]["ok"]]
    missing_any_commands = any_commands if not any_ok else []
    status = "ok" if not missing_required and not missing_commands else "incomplete"

    return {
        "id": skill["id"],
        "branches": list(skill.get("branches", [])),
        "status": status,
        "python": packages,
        "commands": command_results,
        "missingRequired": missing_required,
        "missingOptional": missing_optional,
        "missingCommands": missing_commands,
        "missingOptionalCommands": missing_optional_commands,
        "anyCommands": any_commands,
        "anyCommandsOk": any_ok,
        "missingAnyCommands": missing_any_commands,
        "install": runtime.get("install", ""),
        "note": runtime.get("note", ""),
    }


def check(
    deps: Dict[str, Any],
    selected: Sequence[Dict[str, Any]],
    branches: Sequence[str],
) -> Dict[str, Any]:
    checks: Dict[str, Dict[str, Any]] = {}
    for skill in selected:
        checks[skill["id"]] = evaluate_skill(skill)
    ok_count = sum(1 for item in checks.values() if item["status"] == "ok")
    return {
        "schemaVersion": 1,
        "skillName": deps.get("skillName", "ppt-planner-maker"),
        "branches": list(branches),
        "checks": checks,
        "summary": {
            "selected": len(checks),
            "ok": ok_count,
            "notOk": len(checks) - ok_count,
        },
    }


def _print_human(result: Dict[str, Any]) -> None:
    branch_text = ",".join(result["branches"]) if result["branches"] else "all"
    print(f"branches: {branch_text}")
    for skill_id, item in result["checks"].items():
        print(f"  {skill_id:<20} {item['status'].upper():<11} {','.join(item['branches'])}")
        if item["missingRequired"]:
            print(f"      missing required: {', '.join(item['missingRequired'])}")
        if item["missingOptional"]:
            print(f"      optional missing: {', '.join(item['missingOptional'])}")
        if item.get("anyCommands"):
            if item.get("anyCommandsOk"):
                first = item["anyCommandsOk"][0]
                info = item["commands"][first]
                suffix = "" if info["onPath"] else "  (not on PATH)"
                print(f"      browser (visual check): {first}: {info['path']}{suffix}")
            else:
                print(
                    "      browser (visual check): none of "
                    f"{', '.join(item['anyCommands'])} found"
                )
        for name, info in item["commands"].items():
            if info["ok"]:
                suffix = "" if info["onPath"] else "  (not on PATH)"
                print(f"      command {name}: {info['path']}{suffix}")
            else:
                print(f"      command {name}: missing")
        if item["install"]:
            print(f"      install: {item['install']}")
        if item["note"]:
            print(f"      note: {item['note']}")


def _brief_line(result: Dict[str, Any]) -> str:
    branch_text = ",".join(result["branches"]) if result["branches"] else "all"
    parts: List[str] = []
    for skill_id, item in result["checks"].items():
        detail = item["status"]
        missing = list(item.get("missingRequired") or []) + list(
            item.get("missingCommands") or []
        )
        if missing:
            detail += "(" + ",".join(missing) + ")"
        if item.get("install") and item["status"] != "ok":
            detail += " install=" + item["install"]
        parts.append(f"{skill_id}={detail}")
    return f"{result['skillName']}: branches={branch_text}; " + "; ".join(parts)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check runtime dependencies for ppt-planner-maker branches."
    )
    parser.add_argument(
        "--branches",
        default="",
        help="只检查这些分支的依赖，例如 A,F；默认全部。",
    )
    parser.add_argument(
        "--only",
        default="",
        help="只检查这些依赖 id，例如 ppt-master,html-ppt。",
    )
    parser.add_argument(
        "--deps-file",
        default=str(DEFAULT_DEPS_FILE),
        help="依赖清单路径；默认 scripts/deps.json。",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    parser.add_argument(
        "--brief",
        action="store_true",
        help="输出一行摘要，适合直接给用户看；与 --json 同用时以 JSON 为准。",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="所选依赖运行时未就绪时以退出码 1 结束。",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _utf8_stdout()
    args = parse_args(argv)

    try:
        branches = [branch.upper() for branch in _split_list(args.branches)]
        invalid = [branch for branch in branches if branch not in VALID_BRANCHES]
        if invalid:
            raise ValueError(f"非法分支：{', '.join(invalid)}（只接受 A-F）")
        only = _split_list(args.only)
        deps = load_deps(Path(args.deps_file).expanduser())
        selected = select_skills(deps, only, branches)
        if not selected:
            raise ValueError("没有匹配的依赖；请检查 --branches 或 --only。")
        result = check(deps, selected, branches)
    except (OSError, ValueError) as exc:
        print(f"check_runtime: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.brief:
        print(_brief_line(result))
    else:
        _print_human(result)

    if args.check:
        bad = [
            skill_id
            for skill_id, item in result["checks"].items()
            if item["status"] != "ok"
        ]
        if bad:
            print(
                f"check_runtime: 运行时依赖未就绪：{', '.join(bad)}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
