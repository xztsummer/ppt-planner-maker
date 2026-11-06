# Changelog

## 2.4.0 — 2026-11-05

围绕“普通用户装得上、选得对、拿到的成品可验证”做的一轮修复。

### Added

- **`scripts/verify_deck.py`**：只读的成品结构检查。PPTX 查可见页数、占位残留、整页图、孤儿页、备注；HTML 查本地资源、外部资源、占位残留、页数；扩展名与内容不符直接 FAIL。交付前必跑，不替代视觉检查。
- **内容适配检查**（`production.md` §三）：标题数量词与图形块数一致、并列块内容切题、一页一个主结论。
- **模板页映射**：现成模板库确认逐页大纲时列出“大纲页 → 模板页”，结构装不下当场提出。
- **`doctor.py` 版本漂移与绕过提示**：已装版本与已测不一致时提示；装在宿主扫描目录时提示可能绕过编排层。
- 本地 `evals/e2e-cases.md`：5 个端到端用例和统一 rubric（只写未执行）。

### Changed

- **依赖默认装到私有目录**：`setup.py` 默认装到宿主不扫描的 `~/.ppt-planner/skills`（`PPT_PLANNER_HOME` 可覆盖），只暴露编排层。已装副本仅在已测版本一致时复用；漂移或未知版本按安装计划处理。
- **默认锁定已测版本**：`setup.py` 默认 checkout `testedVersion`，新增 `--latest`；`--pin` 保留为空操作；克隆失败不再执行 checkout。
- **同步上游后锁定**：`ppt-master` → `bc72031`（v6.8.0），`guizang-ppt-skill` → `93d21bf`；`gorden-ppt-skill`、`html-ppt` 未变。
- **gorden 不再自动更新**：编排层有意不执行 `apply_update.py`，改跑只读的 `check_update.py`，用户同意才更新。
- **guizang 品牌色**：跟随上游，改由 `gz-theme.mjs` 受约束生成（需要 node），不直接写用户色值。
- **对齐 ppt-master 路由**：用户 `.pptx` 模板 + 新内容默认 Edit Native PPTX，明确要可复用工作区或 `.potx` 无法直接填充时才 Create Template；Beautify 表述为 Generate 的 profile；该路径预检加 `--company-template-file`，不再被 deck 探针误拦。
- **候选展示**：现成模板库改为正好 3 个候选 + “换一批”；宿主无法内嵌图片时给 `preview.png` 绝对路径。
- **输出格式前置**：首轮问法和最小表单都问 PPTX 还是网页，并给白话指引。
- **对用户说人话**：表单和话术不再出现分支、模式、deck、Skill 名；许可提示保留模板来源。
- **去重瘦身**：路由规则只保留在 `SKILL.md` §四，运行时四文件合计减少 20% 以上；不改语义。

### Fixed

- 修复显式安装目标被旧副本抢占、版本漂移安装计划与 clone → pin → pip 顺序；pip 子进程支持 PyYAML 纯 Python 构建并补齐失败提示。
- 新增 clean_deck.py，删除不可达部件并同步元数据；含占位孤儿升级 FAIL；递归检查 HTML 本地 CSS 与外部字体。
- 补充模板照片、关键数字槽位、图标含义的内容适配检查。

- 运行时探针 `skia` 改为 `pathops`：`skia-pathops` 的导入名是 `pathops`，此前分支 A/B/F 装完也永远显示未就绪。
- 单测不再因本地被忽略的运行目录失败。
- 去掉绑定具体 Python 版本的过时提示；修正 `dependencies.md` 与 `intake.md` 的序号、项数错误。

### Decisions

