# ppt-planner-maker

**中文** | [English](README.en.md)

一个**只做编排**的 Agent Skill：把 PPT 需求变成确认过的逐页方案，再路由到四个外部制作 Skill，产出可编辑 PPTX 或 HTML。

> 本仓库不含制作引擎。`ppt-master`、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill` 需要单独安装，见 [docs/install.md](docs/install.md) 与 [references/dependencies.md](references/dependencies.md)。

## 它做什么

- **三个入口**：从主题规划大纲、按已有大纲/材料制作、修改或美化现有 PPTX。
- **场景优先，路线兜底**：先问“用在什么场合、给谁看、想要什么感觉”。述职竞聘、开题答辩、教学说课、党政党课、总结复盘、数据可视化、运营等场景命中 gorden 模板库时，默认推荐 gorden（内置模板模式 A），给正好 3 个候选预览并附“换一批”；宿主无法内嵌图片时给 `preview.png` 绝对路径；场景不命中或你要完全定制时，再选套公司模板 / 用现成设计模板 / 从零设计。说“你定”时，场景命中按 gorden，否则从零设计。
- **分级确认**：需求、规划思路、逐页大纲/修改方案先在对话中完整展示，用户明确确认后才落盘；制作引擎内部产物直接写入项目工作区。
- **只做编排**：不画页面、不生成 deck，把确认稿和制作约束交给选中的制作 Skill，并检查交接与成品。
- **依赖可替换**：路由只引用逻辑 ID，物理路径由 `scripts/resolve_skills.py` 解析；缺依赖时停止并给安装命令，不静默换路线。
- **可移植**：仓库根目录就是 Skill，clone 或软链到宿主 skills 目录即可被发现；运行产物写到用户工作区，不写入 Skill 包。

## 安装

### 1. 安装本 Skill

DSH 用户级（推荐）：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.dsh/skills/ppt-planner-maker
```

Claude Code 用户级：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.claude/skills/ppt-planner-maker
```

ZCode 用户级：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.zcode/skills/ppt-planner-maker
```

项目级（Windows 目录联接，无需管理员）：

```bat
mklink /J "<工作区>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

macOS / Linux 项目级软链：

```bash
ln -s /path/to/ppt-planner-maker <工作区>/.dsh/skills/ppt-planner-maker
```

DSH 只扫描一层 `<root>/<name>/SKILL.md`；不要把本仓库再套一层 `skills/` 目录，否则不会被发现。ZCode 也是同样的目录形态：放到 `~/.zcode/skills/ppt-planner-maker` 或 `<工作区>/.zcode/skills/ppt-planner-maker` 即可。Claude Code 等宿主同理，放进其 `skills/` 根目录即可。

### 2. 安装制作依赖

至少安装当前任务需要的分支依赖；四个全装也可以。`<skills-dir>` 指任一被宿主扫描的 skills 根目录。本 Skill 不预置任何公司模板；分支 A 选择已安装 deck 时需要至少一个公司模板（可用 fork 自带的中国电子云、中国电信、中汽研）；用户自带 `.pptx` 模板 + 新内容时默认 Edit Native，不要求预装 deck。

```bash
# 分支 A / B / F；公司模板必须使用这个 fork
git clone https://github.com/xztsummer/ppt-master.git <skills-dir>/ppt-master

# 分支 C
git clone https://github.com/GordenSun/GordenPPTSkill.git <skills-dir>/gorden-ppt-skill

# 分支 D
git clone https://github.com/lewislulu/html-ppt-skill.git <skills-dir>/html-ppt

# 分支 E
git clone https://github.com/op7418/guizang-ppt-skill.git <skills-dir>/guizang-ppt-skill
```

也可以把依赖集中放在自定义目录，用环境变量告诉解析器：

```bash
# Windows PowerShell
$env:PPT_PLANNER_SKILLS_DIR = "D:\path\to\ppt-skills"
# macOS / Linux
export PPT_PLANNER_SKILLS_DIR="$HOME/path/to/ppt-skills"
```

### 2.1 安装 Python 运行时依赖

`git clone` 只装引擎，PPTX 分支还需要 Python 包：

```bash
# 分支 A / B / F（ppt-master）
python -m pip install -r <skills-dir>/ppt-master/requirements.txt

