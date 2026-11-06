#!/usr/bin/env python3
"""Read-only doctor for ppt-planner-maker.

Runs dependency resolution and runtime checks in one command and prints a
user-facing summary.  It never installs anything and never writes into the
skill package.  Use the two underlying scripts when you need the full JSON.

Examples::

    python scripts/doctor.py --workspace . --branches A,F
    python scripts/doctor.py --branches A,B,C,D,E,F --brief
    python scripts/doctor.py --branches B --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_runtime import check as runtime_check  # noqa: E402
from resolve_skills import (  # noqa: E402
    DEFAULT_DEPS_FILE,
    HOST_SCANNED_SOURCES,
    VALID_BRANCHES,
    _split_list,
    _split_paths,
    _utf8_stdout,
    build_roots,
    load_deps,
    private_skills_root,
    resolve,
    select_skills,
)


def _drift_text(drift: Dict[str, Any]) -> str:
    if drift.get("state") == "match":
        return f"与已测版本一致（{drift.get('tested')}）"
    if drift.get("state") == "drift":
        return (
            f"已装 {drift.get('installed')}，已测 {drift.get('tested')}；"
            "只提示不阻塞，行为可能与路由说明不同"
        )
    return "未知（无法读取已装版本的提交号）"


def _next_step(
    hint: Optional[str], item: Optional[Dict[str, Any]] = None, skills_root: str = ""
) -> str:
    if not hint:
        return "按 references/dependencies.md 的解析顺序检查安装位置"
    if skills_root:
        hint = hint.replace("<skills-dir>", skills_root)
    if item and item.get("root"):
        root = Path(item["root"])
        hint = hint.replace(
            f"<{item['id']}>/requirements.txt",
            str(root / "requirements.txt"),
        )
        hint = hint.replace(f"<{item['id']}>", str(root))
    return hint


def _summary(result: Dict[str, Any]) -> str:
    branches = ",".join(result["branches"]) if result["branches"] else "all"
    total = len(result["skills"])
    ready = 0
    details: List[str] = []
    for skill_id, item in result["skills"].items():
        runtime = result["runtime"]["checks"].get(skill_id, {})
        path_ok = item["status"] == "ok"
        runtime_ok = runtime.get("status") == "ok"
        if path_ok and runtime_ok:
            ready += 1
            details.append(f"{skill_id}=ok")
        else:
            # Keep import names (for example pathops) in user-facing output;
            # setup.py owns the import-name to PyPI-name mapping.
            missing = list(item.get("missingRequired") or [])
            missing += [
                name
                for name in (runtime.get("missingRequired") or [])
                + (runtime.get("missingCommands") or [])
                if name not in missing
            ]
            state = "missing" if not path_ok and item["status"] == "missing" else "incomplete"
            if missing:
                state += "(" + ",".join(missing) + ")"
            details.append(f"{skill_id}={state}")
    line = f"doctor: branches={branches}; " + "; ".join(details)
    line += f"; ready={ready}/{total}"
    drifted = [
        f"{skill_id}({item['drift'].get('installed')}→{item['drift'].get('tested')})"
        for skill_id, item in result["skills"].items()
        if (item.get("drift") or {}).get("state") == "drift"
    ]
    if drifted:
        line += "; drift=" + ",".join(drifted)
    if result["warnings"]:
        line += "; warnings=" + " | ".join(result["warnings"])
    return line


def _print_human(result: Dict[str, Any]) -> None:
    print(f"workspace: {result['workspace']}")
    print(f"branches: {','.join(result['branches']) if result['branches'] else 'all'}")
    skills_root = str(private_skills_root())
    for skill_id, item in result["skills"].items():
        runtime = result["runtime"]["checks"].get(skill_id, {})
        needs_setup = bool(item.get("root")) and (item.get("drift") or {}).get("state") != "match"
        print(f"\n{skill_id}")
        if item["status"] == "ok":
            version = f"  version {item['version']}" if item.get("version") else ""
            print(f"  路径: OK  {item['root']}{version}")
            print(f"  版本: {_drift_text(item.get('drift') or {})}")
            if item.get("resolvedFrom") in HOST_SCANNED_SOURCES:
                print(
                    "  提示: 装在宿主扫描目录，宿主可能绕过编排层直接调用；"
                    f"可改装到 {skills_root}"
                )
        else:
            print(f"  路径: {item['status'].upper()}")
            missing = item.get("missingRequired") or []
            if missing:
                print(f"        missing required: {', '.join(missing)}")
            if item.get("skillFile"):
                print(f"        skill file: {item['skillFile']}")
            if not needs_setup:
                print(f"  下一步: {_next_step(item.get('install'), item, skills_root)}")

        if needs_setup:
            setup = Path(__file__).resolve().with_name("setup.py")
            branch_args = f' --branches {",".join(result["branches"])}' if result["branches"] else ""
            print(f'  下一步: python "{setup}" --workspace "{result["workspace"]}"{branch_args} --skills-dir "{skills_root}" （先看计划，再加 --yes；已有目标冲突需手动处理）')

        missing_python = runtime.get("missingRequired") or []
        missing_commands = runtime.get("missingCommands") or []
        if runtime.get("status") == "ok":
            print("  运行时: OK")
        elif runtime:
            print("  运行时: INCOMPLETE")
            if missing_python:
                print(f"        missing packages: {', '.join(missing_python)}")
            if missing_commands:
                print(f"        missing commands: {', '.join(missing_commands)}")
            if (missing_python or missing_commands) and not needs_setup:
                print(
                    "  下一步: "
                    + _next_step(runtime.get("install"), item, skills_root)
                )
        else:
            print("  运行时: 未检查")

        optional = runtime.get("missingOptional") or []
        if optional:
            print(f"  可选未安装: {', '.join(optional)}")
        if runtime.get("anyCommands"):
            any_ok = runtime.get("anyCommandsOk") or []
            if any_ok:
                first = any_ok[0]
                info = runtime.get("commands", {}).get(first, {})
                print(f"  浏览器(视觉检查): {first}: {info.get('path', '')}")
            else:
                print(
                    "  浏览器(视觉检查): 未找到 "
                    f"{', '.join(runtime['anyCommands'])}；HTML 交付前需要浏览器逐页确认"
                )
        for other in item.get("shadowed", []):
            location = other.get("root") or other.get("skillFile") or ""
            print(f"  已忽略同名副本: {other.get('source', '')} {location}".rstrip())

    if result["warnings"]:
        print("\nwarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    ready = sum(
        1
        for skill_id, item in result["skills"].items()
        if item["status"] == "ok"
        and result["runtime"]["checks"].get(skill_id, {}).get("status") == "ok"
    )
    total = len(result["skills"])
    if ready == total:
        print(f"\n结论: 所选分支已就绪（{ready}/{total}）。")
    else:
        print(f"\n结论: 未就绪（{ready}/{total}）。先完成上面的“下一步”，再重跑本命令。")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-command read-only readiness check for ppt-planner-maker."
    )
    parser.add_argument("--workspace", default=None, help="目标工作区；默认取当前目录。")
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
        help="只检查这些分支，例如 A,F；默认全部。",
    )
    parser.add_argument(
        "--company-template-file",
        action="store_true",
        help="用户自带公司 .pptx/.potx 模板文件；分支 A 不要求预装 deck。",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    parser.add_argument("--brief", action="store_true", help="输出一行摘要。")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _utf8_stdout()
    args = parse_args(argv)

    try:
        branches = [branch.upper() for branch in _split_list(args.branches)]
        invalid = [branch for branch in branches if branch not in VALID_BRANCHES]
        if invalid:
            raise ValueError(f"非法分支：{', '.join(invalid)}（只接受 A-F）")

        workspace = Path(
            args.workspace
            or os.environ.get("PPT_PLANNER_WORKSPACE")
            or os.getcwd()
        ).expanduser().resolve()
        dsh_home = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))
        agents_home = Path(
            os.environ.get("DSH_AGENTS_HOME") or (Path.home() / ".agents")
        )
        zcode_home = Path(os.environ.get("ZCODE_HOME") or (Path.home() / ".zcode"))

        explicit_values = list(args.skills_dir)
        env_dirs = os.environ.get("PPT_PLANNER_SKILLS_DIR")
        if env_dirs:
            explicit_values.append(env_dirs)
        explicit = _split_paths(explicit_values)

        deps = load_deps(Path(args.deps_file).expanduser())
        selected = select_skills(deps, [], branches)
        if not selected:
            raise ValueError("没有匹配的依赖；请检查 --branches。")

        roots = build_roots(workspace, explicit, dsh_home, agents_home, zcode_home)
        resolved = resolve(
            deps, selected, roots, workspace, branches, args.company_template_file
        )
        runtime = runtime_check(deps, selected, branches)
        result = dict(resolved)
        result["runtime"] = runtime
    except (OSError, ValueError) as exc:
        print(f"doctor: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.brief:
        print(_summary(result))
    else:
        _print_human(result)

    ready = sum(
        1
        for skill_id, item in result["skills"].items()
        if item["status"] == "ok"
        and result["runtime"]["checks"].get(skill_id, {}).get("status") == "ok"
    )
    return 0 if ready == len(result["skills"]) else 1


if __name__ == "__main__":
    sys.exit(main())
