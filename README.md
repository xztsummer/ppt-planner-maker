# ppt-planner-maker

**中文** | [English](README.en.md)

一个**只做编排**的 Agent Skill：把 PPT 需求变成确认过的逐页方案，再路由到四个外部制作 Skill，产出可编辑 PPTX 或 HTML。

> 本仓库不含制作引擎。`ppt-master`、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill` 需要单独安装，见 [docs/install.md](docs/install.md) 与 [references/dependencies.md](references/dependencies.md)。

## 它做什么

- **三个入口**：从主题规划大纲、按已有大纲/材料制作、修改或美化现有 PPTX。
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

项目级（Windows 目录联接，无需管理员）：

```bat
mklink /J "<工作区>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

macOS / Linux 项目级软链：

```bash
ln -s /path/to/ppt-planner-maker <工作区>/.dsh/skills/ppt-planner-maker
```

DSH 只扫描一层 `<root>/<name>/SKILL.md`；不要把本仓库再套一层 `skills/` 目录，否则不会被发现。Claude Code 等宿主同理，放进其 `skills/` 根目录即可。

### 2. 安装制作依赖

至少安装当前任务需要的分支依赖；四个全装也可以。`<skills-dir>` 指任一被宿主扫描的 skills 根目录。

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

### 3. 验证

```bash
python scripts/resolve_skills.py --check --branches A,B,C,D,E,F
```

全部 `OK` 即就绪。Windows 上如果 `python3` 指向 Microsoft Store 占位程序，改用 `python`。缺失项会打印安装命令；详细规则见 [references/dependencies.md](references/dependencies.md)。

## 快速开始

默认流程（推荐第一次使用）：

> 帮我做一份 15 页的《可信数据空间》汇报 PPT，听众是客户，讲解 30 分钟，风格专业简洁。

三个入口：

- **① 规划大纲**：只有主题或零散材料，先调研、对齐思路，再逐页策划。
- **② 已有大纲制作**：保留原大纲顺序和原意，补齐逐页信息后制作；PDF/截图/旧 PPTX 也可当材料。
- **③ 修改/美化现有 PPTX**：保留原版式增量编辑，或保留内容重新设计版式；不覆盖源文件。

只要大纲：

> 先帮我出一版逐页大纲看看，别做 PPT。

赶时间时可以明确授权快速模式：

> 一次确认就行。

> 不用确认，直接做。

快速模式仍会检查依赖、展示 gorden 许可提示、执行下游阻塞检查和成品验证；主题仍需你提供，缺失数据不会被编造。规则见 [references/confirmation.md](references/confirmation.md)。

## 路由规则（摘要）

| 分支 | 场景 | 制作 Skill | 输出格式 |
|---|---|---|---|
| A | 必须使用公司模板 | `ppt-master` | 可编辑 PPTX |
| B | 非公司模板，专业简洁 | `ppt-master` | 可编辑 PPTX |
| C | 非公司模板，复杂豪华（内容偏好默认） | `gorden-ppt-skill` | 可编辑 PPTX |
| D | 常规 HTML | `html-ppt` | HTML |
| E | 杂志风、瑞士风或明确的设计感 HTML | `guizang-ppt-skill` | HTML |
| F | 修改/美化现有 PPTX | `ppt-master` | 可编辑 PPTX |

权威规则在 [SKILL.md](SKILL.md) §四；这里只是摘要。

硬约束：

- **公司模板只出可编辑 PPTX**。用户同时明确要求公司模板和 HTML 时，先请其改一项，不静默改需求。
- **gorden 内置模板仅限个人学习研究**。走分支 C 时，需求表会写一行“模板许可提示：内置模板仅限个人学习研究，商用需自行取得授权”；商用前请自行取得模板作者授权。
- **guizang 只按真实风格意图触发**。否定说法、材料正文里的设计词、只说“复杂豪华”或“高级/好看”都不触发。
- **HTML 不是 PowerPoint**。不要把 HTML 改名成 `.pptx`，也不要承诺它可编辑。
- **依赖缺失时停止**。给出具体 ID、缺失能力和安装命令，不猜测路径、不切换其他制作 Skill。

## 依赖解析

制作 Skill 不随本包分发。进入制作前运行：

```bash
python scripts/resolve_skills.py --workspace <工作区> --branches <选中分支> --json
```

解析顺序（第一个命中即使用）：

1. `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`
2. `<工作区>/.dsh/skills`
3. `<工作区>/.agents/skills`
4. `<工作区>/skills`（旧布局兼容）
5. `~/.dsh/skills`
6. `~/.agents/skills`
7. `~/.claude/skills`

解析器同时检查关键能力，例如分支 A 需要 `ppt-master` 的 `templates/decks/中国电子云`；目录在但能力缺失会标为 `incomplete`，不会当作可用。完整清单与手工解析顺序见 [references/dependencies.md](references/dependencies.md)。

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
│   └── resolve_skills.py    # 依赖根目录/能力解析
├── docs/
│   ├── install.md           # 安装与宿主发现规则
│   ├── migration.md         # 从 0.9 及旧工作区迁移
│   └── design.md            # 维护者：单一事实源与扩展方式
├── tests/                   # Python 单元测试
├── README.md / README.en.md
├── AGENTS.md                # 仓库开发约定
├── VERSION / CHANGELOG.md
├── LICENSE                  # 原创部分 CC BY-NC 4.0
└── THIRD_PARTY_NOTICES.md   # 外部依赖许可矩阵
```

`evals/` 为本地路由评测目录，不随仓库分发；规则见 [docs/design.md](docs/design.md)。

## 开发与验证

```bash
# 静态自检：frontmatter、相对链接、路由表一致性、禁用路径
python scripts/check_skill.py

# 解析器与自检的单元测试
python -m unittest discover -s tests
```

改路由时按 [docs/design.md](docs/design.md) 的同步清单更新 `SKILL.md`、`production.md`、README 和本地 `evals/cases.md`，再跑上面的检查。CI 可选；仓库不依赖第三方 Python 包。

## 常见问题

**Clone 后 AI 没发现这个 Skill？** 它不在宿主的扫描根目录里。把仓库放到 `~/.dsh/skills/ppt-planner-maker`，或在项目内建 `<工作区>/.dsh/skills/ppt-planner-maker` 联接/软链。DSH 只扫一层，别再套 `skills/`。

**提示依赖缺失？** 运行 `python scripts/resolve_skills.py --workspace <工作区> --branches A`，按输出的 `install` 安装；或把已有依赖目录用 `--skills-dir` / `PPT_PLANNER_SKILLS_DIR` 传入。不要手工猜路径。

**Windows 上 `python3` 没反应？** 可能只有 `python`，或 `python3` 指向 Store 占位程序。用 `python`。

**HTML 能直接发给别人吗？** 可以，但要连同项目内 `assets/`、`images/` 一起发送并保持相对路径。若用了 CDN 字体或外部图标，离线放映前请实际断网验证。

**必须用公司模板，但想要 HTML？** 两者冲突。公司模板路线只产出可编辑 PPTX，需要改其中一项要求。

**旧提示词里的 `skills\ppt-master` 还能用吗？** 不再推荐。依赖已外置，安装后直接用 Skill 名即可；迁移步骤见 [docs/migration.md](docs/migration.md)。

**能把 `projects/` 或成品放回仓库吗？** 不建议。仓库是 Skill 包，运行产物应留在工作区；`.gitignore` 已忽略这些路径。

## 许可

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
