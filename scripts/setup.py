#!/usr/bin/env python3
"""Opt-in installer for ppt-planner-maker dependencies.

Read-only by default: without ``--yes`` it only prints what it *would* do.
With ``--yes`` it clones missing dependencies with git and installs missing
Python packages with pip, into a private root (``~/.ppt-planner/skills``, or
``PPT_PLANNER_HOME``) that hosts do not scan, so only the orchestrator is
discoverable.  New clones are pinned to ``testedVersion`` unless ``--latest``.
System-level components (LibreOffice, browsers) are reported, never installed.

Examples::

    python scripts/setup.py --branches A,F              # plan only
    python scripts/setup.py --branches A,F --yes        # install at the tested commit
    python scripts/setup.py --branches B --yes --latest # install upstream HEAD instead
    python scripts/setup.py --branches A,F --json       # machine-readable plan
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_runtime import evaluate_skill  # noqa: E402
from resolve_skills import (  # noqa: E402
    DEFAULT_DEPS_FILE,
    SKILL_ROOT,
    VALID_BRANCHES,
    _split_list,
    _split_paths,
    _utf8_stdout,
    build_roots,
    load_deps,
    private_skills_root,
    resolve,
    resolve_skill,
    select_skills,
    tested_commit,
)

# import name -> PyPI name; anything not listed is used as-is.
IMPORT_TO_PIP = {
    "yaml": "PyYAML",
    "pptx": "python-pptx",
    "xlsxwriter": "XlsxWriter",
    "pathops": "skia-pathops",
    "uharfbuzz": "uharfbuzz",
    "edge_tts": "edge-tts",
    "fitz": "PyMuPDF",
}

# Targeted advice for packages known to lack wheels on very new Python versions.
PIP_FAILURE_HINTS = {
    "PyYAML": "PyYAML 无 wheel 时使用 PYYAML_FORCE_LIBYAML=0 纯 Python 构建；若仍失败，请检查构建日志或改用 Python 3.11/3.12。",
    "skia-pathops": (
        "skia-pathops 在过新的 Python 上可能缺少可用 wheel；"
        "建议改用带 wheel 的 Python 版本（如 3.11/3.12）后重跑本命令，"
        "或手动安装官方预编译 wheel。"
    ),
    "uharfbuzz": (
        "uharfbuzz 安装失败时，建议改用带 wheel 的 Python 版本（如 3.11/3.12），"
        "或手动安装官方预编译 wheel。"
    ),
}

def _pip_name(import_name: str) -> str:
    return IMPORT_TO_PIP.get(import_name, import_name)


def choose_target_root(
    explicit_dirs: Sequence[str],
    roots: Sequence[Dict[str, Any]],
) -> Path:
    """Pick where new dependencies go: explicit > private root hosts do not scan."""
    for value in explicit_dirs:
        for part in _split_paths([value]):
            return part
    return private_skills_root()


def _ensure_outside_skill(target: Path) -> Optional[str]:
    try:
        target.resolve().relative_to(SKILL_ROOT.resolve())
        return (
            f"安装目标 {target} 位于 Skill 包内；运行产物和依赖不能写入 Skill 包，"
            "请用 --skills-dir 指定其他目录。"
        )
    except (ValueError, OSError):
        return None


def _plan_for_skill(
    skill: Dict[str, Any],
    item: Dict[str, Any],
    target_root: Path,
    pin: bool,
) -> Dict[str, List[Dict[str, Any]]]:
    """Compute clone/pip/pin/manual actions for one dependency."""
    actions: Dict[str, List[Dict[str, Any]]] = {
        "clone": [],
        "pip": [],
        "pin": [],
        "manual": [],
    }
    skill_id = skill["id"]
    runtime = skill.get("runtime") or {}

    if item["status"] == "missing":
        install = skill.get("install") or {}
        if install.get("type") == "git" and install.get("url"):
            target = target_root / (install.get("targetName") or skill_id)
            actions["clone"].append(
                {
                    "id": skill_id,
                    "cmd": ["git", "clone", install["url"], str(target)],
                    "target": str(target),
                }
            )
            commit = tested_commit(skill.get("testedVersion", ""))
            if pin and commit:
                actions["pin"].append(
                    {
                        "id": skill_id,
                        "cmd": ["git", "-C", str(target), "checkout", commit],
                        "commit": commit,
                    }
                )
            runtime_root: Optional[Path] = target
        else:
            actions["manual"].append(
                {
                    "id": skill_id,
                    "reason": f"依赖 {skill_id} 缺失，且没有可自动执行的安装方式",
                }
            )
            runtime_root = None
    elif item["status"] == "invalid":
        actions["manual"].append(
            {
                "id": skill_id,
                "reason": (
                    "只找到扁平 <id>.md；请删除该文件或改为目录型安装 "
                    f"（{item.get('skillFile', '')}）"
                ),
            }
        )
        runtime_root = None
    elif item["status"] == "incomplete":
        missing = item.get("missingRequired") or []
        actions["manual"].append(
            {
                "id": skill_id,
                "reason": (
                    "依赖存在但缺少能力 "
                    f"{', '.join(missing)}；脚本无法代为补齐（如 deck 内容），需手动处理"
                ),
            }
        )
        runtime_root = Path(item["root"]) if item.get("root") else None
    else:
        runtime_root = Path(item["root"]) if item.get("root") else None

    if runtime_root is not None and runtime.get("python"):
        probe = evaluate_skill(skill)
        missing_packages = list(probe.get("missingRequired") or [])
        if missing_packages:
            requirements = runtime_root / "requirements.txt"
            if requirements.is_file() or actions["clone"]:
                actions["pip"].append(
                    {
                        "id": skill_id,
                        "cmd": [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-r",
                            str(requirements),
                        ],
                        "packages": missing_packages,
                        "runtimeRoot": str(runtime_root),
                    }
                )
            else:
                for name in missing_packages:
                    actions["pip"].append(
                        {
                            "id": skill_id,
                            "cmd": [
                                sys.executable,
                                "-m",
                                "pip",
                                "install",
                                _pip_name(name),
                            ],
                            "packages": [name],
                        }
                    )
    return actions


def _version_description(skill: Dict[str, Any], item: Dict[str, Any]) -> str:
    drift = item.get("drift") or {}
    installed = item.get("version") or drift.get("installed")
    tested = skill.get("testedRelease") or drift.get("tested")
    installed_text = f"已装 {installed}" if installed and drift.get("state") != "unknown" else "版本未知"
    return installed_text + (f"，已测 {tested}" if tested else "")


def build_plan_for_run(
    deps: Dict[str, Any],
    selected: Sequence[Dict[str, Any]],
    roots: Sequence[Dict[str, Any]],
    workspace: Path,
    branches: Sequence[str],
    target_root: Path,
    pin: bool,
    company_template_file: bool = False,
    explicit_target: bool = False,
) -> Dict[str, Any]:
    result = resolve(
        deps, selected, roots, workspace, list(branches), company_template_file
    )
    plan: Dict[str, Any] = {
        "workspace": result["workspace"],
        "warnings": result["warnings"],
        "targetRoot": str(target_root),
        "clone": [],
        "pip": [],
        "pin": [],
        "manual": [],
        "ready": [],
    }
    for skill in selected:
        item = result["skills"][skill["id"]]
        target_roots = [{"path": str(target_root), "source": "explicit", "exists": target_root.is_dir(), "rank": 1}]
        target_item = resolve_skill(skill, target_roots, branches, company_template_file)
        explicit_target = explicit_target or any(r["source"] == "explicit" and Path(r["path"]).resolve() == target_root.resolve() for r in roots)
        old = item
        if explicit_target:
            item = target_item
            if old.get("root") and old.get("root") != item.get("root"):
                plan["warnings"].append(f"{skill['id']}: 其他位置副本 {old['root']} 不计入目标就绪状态")
        elif item.get("drift", {}).get("state") != "match":
            if item.get("root"):
                plan["warnings"].append(f"{skill['id']}: 旧副本 {item['root']}，{_version_description(skill, item)}；将安装到 {target_root}")
            item = target_item
        target_path = target_root / ((skill.get("install") or {}).get("targetName") or skill["id"])
        if target_path.exists() and target_item.get("drift", {}).get("state") != "match":
            plan["manual"].append({"id": skill["id"], "reason": f"目标 {target_path} 已存在但版本不一致或未知：{_version_description(skill, target_item)}；不覆盖、不自动切换，请手动处理"})
            continue
        if not explicit_target and old.get("root") and old.get("root") != item.get("root") and Path(old["root"]).parent.resolve() != target_root.resolve():
            for root in roots:
                if Path(root["path"]).resolve() == target_root.resolve():
                    break
                if Path(root["path"]).resolve() == Path(old["root"]).parent.resolve():
                    plan["warnings"].append(f"{skill['id']}: 更高优先级根目录 {root['path']} 仍会抢占新装副本；请手动处理旧副本或显式传 --skills-dir {target_root}")
                    break
        if item["status"] == "ok":
            plan["ready"].append(skill["id"])
        actions = _plan_for_skill(skill, item, target_root, pin)
        for key in ("clone", "pip", "pin", "manual"):
            plan[key].extend(actions[key])
    return plan


def _print_plan(plan: Dict[str, Any], execute: bool) -> None:
    print(f"workspace: {plan['workspace']}")
    print(f"安装目标: {plan['targetRoot']}")
    if plan["warnings"]:
        for warning in plan["warnings"]:
            print(f"  warning: {warning}")

    if plan["ready"]:
        print("\n已就绪: " + ", ".join(plan["ready"]))

    if plan["clone"]:
        print("\n将克隆:")
        for action in plan["clone"]:
            print(f"  [{action['id']}] {' '.join(action['cmd'])}")
    if plan["pip"]:
        print("\n将安装 Python 包:")
        for action in plan["pip"]:
            print(f"  [{action['id']}] {' '.join(action['cmd'])}")
    if plan["pin"]:
        print("\n将锁定版本（--latest 可跳过）:")
        for action in plan["pin"]:
            print(f"  [{action['id']}] checkout {action['commit']}")
    if plan["manual"]:
        print("\n需要手动处理:")
        for action in plan["manual"]:
            print(f"  [{action['id']}] {action['reason']}")

    if not any(plan[key] for key in ("clone", "pip", "pin", "manual")):
        print("\n没有需要安装的内容。")
        return

    if not execute:
        print("\n以上是计划（未执行）。确认无误后加 --yes 运行。")
    else:
        print("\n开始执行…")


def _pip_failure_hint(cmd: Sequence[str], packages: Sequence[str] = ()) -> Optional[str]:
    if "-r" in cmd:
        return " ".join(PIP_FAILURE_HINTS.values())
    for arg in list(cmd) + [_pip_name(p) for p in packages]:
        if arg in PIP_FAILURE_HINTS:
            return PIP_FAILURE_HINTS[arg]
    return None


def _run_actions(plan: Dict[str, Any]) -> bool:
    ok = not plan.get("manual")
    failed_clones = set()
    for key in ("clone", "pin", "pip"):
        for action in plan[key]:
            if key in {"pin", "pip"} and action["id"] in failed_clones:
                print(f"\n跳过 [{action['id']}] {key}：克隆或锁定未成功。")
                continue
            cmd = action["cmd"]
            if key == "pip" and action.get("runtimeRoot"):
                req = Path(action["runtimeRoot"]) / "requirements.txt"
                if req.is_file():
                    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
                else:
                    cmd = [sys.executable, "-m", "pip", "install"] + [_pip_name(p) for p in action["packages"]]
            print(f"\n$ {' '.join(cmd)}")
            try:
                if key == "pip":
                    env = dict(os.environ, PYYAML_FORCE_LIBYAML="0")
                    completed = subprocess.run(cmd, env=env)
                else:
                    completed = subprocess.run(cmd)
            except OSError as exc:
                print(f"  执行失败: {exc}")
                ok = False
                if key in {"clone", "pin"}:
                    failed_clones.add(action["id"])
                continue
            if completed.returncode != 0:
                print(f"  退出码 {completed.returncode}，请查看上方输出。")
                hint = _pip_failure_hint(cmd, action.get("packages", [])) if key == "pip" else None
                if hint:
                    print(f"  提示: {hint}")
                ok = False
                if key in {"clone", "pin"}:
                    failed_clones.add(action["id"])
    return ok


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install missing ppt-planner-maker dependencies (opt-in)."
    )
    parser.add_argument("--workspace", default=None, help="目标工作区；默认取当前目录。")
    parser.add_argument(
        "--skills-dir",
        action="append",
        default=[],
        help="依赖安装目标根目录；默认 ~/.ppt-planner/skills（宿主不扫描）。",
    )
    parser.add_argument(
        "--deps-file",
        default=str(DEFAULT_DEPS_FILE),
        help="依赖清单路径；默认 scripts/deps.json。",
    )
    parser.add_argument(
        "--branches",
        default="",
        help="只处理这些分支的依赖，例如 A,F；默认全部。",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="真正执行安装；不加时只打印计划。",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="跳过版本锁定，使用上游最新提交；默认锁定到 deps.json 的 testedVersion。",
    )
    parser.add_argument(
        "--pin",
        action="store_true",
        help="兼容旧命令的空操作：现在默认就会锁定版本。",
    )
    parser.add_argument(
        "--company-template-file",
        action="store_true",
        help="用户自带公司 .pptx/.potx 模板文件；分支 A 不要求预装 deck。",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 计划。")
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
        target_root = choose_target_root(list(args.skills_dir), roots)
        outside_error = _ensure_outside_skill(target_root)
        if outside_error:
            raise ValueError(outside_error)

        plan = build_plan_for_run(
            deps,
            selected,
            roots,
            workspace,
            branches,
            target_root,
            not args.latest,
            args.company_template_file,
            bool(args.skills_dir),
        )
    except (OSError, ValueError) as exc:
        print(f"setup: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        _print_plan(plan, args.yes)

    if args.yes:
        ok = _run_actions(plan)
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