# 分支 C（gorden）
python -m pip install python-pptx
```

分支 D / E 无 Python 运行时依赖。`requirements.txt` 里的 `edge-tts`、`PyMuPDF` 是可选能力；PyMuPDF 是 AGPL-3.0。PPTX 视觉检查与旧版 `.ppt` 转换需要 LibreOffice（`soffice`），不在 PATH 时脚本会尝试常见安装目录。

### 2.2 一键安装（推荐）

先用计划模式看看会做什么（只读，不安装）：

```bash
python "<skill-dir>/scripts/setup.py" --workspace <工作区> --branches A,F
```

确认后加 `--yes` 执行：缺失的依赖 `git clone` 到私有目录 `~/.ppt-planner/skills` 并锁定到 `deps.json` 记录的已测版本，缺的 Python 包用 `pip` 安装。这个目录不被宿主扫描，所以只有本编排 Skill 会响应“做 PPT”，不会被制作 Skill 抢走请求；制作 Skill 由编排层按绝对路径加载。可用 `--skills-dir` 或 `PPT_PLANNER_HOME` 改位置，用 `--latest` 改装上游最新版。LibreOffice、浏览器等系统级组件只提示，不代装。**安装只在你说“可以/装吧”之后发生。**

### 3. 验证

```bash
python "<skill-dir>/scripts/doctor.py" --workspace <工作区> --branches A,B,C,D,E,F
```

`doctor.py` 只读，会把路径、能力和运行时检查合成一份结论。缺什么按“下一步”安装，再重跑；需要单独排查时再用：

```bash
python "<skill-dir>/scripts/resolve_skills.py" --check --branches A,B,C,D,E,F
python "<skill-dir>/scripts/check_runtime.py" --check --branches A,B,C,D,E,F
```

`<skill-dir>` 是含 `SKILL.md` 的本仓库根目录，不是当前工作区。路径检查全部 `OK` 只代表目录就绪；运行时检查通过才代表能构建。Windows 上如果 `python3` 指向 Microsoft Store 占位程序，改用 `python`。

## 快速开始

第一次用会先问“这份 PPT 用在什么场合、给谁看、想要什么感觉、要 PPTX 还是网页”。要发给别人继续改、走公司流转，选可编辑 PPTX（默认）；现场放映、线上分享、想要动效，选网页 HTML（不能在 PowerPoint 里编辑）。例如：

```text
场景：述职竞聘 / 开题答辩 / 教学说课 / 党政党课 / 年度总结 / 项目复盘 / 数据可视化 / 运营汇报 / 客户提案 / 其他
感觉：正式 / 简洁 / 复杂豪华 / 有设计感 / 没特别要求
输出格式：可编辑 PPTX（默认，便于继续修改和公司流转）/ 网页 HTML（适合放映、分享和动效，不能在 PowerPoint 里编辑）
```

如果场景命中 gorden 的 21 套中文模板库，会默认推荐 ②，并给你看正好 3 个模板预览，附“换一批”；无法内嵌图片时给出 `preview.png` 绝对路径。你也可以直接说“从零设计”或“用我们公司的模板”。如果你已经知道制作路线，可以直接选：

```text
① 套公司模板（你已经有自己的公司品牌模板，或本机已安装对应公司模板）
② 用现成设计模板（gorden 内置模板库：配色固定、可能带示例数据、不能新增版式、示例数字可能删不掉，商用需授权）
③ 从零设计（完全可改；有公司模板先选①，完全没头绪再选这个）
```

你不需要记分支 A–F、deck 或 gorden：这些是内部叫法。只要说清楚“用在什么场合、给谁看、要 PPTX 还是网页、想要什么感觉”就够了。不确定就写“你定”，我会按场景推荐。

场景命中模板库时，推荐的是 gorden 模式 A（内置模板）；它的模式 C 原创明确要求简洁，不能用来做场景模板或豪华版。如果你同时明确“不要模板”，会在“接受 gorden 模式 C 的简洁原创”和“改走 ③ ppt-master 自由设计”之间让你选一次。说“复杂豪华 / 豪华”时同理，默认推荐 ②。

如果你手里是一个公司的 `.pptx` 模板文件，直接说“用这个模板”，默认走 ppt-master 的 Edit Native PPTX 填充新内容；只有明确要可复用模板工作区，或 `.potx` 无法直接填充时，才走 Create Template。不要选“用现成设计模板”，那指的是 gorden 内置模板库。

如果先说清楚，可以直接下指令：

> 帮我做一份 15 页的《可信数据空间》汇报 PPT，听众是客户，讲解 30 分钟，从零设计，专业简洁。

三个入口：

- **① 规划大纲**：只有主题或零散材料，先调研、对齐思路，再逐页策划。
- **② 已有大纲制作**：保留原大纲顺序和原意，补齐逐页信息后制作；PDF/截图/旧 PPTX 也可当材料。
- **③ 修改/美化现有 PPTX**：保留原版式增量编辑，或保留内容重新设计版式；不覆盖源文件。

只要大纲：

> 先帮我出一版逐页大纲看看，别做 PPT。

赶时间时可以明确授权快速模式，但两档不同：

| 你说 | 档位 | 结果 |
|---|---|---|
| 一次确认就行 / 越快越好，别问太多 | 合并确认 | 多份文档合成一次确认，仍要你点头 |
| 不用确认，直接做 / 你全权决定 | 授权直出 | 展示后不等确认，直接制作 |

只授权某个字段不会进入快速模式：

> 路线你定。 → 只决定制作路线，仍按标准流程确认。

说“你看着办 / 都行”时，AI 会追问一次“合并确认还是全权决定”，不自行升级。

快速模式仍会检查依赖、展示 gorden 许可提示、执行下游阻塞检查和成品验证；主题仍需你提供，缺失数据不会被编造。规则见 [references/confirmation.md](references/confirmation.md)。

## 路由规则（摘要）

| 分支 | 触发条件 | 制作 Skill | 输出格式 |
|---|---|---|---|
| A | 制作路线 = 套公司模板 | `ppt-master` | 可编辑 PPTX |
| B | 制作路线 = 从零设计（用户明确） | `ppt-master` | 可编辑 PPTX |
| C | 制作路线 = 用现成设计模板（gorden 内置模板库）；或 PPTX + 场景命中 gorden 模板库 / “复杂豪华”版面（默认推荐，模式 A） | `gorden-ppt-skill` | 可编辑 PPTX |
| D | HTML，常规 | `html-ppt` | HTML |
| E | HTML，杂志风 / 瑞士风；仅“设计感”先确认 D/E | `guizang-ppt-skill` | HTML |
| F | 修改/美化现有 PPTX | `ppt-master` | 可编辑 PPTX |

权威规则在 [SKILL.md](SKILL.md) §四；这里只是摘要。

硬约束：

- **制作路线为“套公司模板”时只出可编辑 PPTX**。用户同时明确要求公司模板和 HTML 时，先请其改一项，不静默改需求。
- **没有默认公司模板**。用户未说明制作路线时先问场合与想要的感觉；场景未命中 gorden、也无“复杂豪华”偏好时再问三选一。不能静默套用任何品牌 deck。“复杂豪华”是 gorden 分支 C 的偏好信号，不是套公司模板的理由。用户给的是 `.pptx` 模板 + 新内容时，默认走 ppt-master Edit Native PPTX；明确要可复用工作区或 `.potx` 无法直接填充时才走 Create Template，不要当成已安装 deck。
- **场景推荐不是硬路由**。述职竞聘、开题答辩、教学说课、党政党课、总结复盘、数据可视化、运营等场景命中 gorden 时，只推荐分支 C 模式 A，并展示正好 3 个预览、“换一批”、非商业许可与能力边界；无法内嵌图片时给 `preview.png` 绝对路径；用户明确拒绝或要求完全定制时改走 ppt-master 自由设计。明确路线和公司模板仍优先。
- **gorden 内置模板仅限个人学习研究**。走分支 C（用现成设计模板、场景命中或复杂豪华推荐）时，需求表会写一行“模板许可提示：内置模板仅限个人学习研究，商用需自行取得授权”；商用前请自行取得模板作者授权。模式 C 原创不使用模板素材，但只能做简洁版式。
- **gorden 的场景模板和复杂豪华来自内置模板**。两者默认推荐 gorden 模式 A（内置模板）；模式 C 原创明确要求简洁，不能承接场景模板效果或复杂豪华。用户明确不要模板、又要求复杂豪华或“像现成模板那样”的效果时，在“接受模式 C 简洁原创”和“改走 ppt-master 自由设计”之间二选一，不静默降级；只拒绝模板、没有要求模板效果时按自由设计处理，不强行二选一。
- **guizang 只按真实风格意图触发**。否定说法、材料正文里的设计词、只说“复杂豪华”（HTML 场景）或“高级/好看”都不触发；PPTX 场景的“复杂豪华”按分支 C 处理。
- **HTML 不是 PowerPoint**。不要把 HTML 改名成 `.pptx`，也不要承诺它可编辑。
- **依赖缺失时停止**。给出具体 ID、缺失能力和安装命令，不猜测路径、不切换其他制作 Skill。

## 依赖预检

制作 Skill 不随本包分发。**分支确定后、开始逐页策划前**先做一次只读预检；不要等三轮确认完才发现缺依赖。

```bash
python "<skill-dir>/scripts/doctor.py" --workspace <工作区> --branches A,B,C,D,E,F
```

`doctor.py` 只读，会把“装没装、能力全不全、Python 包能不能用、版本是否与已测一致”合成一份结论；缺什么就按“下一步”安装，然后重跑。需要单独排查时再用：

```bash
python "<skill-dir>/scripts/resolve_skills.py" --workspace <工作区> --branches <选中分支> --brief
python "<skill-dir>/scripts/check_runtime.py" --branches <选中分支> --brief
```

第一个查“装没装、能力全不全”，第二个查“Python 包和命令能不能用”。`--brief` 输出一行摘要；需要排查时换成 `--json`。正式制作前用最终工作区复检一次。解析路径由 `scripts/resolve_skills.py` 给出，运行时清单在 `scripts/deps.json` 的 `runtime` 字段。

解析顺序（第一个命中即使用）：

1. `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`
2. `<工作区>/.dsh/skills`
3. `<工作区>/.zcode/skills`
4. `<工作区>/.agents/skills`
5. `<工作区>/skills`（旧布局兼容）
6. `~/.ppt-planner/skills`（`setup.py` 默认安装位置，宿主不扫描）
7. `~/.dsh/skills`
8. `~/.zcode/skills`
9. `~/.agents/skills`
10. `~/.claude/skills`

解析器同时检查关键能力，例如分支 A 选择已安装 deck 时需要 `ppt-master` 的 `templates/decks/` 下至少一个 deck；目录在但为空会标为 `incomplete`，不会当作可用。用户自带公司 `.pptx` / `.potx` 文件时给预检命令加 `--company-template-file`，不要求预装 deck。完整清单与手工解析顺序见 [references/dependencies.md](references/dependencies.md)。

## 产物与工作区

目标工作区默认取当前会话工作目录；用户指定其他目录时以用户为准。**Skill 包只读**，任务产物不写进本仓库。

```text
<工作区>/
└── projects/YYYYMMDDHHmm_主题名/
    ├── 需求调研.md
    ├── PPT规划思路.md                 # 入口①
    ├── PPT详细大纲_确认版.md           # 入口①②
    ├── 修改方案_确认版.md              # 入口③
    ├── sources/                       # 用户材料只读副本
    ├── versions/                      # 已确认稿历史版本
    ├── _draft/                        # 可选：未确认草稿
    ├── YYYYMMDDHHmm_主题名.pptx        # PPTX 分支
    ├── YYYYMMDDHHmm_主题名.html        # HTML 分支
    ├── assets/ 或 images/              # HTML 本地资源
    └── _build/<skill 名>/              # 制作工作区与内部产物
