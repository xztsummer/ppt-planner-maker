# 仓库开发约定

本仓库只维护 `ppt-planner-maker` 一个 Skill。根目录 `SKILL.md` 就是运行时入口，不再有 `skills/` 中间层。

- **制作 Skill 是外部依赖**：`ppt-master`、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill` 不复制进本仓库；依赖清单见 `scripts/deps.json`，安装与解析见 `references/dependencies.md`。
- **改路由时同步四处**：`SKILL.md` §四决策表 → `references/production.md` 分支手册 → `README.md` 路由摘要 → `evals/cases.md` 期望值；然后运行 `python scripts/check_skill.py`。
- **运行产物不写入仓库**：`projects/`、`output/`、`_build/`、`*.pptx`、`*.html` 已在 `.gitignore`；任务产物写到目标工作区。
- **评测用例在本地**：`evals/` 不随仓库分发，规则见 `.gitignore` 与 `docs/design.md`；Python 单元测试在 `tests/`，随仓库分发。
- **脚本只用标准库**：`scripts/resolve_skills.py` 与 `scripts/check_skill.py` 不引入第三方依赖；Windows 上优先用 `python`。
- **Windows 中文路径**：临时 PowerShell 脚本保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`；无 BOM 的 UTF-8 会被 PowerShell 5.1 按 GBK 读取，可能吞掉路径分隔符并生成乱码目录。

## 常用命令

```bash
python scripts/check_skill.py
python -m unittest discover -s tests
python scripts/resolve_skills.py --workspace <工作区> --branches A,F --json
```