- 路由不按用途分流，暂不管其他 Skill 的用途限制（维护者决策，2026-11-05）。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`
- 全量路由干跑，见本地 `evals/reports/2026-11-05-routing-2.4.md`。

## 2.3.0 — 2026-10-27

面向普通用户的场景路由：先问“用在什么场合、给谁看、想要什么感觉”，场景命中 gorden 模板库时推荐分支 C，而不是默认落到 ppt-master 自由设计。

### Changed

- **新增“具体场景”字段**：述职竞聘、开题答辩、教学说课、党政党课、数据可视化、总结复盘、运营汇报、商务提案、架构流程等；用于路由推荐，不替代原有“使用场景”的叙事分类。
- **场景优先推荐 gorden**：可编辑 PPTX、未点名其他制作 Skill、未要求公司模板时，具体场景命中 gorden 模板库擅长类型 → 推荐分支 C 模式 A，展示 2–3 个模板预览、非商业许可与能力边界；用户拒绝或要求完全定制时走 B。
- **结果语言问法**：制作路线未定时先问场合、听众和想要的感觉，再给推荐或结果语言三选一；保留“我知道我要什么”的直接路线入口。
- **“你定 / 随便”落点**：具体场景命中 gorden 或复杂豪华 → C 模式 A；否则 B。明确路线、公司模板和“从零设计”仍优先。
- **短表单调整**：删除“不确定就选从零设计”，改为“不确定就写‘你定’，我会按场景推荐”；新增可选“具体场景”行。
- **frontmatter 关键词**：补 WPS、述职竞聘、答辩、说课、党政、总结、复盘、数据可视化，改善普通人用场景词触发 Skill 的命中率。
- 同步 `SKILL.md`、`references/{intake,production,confirmation}.md`、README、设计/迁移文档与评测；`check_skill.py` 增加“不确定就选从零设计”旧口径拦截。

### Breaking

- 2.2 中“未说明路线且无复杂豪华时默认从零设计”的行为在场景命中 gorden 时不再成立；年度总结、内部培训、运营汇报、述职竞聘等场景会先推荐 gorden 模式 A。
- 需求表新增“具体场景”行；旧项目续作时需补记。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`
- 路由干跑 T46–T55 与受影响用例（报告见 `evals/reports/2026-10-27-routing-2.3.md`）。

## 2.2.0 — 2026-10-27

“复杂豪华”从纯视觉密度改为分支 C 的 PPTX 偏好信号；gorden 内部按模式 A / C 分工，避免把“豪华”降级成简洁原创。

### Changed

- **“复杂豪华”默认推荐 gorden（分支 C）**：可编辑 PPTX、未点名其他制作 Skill、未要求公司模板时，用“复杂豪华 / 豪华 / 繁复”描述版面，默认推荐 `gorden-ppt-skill`，依据记“复杂豪华版面偏好”；不再只当视觉密度。
- **gorden 模式选择**：默认模式 A（内置模板）兑现复杂豪华；模式 C 原创仅用于用户明确接受简洁设计，不得承接复杂豪华。
- **冲突处理**：用户明确不要模板又要复杂豪华时，在“接受 gorden 模式 C 简洁原创 / 改走 `ppt-master` 自由设计（分支 B）”之间二选一，不静默降级；模板承载不了额外要求时先换模板，仍不行改走 B 或调整需求，不用模式 C 兜底。
- **路线优先级不变**：明确 A/B/C/D/E/F 优先；HTML 不受影响；“专业简洁”“高级/好看”和描述内容复杂不触发 C。
- 同步 `SKILL.md`、`references/{intake,production,confirmation,planning}.md`、README、设计/迁移文档与评测用例；`check_skill.py` 增加旧口径拦截。

### Breaking

- 2.1 中“复杂豪华只影响版式、不影响分支”的行为不再成立；旧需求表只记“视觉密度：复杂豪华”的续作项目，需要补记 gorden 模式 A 或按用户最新选择更新。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`
- 路由干跑 T40-T45（报告见 `evals/reports/2026-10-27-routing-2.2.md`）。

## 2.1.0 — 2026-10-26

面向普通用户的可用性修复：补齐运行时路径与宿主发现，修掉两个会直接卡住或误路由的问题，并把模板来源、确认档位和 HTML 派生规则写清楚。

### Changed

- **运行命令统一用 `{SKILL_DIR}` 绝对路径**：`SKILL.md`、`references/dependencies.md`、README、`docs/install.md` 不再假设当前目录是 Skill 根；避免装好后在用户工作区执行 `python scripts/...` 直接报文件不存在。
- **解析器新增 ZCode 根目录**：`<workspace>/.zcode/skills` 与 `~/.zcode/skills`（`ZCODE_HOME`）加入解析顺序，和 DSH / Agents / Claude 并列；文档同步。
- **双格式不再抹掉 PPTX 路线**：只有“输出格式仅为 HTML”才把制作路线记为“不适用（HTML）”；同时交付 PPTX + HTML 时仍按 PPTX 三选一记录。
- **“随便/都行”按上下文分流**：回答制作路线问题时按“从零设计（AI 建议）”；对确认方式说“你看着办/随便”才追问合并确认还是授权直出。
- **快速模式与分支 C/E 对齐**：授权直出时，gorden 模板、guizang A/B 与主题由 AI 选定并记录，不再转问；许可提示和阻塞检查仍执行。
- **模板来源护栏**：套公司模板但品牌不匹配时先说明并建议 B/C；用户给 `.pptx` / `.potx` 模板时先走 ppt-master Create Template（deck），不把 `.pptx` 当 deck 目录；“用现成设计模板”明确指 gorden 内置模板库，用户自备模板不走 C。
- **分支 E 触发收敛**：只有明确“杂志风/杂志感/瑞士风/指定 guizang”才直接进入；仅说“设计感”时先做一次 D/E 二选一确认。
- **需求调研更省事**：缺口较多时默认给可预填推荐值的短表单；目标/听众/时长可给推荐值供确认，但不得静默采用；新增“演示语言”“画布比例”字段。
- **移除硬编码 `#0058FF`**：HTML 分支未指定配色时使用 html-ppt / guizang 自带默认主题，不再由编排层发明主色。
- **视觉检查更明确**：渲染器/浏览器可用时视觉检查是交付前必经项；不可用时在交付摘要第一行标注“视觉检查未完成”。
- **许可证决策（维护者，2026-10-26）**：原创部分维持 CC BY-NC 4.0，不添加内部使用豁免；商业与多数职场使用按许可原文需维护者书面授权，README 保留白话提示。
- **一键安装（需同意）**：依赖缺失时先给命令；用户同意后可由 `setup.py --yes` 代为安装（只覆盖 git/pip，不碰系统级组件）。