```

如果当前目录就是本 Skill 根目录（根目录含 `SKILL.md`），编排层会先请你指定工作区，而不是在 Skill 包里创建 `projects/`。

## 仓库结构

```text
ppt-planner-maker/
├── SKILL.md                 # 运行时入口与路由决策表
├── references/
│   ├── intake.md            # 需求调研
│   ├── planning.md          # 思路与逐页策划
│   ├── edit.md              # 修改/美化现有 PPTX
│   ├── production.md        # A–F 分支执行手册
│   ├── confirmation.md      # 确认、快速模式、交付后修改
│   └── dependencies.md      # 外部依赖安装、解析、许可
├── scripts/
│   ├── deps.json            # 机器可读依赖清单
│   ├── resolve_skills.py    # 依赖根目录/能力解析
│   ├── check_runtime.py     # Python 包 / 命令运行时探针
│   ├── doctor.py            # 合并两项检查的一行结论
│   ├── setup.py             # 一键安装（默认只出计划，装到私有目录并锁定版本）
│   ├── clean_deck.py        # remove unreachable OPC parts into a new output
│   └── verify_deck.py       # 成品结构检查（页数、占位残留、整页图、孤儿页、资源）
├── docs/
│   ├── install.md           # 安装与宿主发现规则
│   ├── migration.md         # 从 0.9 及旧工作区迁移
│   └── design.md            # 维护者：单一事实源与扩展方式
├── README.md / README.en.md
├── AGENTS.md                # 仓库开发约定
├── VERSION / CHANGELOG.md
├── LICENSE                  # 原创部分 CC BY-NC 4.0
└── THIRD_PARTY_NOTICES.md   # 外部依赖许可矩阵
```

`evals/` 和 `tests/` 分别为本地评测和单测目录，不随仓库分发；规则见 [docs/design.md](docs/design.md)。

## 开发与验证

以下命令在仓库根目录运行；编排层运行时请使用 `{SKILL_DIR}/scripts/...` 的绝对路径。

```bash
# 静态自检：frontmatter、相对链接、路由表一致性、禁用路径
python scripts/check_skill.py

