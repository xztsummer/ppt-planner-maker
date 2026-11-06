# 仓库开发约定

本仓库只维护 `ppt-planner-maker` 一个编排 Skill：根目录 `SKILL.md` 是运行时入口（`references/` 是运行时正文），`scripts/` 是依赖解析与自检，`docs/` 是维护者文档，`tests/` 是 Python 单测。不再有 `skills/` 中间层。

## 边界与外部依赖

- 四个制作 Skill（`ppt-master`、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill`）是外部依赖，不复制进仓库；清单在 `scripts/deps.json`（ID/分支/能力探针/运行时），安装与解析见 `references/dependencies.md`。路由只写逻辑 ID 与 `{skill:<id>}` 占位，不写物理路径。
- 运行产物不写入仓库：`projects/`、`output/`、`_build/`、`*.pptx`、`*.html` 已在 `.gitignore`；任务产物写到目标工作区，Skill 包只读。

## 运行时命令约定

- 编排层运行预检必须展开为 `{SKILL_DIR}/scripts/...` 绝对路径（`SKILL_DIR` = 根目录 `SKILL.md` 所在目录），不假设 cwd 是 Skill 根；该规则写在 `SKILL.md` 开头引用块。
- 脚本只用标准库，Windows 上用 `python`（不要 `python3`）；所有脚本导入本地模块前设置 `sys.dont_write_bytecode = True`，Skill 包必须保持零 `__pycache__`、零写入。

## 脚本职责与探针语义

- `resolve_skills.py` / `check_runtime.py` / `doctor.py` 只读；`doctor.py` 是面向用户的合并就绪结论。
- `setup.py` 是唯一安装入口：默认只出计划，`--yes` 才执行 git clone / pip；默认装到宿主不扫描的 `~/.ppt-planner/skills`（只暴露编排层）并锁定 `testedVersion`，`--latest` 跳过锁定；拒绝装进 Skill 包，LibreOffice、浏览器等系统级组件只提示不代装，pip 失败会给出针对性提示。
- `verify_deck.py` 只读，交付前必跑：FAIL 不得报告完成；只查结构，不替代视觉检查。
- 探针在 `scripts/deps.json` 声明：分支 A 选择已安装 deck 时要求 deck 子目录含 `templates/design_spec.md` 且存在 `decks_index.json`；仅用户自带公司 `.pptx` / `.potx` 文件时可用 `--company-template-file` 取消这两项的 required 标记，其他探针不放松；`anyCommands`（浏览器）是"任一存在即可"，只提示不阻塞构建。

## 改动同步清单

- **改路由**（分支/条件/制作路线/视觉密度/模板来源）：`SKILL.md` §四 → `references/production.md` → `README.md`+`README.en.md` 摘要 → `scripts/deps.json`+`references/dependencies.md` → `evals/cases.md` 期望值；字段级改动另同步 `references/intake.md`、`references/planning.md`、`references/confirmation.md` 与 `需求调研.md` 模板。
- **新增宿主 skills 根目录**：`scripts/resolve_skills.py` 的 `build_roots` + `references/dependencies.md` + `docs/install.md` + 两个 README 一起改。
- 改完必跑 `python scripts/check_skill.py`（0 error 才算过；`STALE_TERMS` 会拦截"只有一套就直接用"等旧口径）和 `python -B -m unittest discover -s tests`。`check_skill` 只能证明结构一致，路由行为要靠干跑。

## 评测（本地，不随仓库分发）

- `evals/cases.md` 是路由干跑用例集，`evals/reports/YYYY-MM-DD-routing*.md` 记录结果；干跑方式：每个用例一个独立只读子代理，只读 `SKILL.md` 与相关 `references/`，禁止创建文件、禁止调用制作 Skill。大改路由后必须补一轮干跑并把报告写入 `evals/reports/`。

## 已知坑与既定决策

- `skia-pathops` 在过新的 Python 上可能缺少可用 wheel；PPTX 分支运行时建议 3.11/3.12，`setup.py` 会在 pip 失败时给出提示。
- Windows：临时 PowerShell 脚本存 UTF-8 with BOM（否则按 GBK 读取）；路径含空格加引号。
- 许可证（维护者决策，2026-10-26）：原创部分维持 CC BY-NC 4.0，不加内部使用豁免；不要再当作未决项。
- 路由不按用途分流（维护者决策，2026-11-05）：暂不管其他 Skill 的用途限制，不因商用风险收窄 gorden 的场景推荐，只保留现有许可提示；不要再当作未决项。
- 路由规则只写在 `SKILL.md` §四，其他文件只引用，不转述。
- `VERSION` 是 semver 且必须出现在 `CHANGELOG.md`。
- 升级依赖：`git ls-remote` 看上游 → 克隆到临时目录查探针、`requirements.txt` 与入口 diff → 对齐 `SKILL.md`、`production.md` → 更新 `deps.json` 的 `testedVersion`/`testedRelease` 和 `dependencies.md` → 跑检查与受影响用例干跑。
- **Windows 中文路径**：临时 PowerShell 脚本保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`；无 BOM 的 UTF-8 会被 PowerShell 5.1 按 GBK 读取，可能吞掉路径分隔符并生成乱码目录。

## 常用命令

```bash
python scripts/check_skill.py
python -B -m unittest discover -s tests
python scripts/doctor.py --workspace <工作区> --branches A,F --brief
python scripts/setup.py --workspace <工作区> --branches A,F   # 计划模式，--yes 才安装
python scripts/verify_deck.py <成品路径> --expected-pages <页数> --brief
python scripts/resolve_skills.py --workspace <工作区> --branches A,F --brief
python scripts/check_runtime.py --branches A,F --brief
```

以上是维护者在仓库根目录运行的命令；编排层运行时用 `{SKILL_DIR}/scripts/...` 绝对路径（见「运行时命令约定」）。


显式 --skills-dir 仅检查目标根目录，其他副本只提示；默认仅复用 drift=match 的副本，drift/unknown 则计划装入私有目录（PPT_PLANNER_HOME 可覆盖）。目标已有不同或未知版本需手动处理，不覆盖、不自动切换；项目级旧副本可能抢占，须按警告处理。执行顺序为 clone → pin → pip，requirements 取锁定后的目标副本。

PyYAML 无 wheel 时，setup.py 仅向 pip 子进程传 PYYAML_FORCE_LIBYAML=0 以使用纯 Python 构建；requirements 安装失败也提供 PyYAML、skia-pathops、uharfbuzz 提示，不修改全局环境。

`clean_deck.py` 是显式输出的新成品清理器：从包根关系遍历删除不可达部件，同步 Content_Types、sections 和应用属性；保留其余可达部件字节，拒绝覆盖输入。清理后重新 verify 和视觉检查；verify 的含占位孤儿为 FAIL，其他孤儿为 WARN；HTML 递归检查本地 CSS、@import 和 url，防循环。