### Added

- `scripts/doctor.py`：只读的“一条命令体检”，合并路径解析、能力探针与运行时检查，输出用户可读的下一步；不安装、不写 Skill 包。
- `scripts/setup.py`：可选的一键安装器，默认只打印计划，`--yes` 才执行（git clone 缺失依赖 + pip 装缺包，`--pin` 锁定 testedVersion commit）；拒绝把依赖装进 Skill 包，系统级组件只提示不代装。
- `check_runtime.py`：导入前设置 `sys.dont_write_bytecode`，不再向 Skill 包写 `__pycache__`；改用真实 `importlib.import_module`，能发现缺 DLL/初始化失败；`--brief`；新增 `anyCommands` 浏览器探针（Edge/Chrome/Firefox 常见路径，任一命中即可，缺失只提示不阻塞构建）。
- `resolve_skills.py`：`--brief` 一行摘要；`childPath` 能力探针（分支 A 要求 deck 内有 `templates/design_spec.md`）；`deck-index` 探针（`decks_index.json`）；`requirements.txt` 探针；版本回退读取 `SKILL.md` frontmatter 的 `metadata.version`。
- `check_skill.py`：发现 `__pycache__` 或残留“只有一套就直接用”旧口径时给出警告。
- `tests/`：新增扁平文件遮蔽、`childPath`、frontmatter 版本、真实 import、`--brief`、零 `__pycache__`、浏览器探针、doctor、setup 计划等回归，共 76 项。
- PDF 交付路径：用户明确要求 PDF 时，PPTX 用 LibreOffice 转换、HTML 用浏览器打印，转换后核对页数，不可用时如实说明。
- `evals/cases.md`：新增自备 `.pptx` 模板、公司品牌不匹配、自备设计模板 ≠ gorden、授权直出 + C/E、路线“随便” vs 确认“随便”、“模板你定”等用例；合规检查新增脚本绝对路径、Skill 包零写入与“安装需用户同意”。
- `.github/workflows/ci.yml`：公开 CI 跑 `check_skill.py` 与单测。

### Fixed

- 扁平 `<id>.md` 不再遮蔽低优先级的有效 `<id>/SKILL.md`；目录型 bundle 优先，扁平文件只作为回退并标记 `invalid`。
- `check_runtime.py` 的 `__pycache__` 写入问题；工作区已有 `scripts/__pycache__` 已清理。
- `AGENTS.md` 的同步清单补上 `README.en.md`、`deps.json`、`dependencies.md` 和新宿主根目录。

### Breaking