# 运行时依赖探针（可加 --check）
python scripts/check_runtime.py --branches A,B,C,D,E,F

# 本地有 tests/ 时运行单元测试
python -B -m unittest discover -s tests
```

改路由时按 [docs/design.md](docs/design.md) 的同步清单更新 `SKILL.md`、`production.md`、`README.md`/`README.en.md`、`scripts/deps.json`、`references/dependencies.md` 和本地 `evals/cases.md`，再跑适用的检查。CI 运行静态检查；仓库不依赖第三方 Python 包。

## 常见问题

**Clone 后 AI 没发现这个 Skill？** 它不在宿主的扫描根目录里。把仓库放到 `~/.dsh/skills/ppt-planner-maker`，或在项目内建 `<工作区>/.dsh/skills/ppt-planner-maker` 联接/软链。DSH 只扫一层，别再套 `skills/`。

**提示依赖缺失？** 先跑 `python "<skill-dir>/scripts/doctor.py" --workspace <工作区> --branches A` 看结论；缺什么按“下一步”装。不想手动装时，用 `python "<skill-dir>/scripts/setup.py" --workspace <工作区> --branches A` 看计划，确认后加 `--yes` 代为安装。或把已有依赖目录用 `--skills-dir` / `PPT_PLANNER_SKILLS_DIR` 传入。不要手工猜路径。

**解析器显示 OK，构建却报 ModuleNotFoundError？** 路径 OK 不等于运行时就绪。运行 `python "<skill-dir>/scripts/check_runtime.py" --branches A`，按 `missing required` 安装 ppt-master 的 `requirements.txt`。

**我有自己的公司 `.pptx` 模板，怎么用？** 直接把模板文件路径给我，说“按这个模板做”。默认由 ppt-master 的 Edit Native PPTX 填充新内容；明确要可复用模板工作区，或 `.potx` 无法直接填充时，才用 Create Template。不要选“用现成设计模板”，那指的是 gorden 内置模板库。

**公司内部汇报算商业使用吗？** CC BY-NC 4.0 的“非商业”定义并不覆盖所有内部使用场景，正式在公司内推广前请按组织政策确认，或联系维护者取得书面授权。这不是法律意见。

**Windows 上 `python3` 没反应？** 可能只有 `python`，或 `python3` 指向 Store 占位程序。用 `python`。

**HTML 能直接发给别人吗？** 可以，但要连同项目内 `assets/`、`images/` 一起发送并保持相对路径。若用了 CDN 字体或外部图标，离线放映前请实际断网验证。

**没有公司模板能用吗？** 可以，制作路线选“从零设计”，不需要任何模板。

**必须用公司模板，但想要 HTML？** 两者冲突。公司模板路线只产出可编辑 PPTX，需要改其中一项要求。

**说“越快越好”会跳过确认吗？** 不会。它只把三份文档合并成一次确认，制作路线仍要回答；要跳过确认请说“不用确认，直接做”。“路线你定”只决定制作路线，不算快速模式。

**旧提示词里的 `skills\ppt-master` 还能用吗？** 不再推荐。依赖已外置，安装后直接用 Skill 名即可；迁移步骤见 [docs/migration.md](docs/migration.md)。

**能把 `projects/` 或成品放回仓库吗？** 不建议。仓库是 Skill 包，运行产物应留在工作区；`.gitignore` 已忽略这些路径。

## 许可

一句话：个人学习、研究、教学可用；公司内部或商业使用前，先确认是否需要维护者书面授权。

本仓库原创部分（`SKILL.md`、`references/`、`scripts/`、`docs/`、`tests/` 与根目录文档）采用 [CC BY-NC 4.0](LICENSE)：可用于个人学习、研究、教学与非营利交流，**禁止商业使用**；商业使用须事先取得维护者书面授权。

外部制作 Skill **不随本仓库分发**，按各自许可证使用：

| 依赖 | 许可证 | 商业使用 |
|---|---|---|
| `ppt-master`（含公司 deck） | MIT | 允许；公司 logo/商标权不随 MIT 授予 |
| `gorden-ppt-skill` 代码 | MIT | 允许 |
| `gorden-ppt-skill` 内置模板/素材 | 非商业许可 | **禁止**；仅限个人学习研究 |
| `html-ppt` | MIT | 允许 |
| `guizang-ppt-skill` | AGPL-3.0 | 允许；修改后分发或作为网络服务提供时须开源对应源码 |

商用自查：

| 你的用法 | 结论 |
|---|---|
| 用本 Skill 为付费客户做 PPT，或做成付费产品/课程 | **不可以**（本 Skill 为 CC BY-NC 4.0）；需书面授权 |
| 用 `ppt-master` / `html-ppt` 做商业 deck | 可以（MIT）；保留版权声明 |
| 用 `gorden-ppt-skill` 内置模板做商业 deck | **不可以**；仅限个人学习研究 |
| 用 `guizang-ppt-skill` 做商业 deck | 可以；分发修改版时遵守 AGPL |
| 把本仓库打包出售或做成付费 SaaS | **不可以**；依赖另行核对 |

完整条款见 [LICENSE](LICENSE) 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。以上不构成法律意见；正式商用前请以许可证原文为准。

## 上游与致谢

- [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)（MIT）与 [xztsummer/ppt-master](https://github.com/xztsummer/ppt-master)（定制 fork）
- [GordenSun/GordenPPTSkill](https://github.com/GordenSun/GordenPPTSkill)
- [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill)
- [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)

本仓库只维护编排层；制作能力、模板与素材的版权归各上游作者所有。


显式 --skills-dir 仅检查目标根目录，其他副本只提示；默认仅复用 drift=match 的副本，drift/unknown 则计划装入私有目录（PPT_PLANNER_HOME 可覆盖）。目标已有不同或未知版本需手动处理，不覆盖、不自动切换；项目级旧副本可能抢占，须按警告处理。执行顺序为 clone → pin → pip，requirements 取锁定后的目标副本。