- 分支 A 的 deck 探针更严格：只有子目录但缺 `templates/design_spec.md`，或缺少 `decks_index.json`，会判为 `incomplete`。
- HTML 分支不再默认 `#0058FF`；旧项目里记录该色的，按用户原记录保留，新项目按制作 Skill 默认主题。
- “用现成设计模板”只指 gorden 内置模板库；自备模板改走 ppt-master Create Template/Beautify。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`（76 tests）
- `python scripts/doctor.py --workspace . --branches A,B,C,D,E,F --brief`
- `python scripts/setup.py --workspace . --branches A,F`（计划模式，只读）
- `python scripts/resolve_skills.py --workspace . --branches A,B,C,D,E,F --brief`
- `python scripts/check_runtime.py --branches A,B,C,D,E,F --brief`
- 路由干跑 14 例（T04/T06/T07/T13/T17/T25/T33/T34/T35/T36/T37C/T37E/T38A/T39，覆盖 2.1.0 全部路由改动），M 项 14/14 通过、0 误路由（报告见 `evals/reports/2026-10-26-routing-2.1.md`）。
- `setup.py --yes` 真实端到端（隔离临时 skills 目录，全部依赖来源指向临时根）：分支 C 计划模式只读 → `--yes` 真实 `git clone` gorden-ppt-skill → doctor 复检就绪 1/1（version 1.0.20）；分支 B `--yes --pin` 真实克隆 ppt-master 并 checkout 至 testedVersion（`HEAD is now at 0e8d92c`）、`uharfbuzz 0.57.0` pip 装成功，`skia-pathops` 因当前 Python 3.14 无任何可用发行版（upstream 未发 cp314 wheel）而失败，setup 如实报错退出 1，doctor 同步显示 incomplete（仅缺 skia）——据此新增 pip 失败的针对性提示（建议 3.11/3.12）并写入 deps.json 说明。

## 2.0.0 — 2026-10-26

路由模型从“公司模板默认 + 内容偏好选引擎”改为“制作路线提问 + 视觉密度只调版式”，面向公开通用场景。

### Changed

- **新增制作路线字段**：套公司模板 / 用现成设计模板 / 从零设计。无默认值；用户未说明时先问一次三选一，答“你定 / 随便 / 都行”按“从零设计”并标“AI 建议”。
- **移除默认公司模板**：不再默认“是 / 中国电子云”。分支 A 的 deck 由用户指定，或从 `templates/decks/` 的可用 deck 中选择；没有可用 deck 时按依赖缺失阻塞。
- **“内容偏好”拆为“视觉密度”**：复杂豪华 / 专业简洁（默认专业简洁），只影响版式，不再决定分支；分支 C 由“用现成设计模板”触发。
- 分支 A/B/C 的条件改为制作路线；D/E 仍按 HTML 与真实风格意图；F 不变。
- `需求调研.md` 模板：`必须使用公司模板` / `内容偏好` 行替换为 `制作路线` / `公司模板` / `视觉密度`。
- 快速模式：制作路线三选一必须出现在合并展示里；授权直出时按“从零设计”补全并标“AI 建议”。
- **依赖预检提前**：制作路线明确后立即落定分支并做只读预检（`resolve_skills.py` + `check_runtime.py`），不等三轮确认完才发现缺依赖；正式制作前用最终工作区复检。
- **分支不因缺字段回退**：目标、听众、时长等必填项缺失只阻塞需求确认，不把已确定的分支记为“待定”。
- **快速模式档位拆清**：赶时间（“越快越好 / 别问太多”）只到合并确认；授权直出需“不用确认 / 直接做 / 你全权决定”；“路线你定 / 模板你定”只授权字段，不进入快速模式；“你看着办 / 都行”先追问一次档位。
- 安装文档补全：ppt-master 的 `pip install -r requirements.txt`、gorden 的 `python-pptx` 与首次联网更新、LibreOffice 渲染器、Windows `python3` → `python`。
- 评测用例扩到 33 例，新增“沉默用户必须提问”“你定 → B”“现成模板 → C + 许可提示”“双格式”“运行时缺包阻塞”“路线明确但字段缺失仍落分支”“赶时间 ≠ 直出”“字段授权 ≠ 快速模式”等回归。

### Added

- `scripts/check_runtime.py`：只读检查选中分支的 Python 包与命令，支持 `--json`、`--check`；`soffice` 会尝试常见安装路径。
- `scripts/deps.json`：每个依赖增加 `runtime` 清单（必需/可选 Python 包、命令、pip 提示）；分支 A 的 deck 探针改为 `decks` + `requireAnyChild`，不再绑定中国电子云。
- `scripts/resolve_skills.py`：支持 `requireAnyChild`，目录为空时能力状态为 `empty`、依赖为 `incomplete`；`--check` 输出 `empty` 提示；校验 `runtime` 结构。
- `tests/test_check_runtime.py`：运行时探针单测；`tests/test_resolve_skills.py` 补 deck 探针与清单测试。
- `references/dependencies.md`：补“运行时依赖”表、pip 命令与渲染器说明。
- `docs/install.md`：补 Python 运行时依赖、渲染器、故障排查。
- `docs/design.md`：补字段同步清单、deck 探针、运行时探针与已知限制。
- `docs/migration.md`：补 1.x → 2.0 字段映射。

### Breaking

- 旧需求表里的“必须使用公司模板 = 是（默认）”不再生效；未说明制作路线时必须先提问。
- 旧“内容偏好”不再参与路由；旧记录只作历史信息，续作时补“制作路线”和“视觉密度”。
- 分支 A 不再默认中国电子云 deck；用户未指定且本机有多套 deck 时会要求选择。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`
- `python scripts/check_runtime.py --check --branches A,B,C,D,E,F`
- 路由干跑 27 例 + P1-2 回归 8 例 + P1-4 回归 3 例（报告见 `evals/reports/`）。

## 1.0.0 — 2026-10-26

首个“单 Skill 包”版本。仓库根目录即 `ppt-planner-maker`，四个制作 Skill 改为外部依赖。

### Changed

- 仓库根目录改为 Skill 根：`SKILL.md` 与 `references/` 上移，不再有 `skills/ppt-planner-maker/`。
- `ppt-master`、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill` 移出仓库，作为外部依赖按需安装。
- 路由表增加 `分支` 列，只写逻辑 ID；制作路径改用 `{skill:<id>}` 占位，由解析器给出绝对路径。
- 运行资产（`projects/`、`output/`、参考素材、只读效果样例）移出仓库；Skill 包只读，产物写到目标工作区。
- 需求调研不再记录“使用性质”；非公司模板 PPTX 由内容偏好决定分支（复杂豪华 → gorden，专业简洁 → ppt-master）。
- 分支 C 的需求表增加 gorden 内置模板的非商业许可提示；快速模式不省略。
- `THIRD_PARTY_NOTICES.md` 从“随仓库分发的第三方组件”改为“外部依赖许可矩阵”。
- `LICENSE` 的适用范围改为本仓库原创文件，署名与仓库 URL 更新为 `ppt-planner-maker`。

### Added

- `scripts/deps.json`：四个制作 Skill 的机器可读清单（ID、上游、许可证、分支、能力探针、安装信息）。
- `scripts/resolve_skills.py`：按项目/用户根目录解析依赖，检查能力，支持 `--json`、`--check`、`--out`。
- `docs/install.md`：宿主发现规则、安装、验证与故障排查。
- `docs/migration.md`：从 0.9 及旧工作区迁移。
- `docs/design.md`：维护者的单一事实源、同步清单、依赖契约与评测规则。
- `VERSION`、`CHANGELOG.md`。
- `references/dependencies.md`：依赖安装、解析顺序、能力要求与许可边界。

### Fixed

- 修正 README 与 `SKILL.md` 的路由漂移：旧 README 仍按“商业/个人用途”分流。
- 删除 `confirmation.md` 中“使用许可判断（默认走 ppt-master）”的旧口径，改为 gorden 许可提示。
- 清理 `intake.md` 的“使用性质”字段与模板行。
- 修正 `SKILL.md` 许可链接（上移到根目录后指向 `LICENSE`）。

### Breaking

- 旧提示词中的 `skills\ppt-master`、`skills\guizang-ppt-skill` 等路径不再指向仓库内目录；需先安装依赖，再直接用 Skill 名。
- 旧脚本若按 `skills/ppt-planner-maker/SKILL.md` 读取入口，需改为根目录 `SKILL.md`。
- `AGENTS.md` 不再声明“默认执行 `skills\ppt-planner-maker`”；默认入口由宿主 catalog 提供。

### Verification

- `python scripts/check_skill.py`
- `python -B -m unittest discover -s tests`
- 路由干跑：A–F 分支、冲突拦截、负向风格词、依赖缺失、只要大纲、工作区保护。
- 真实端到端：至少一条公司模板 PPTX 或 HTML 分支，检查解析、交接与成品。

## 0.9.0 — 2026-10-26

最后一版捆绑式工作区：5 个 Skill（1 个编排 + 4 个制作）与演示资产同仓，路由按内容偏好分流，保留“使用性质”之外的新口径。作为迁移回滚点保留。
