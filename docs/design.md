# 设计说明（维护者）

本仓库只维护一个编排 Skill：`ppt-planner-maker`。制作能力是外部依赖。设计目标不是“把五个 Skill 装进一个仓库”，而是让编排层可以单独安装、单独升级、单独测试。

## 一、三条边界

1. **路由层**：`SKILL.md` §四决定“哪个分支、用哪个逻辑 ID、输出什么格式”。它不写物理路径。
2. **解析层**：`scripts/deps.json` + `scripts/resolve_skills.py` 把逻辑 ID 解析成绝对根目录，并检查能力；`scripts/check_runtime.py` 再检查 Python 包与命令；`scripts/doctor.py` 把两者合成一条面向用户的就绪结论。任一层失败都是阻塞项。安装只通过用户同意后的 `scripts/setup.py --yes` 进行（默认只出计划）。
3. **委派层**：`references/production.md` 只加载选中依赖的 `SKILL.md`，传交接清单；不复制依赖内容，不改依赖文件。

运行产物属于用户工作区，不属于 Skill 包。Skill 目录在任务期间只读。

## 二、单一事实源

| 问题 | 权威位置 | 镜像/派生 |
|---|---|---|
| 选哪个分支、用哪个 Skill | `SKILL.md` §四（判定规则与决策表，其他文件只引用，不转述） | `README.md` / `README.en.md` 路由摘要 |
| 分支怎么执行 | `references/production.md` 的 A–F 小节 | — |
| 依赖的 ID、上游、分支、能力与运行时 | `scripts/deps.json` | `references/dependencies.md` 人类可读表 |
| 依赖安装、运行时、解析顺序、许可 | `references/dependencies.md` | `README` 安装段、`docs/install.md` |
| 路由期望值 | 本地 `evals/cases.md` | 评测报告 |
| 快速模式档位与确认口径 | `references/confirmation.md` §五 | `SKILL.md` 核心规则 5、`README` 快速开始、`evals/cases.md` T15/T16/T31–T33 |
| 安装与宿主发现 | `docs/install.md` | `README` 安装段 |
| 迁移 | `docs/migration.md` | `CHANGELOG.md` |

判断标准：出现冲突时，以 `SKILL.md` §四和 `scripts/deps.json` 为准；其余位置是摘要，必须跟着改。

### 改路由的同步清单

0. 若改的是路由字段（如制作路线、视觉密度），先改 `references/intake.md` 字段表与 `需求调研.md` 模板，再改下游文档。
1. 改 `SKILL.md` §四的决策表（分支、条件、Skill ID、设计依据）。
2. 改 `references/production.md` 对应分支小节的 `{skill:<id>}` 与约束。
3. 改 `README.md` 与 `README.en.md` 的路由摘要表。
4. 改 `scripts/deps.json` 的分支、能力探针与运行时清单，并同步 `references/dependencies.md`。
5. 改本地 `evals/cases.md` 的期望分支/Skill，补一条反例。
6. 跑静态检查；本地有 `tests/` 时再跑单测（该目录不随仓库分发）：

   ```bash
   python scripts/check_skill.py
   python -B -m unittest discover -s tests
   ```

6. 干跑评测（见「五、评测」），把报告写到 `evals/reports/`。

只改文档不改表、只改表不改评测，都会被 `check_skill.py` 的分支集合比较或干跑发现。

## 三、分支模型

| 分支 | 条件 | Skill ID | 输出 |
|---|---|---|---|
| A | 制作路线 = 套公司模板（已装 deck → Generate；自备 `.pptx` + 新内容 → 默认 Edit Native；可复用工作区 / `.potx` → Create Template） | `ppt-master` | 可编辑 PPTX |
| B | 制作路线 = 从零设计（用户明确） | `ppt-master` | 可编辑 PPTX |
| C | 制作路线 = 用现成设计模板（gorden 内置模板库）；或 PPTX + 具体场景命中 gorden 模板库 / “复杂豪华”版面（默认推荐，模式 A） | `gorden-ppt-skill` | 可编辑 PPTX |
| D | HTML + 常规 | `html-ppt` | HTML |
| E | HTML + 杂志风/瑞士风；仅“设计感”先确认 D/E | `guizang-ppt-skill` | HTML |
| F | 修改/美化现有 PPTX | `ppt-master` | 可编辑 PPTX |

- 分支只看制作路线、输出格式、具体场景和真实风格意图；视觉密度本身只影响版式，PPTX 的“复杂豪华”是 C 的另一条偏好信号；不看商业/个人用途。
- 制作路线没有通用默认值：未说明时先问场合、听众和想要的感觉；具体场景命中 gorden 或存在“复杂豪华”偏好时推荐 C（gorden 模式 A）；都没有时再问三选一，答“你定”按从零设计。任何公司 deck 都必须由用户指定或从本机已装 deck 中选择；用户给 `.pptx` 模板 + 新内容时默认 Edit Native，明确要可复用工作区或 `.potx` 无法直接填充时才走 Create Template。
- 分支 C 必须在需求表展示 gorden 模板的非商业许可提示；快速模式也不省略。用户自备模板不属于 C。
- 分支 E 的触发是负向敏感的：否定词、材料正文里的设计词、“复杂豪华”（HTML 场景）、“高级/好看”都不触发；仅“设计感”时先确认 D/E。PPTX 场景的“复杂豪华”按分支 C 处理。
- 分支 F 的内容/结构大改要回到入口②，不在入口③静默重构。

### gorden 模式（分支 C）

| 模式 | 能力 | 适用 |
|---|---|---|
| A 内置模板 | 保留模板的复杂排版，只换文字/原生图表数据；配色固定，不能新增版式 | 场景模板 / 复杂豪华默认 |
| C 原创简洁 | `python-pptx` 代码生成；大量留白、单页 ≤4 元素、1 主色 + 灰阶 | 用户明确接受简洁原创 |

不得用模式 C 承接场景模板效果或复杂豪华；模式 A 模板页与模式 C 原创页不混排；模板承载不了额外要求时先换模板，仍不行改走 B 或调整需求。

### 场景 → 分支 C 推荐（不硬判）

| 具体场景 | gorden 候选方向 |
|---|---|
| 党政 / 党课 / 主题党日 | `red-patriot-youth`、`red-patriot-general`、`red-teaching-*` |
| 教学 / 说课 / 课件 / 培训 | `cute-orange-class`、`thesis-novice`、`red-teaching-*` |
| 开题 / 答辩 / 课题汇报 | `thesis-novice`、`thesis-formula`、`top-thesis` |
| 述职 / 竞聘 / 晋升答辩 | `competition-speech`、`report-savior`、`report-massive-reports` |
| 年度 / 季度总结 | `minimal-business-summary`、`geometric-summary`、`report-savior` |
| 复盘 / 思维模型 | `report-massive-models`、`competition-speech`、`report-savior` |
| 数据可视化 / 经营分析 | `data-viz-deck`、`report-massive-charts`、`operations-deck` |
| 运营 / 互联网产品 | `operations-deck`、`quarterly-illust`、`premium-corp` |
| 商务提案 / 咨询 / 战略 | `minimal-business-summary`、`mckinsey-style`、`premium-corp` |
| 架构 / 流程 / 系统拓扑 | `architecture-deck`、`mckinsey-style`、`report-massive-models` |

命中只推荐 C 模式 A，并展示正好 3 个预览、“换一批”、非商业许可与能力边界；宿主无法内嵌图片时给 `preview.png` 绝对路径；明确路线和公司模板优先，用户拒绝或要求完全定制时走 B。用户只拒绝模板、没有要求模板效果时也走 B，不强行二选一；只有同时要求复杂豪华或“像现成模板那样”的效果时才按冲突处理。

## 四、依赖契约

`scripts/deps.json` 的每个条目：

```json
{
  "id": "ppt-master",
  "source": "https://github.com/xztsummer/ppt-master",
  "license": "MIT",
  "testedVersion": "0e8d92c…",
  "branches": ["A", "B", "F"],
  "capabilities": {
    "skill": { "path": "SKILL.md", "required": true },
    "decks": { "path": "templates/decks", "for": ["A"], "requireAnyChild": true }
  },
  "runtime": {
    "python": ["pptx"],
    "optionalPython": ["fitz"],
    "optionalCommands": ["soffice"],
    "install": "python -m pip install -r <ppt-master>/requirements.txt",
    "note": "…"
  },
  "install": { "type": "git", "url": "…", "targetName": "ppt-master" }
}
```

- `capabilities` 的 `path` 相对依赖根目录。
- `required: true` 表示任何使用该依赖的分支都需要。
- `for: ["A"]` 表示只在分支 A 需要；解析器按 `--branches` 判定。用户自带公司模板文件时，`--company-template-file` 只取消 `decks` / `deck-index` 的 required 标记；默认与选择已安装 deck 时仍严格检查。
- `requireAnyChild: true` 表示该目录必须至少有一个子目录；为空时能力状态为 `empty`，整体标为 `incomplete`。分支 A 的 deck 探针用它，避免把“引擎在、deck 没有”当成可用。
- `childPath` 与 `requireAnyChild` 配套：要求至少一个子目录里存在该相对路径。分支 A 用它检查 `templates/design_spec.md`，避免“有个空目录就算 deck”。
- `runtime` 由 `check_runtime.py` 读取：`python` / `optionalPython` 是 import 名，`commands` / `optionalCommands` 是 PATH 命令名，`anyCommands` 是“任一存在即可”的命令组（如浏览器），只提示不阻塞；`install` 是 pip 提示，`note` 是人类说明。缺必需项时运行时检查为 `incomplete`。检查会实际 import，不只是查 `find_spec`。
- 只有目录型依赖可用：`<root>/<id>/SKILL.md`。扁平 `<id>.md` 标为 `invalid`。
- 依赖 `status`：`ok` / `incomplete` / `missing` / `invalid`；能力 `status` 另有 `empty`。
- `testedVersion` 只记录验证过的版本，不强制用户安装同版；升级后重跑检查和评测。

解析根顺序（项目级优先于用户级）：

```text
--skills-dir / PPT_PLANNER_SKILLS_DIR
<workspace>/.dsh/skills
<workspace>/.zcode/skills
<workspace>/.agents/skills
<workspace>/skills          # 旧布局兼容
$PPT_PLANNER_HOME/skills    # 私有目录，默认 ~/.ppt-planner/skills，宿主不扫描
$DSH_HOME/skills
$ZCODE_HOME/skills
$DSH_AGENTS_HOME/skills
~/.claude/skills
```

退出码：`0` 全部 ok；`1` `--check` 下有非 ok；`2` 参数/清单错误。解析器只读，不写 Skill 目录；`--out` 是显式写文件。

## 五、评测

`evals/` 是**本地目录，不随仓库分发**（`.gitignore` 与 `.git/info/exclude` 都排除）。原因：

- 用例主要验证模型的路由判断，噪声大，不适合作为公开 CI 的硬门禁；
- 用例里包含具体业务场景和预期，公开后容易被过度拟合；
- 维护者本地干跑足够覆盖路由回归。

用例格式：

- 每条一个场景，写用户原话；
- 判定项分 `M`（must，失败即用例失败）和 `S`（should，失败记瑕疵）；
- 至少覆盖：入口①②③、A–F 六个分支、冲突拦截、负向风格词、指定 Skill 优先、只要大纲、快速模式、依赖缺失、工作区等于 Skill 根。

执行方式：

- 由独立子代理在只读模式下读取 `SKILL.md` 与必要 `references/`，只输出路由结论；禁止创建文件、禁止真正生成 PPT。
- 报告写到 `evals/reports/YYYY-MM-DD-routing.md`，记录被测 commit、用例数、M/S 通过率、误路由和残余风险。

静态检查不能替代干跑：`check_skill.py` 只能证明文档结构一致，不能证明模型会按文档路由。

## 六、`check_skill.py` 检查项

- frontmatter：`name` 为 kebab-case 且等于 `ppt-planner-maker`；`description` 非空且不超过 500 字符。
- 相对链接：`SKILL.md`、`references/*.md`、`docs/*.md`、`README*.md`、`AGENTS.md`、`THIRD_PARTY_NOTICES.md` 中的相对链接目标存在。
- 禁用路径：`SKILL.md` 与 `references/` 不出现 `{工作区}/skills`、`skills/ppt-master`、`skills/gorden-ppt-skill`、`skills/html-ppt`、`skills/guizang-ppt-skill`，也不出现 Windows 绝对路径。
- 陈旧口径：不出现 `使用性质`；旧仓库名只允许出现在 `docs/migration.md` 与 `CHANGELOG.md`。
- 路由一致性：
  - `SKILL.md` 决策表的分支集合与 Skill ID；
  - `production.md` 的 `### A.`–`### F.` 与 `- Skill：{skill:<id>}`；
  - `README.md` / `README.en.md` 路由摘要表；
  - `scripts/deps.json` 的 ID 与分支；
  - `references/dependencies.md` 的 ID；
  - `{skill:<id>}` 占位是否都有对应依赖。
- 结构：根目录 `SKILL.md` 唯一；不存在嵌套 `SKILL.md`；`VERSION` 是 semver；`CHANGELOG.md` 提到当前版本；运行目录 `projects/`、`output/`、`_build/` 不存在；`__pycache__` 出现时给出警告。
- 依赖清单：每个依赖必须有 `runtime` 对象；缺了记警告（`check_runtime.py` 无法检查）。
- 可选：本地 `evals/cases.md` 出现时必须只用 A–F 分支。

## 七、新增一个制作 Skill

1. 在 `scripts/deps.json` 增加条目：ID、上游、许可证、`branches`、能力探针、运行时清单（`runtime`）、安装信息。
2. 在 `SKILL.md` §四增加分支行（或扩展现有分支），只写逻辑 ID。
3. 在 `references/production.md` 增加对应分支手册，路径用 `{skill:<id>}`。
4. 在 `references/dependencies.md` 增加安装、能力、许可条目；在 `THIRD_PARTY_NOTICES.md` 增加许可证行。
5. 在 `README.md` 与 `README.en.md` 的摘要表增加分支行。
6. 在本地 `evals/cases.md` 增加正例和误触发反例。
7. 跑 `check_skill.py`、单测和干跑；确认新增依赖缺失时会阻塞而不是误路由。

## 八、升级一个依赖

1. 在依赖目录 checkout/pull 到目标版本。
2. 跑 `resolve_skills.py`，确认 `status` 与 `missingRequired`；再跑 `check_runtime.py`，确认运行时包与命令。
3. 更新 `deps.json` 的 `testedVersion`、必要的 `capabilities` 与 `runtime`。
4. 跑 `check_skill.py`、单测、干跑；需要时做一条真实端到端。
5. 不修改依赖源码；能力不兼容时改本仓库的适配层或回退版本。

## 九、已知限制

- 路由是自然语言规则，不是可执行代码；静态检查只能保证结构一致，模型行为要靠干跑。
- 能力探针只检查路径、目录是否非空，以及 `childPath` 指定的单个文件是否存在，不检查依赖内部版本或接口语义。
- 运行时探针只检查 import 是否成功、命令是否存在，不检查版本、ABI 或接口兼容；浏览器能力不检查。
- 已实测的边界：扁平 `<id>.md` 不会遮蔽目录型 bundle；`check_runtime.py` 不会向 Skill 包写 `__pycache__`；`ppt-master` 的版本优先从 `VERSION`、`manifest.json`，再回退到 `SKILL.md` frontmatter 的 `metadata.version`。
- `soffice` 只查 PATH 与几个常见安装路径；自定义安装位置需要在命令中显式使用。
- 公司 deck 不随本 Skill 分发；分支 A 选择已安装 deck 时需要用户已装 fork 自带的 deck 或自备 deck，空目录按 `incomplete` 阻塞；用户自带公司模板文件时显式使用 `--company-template-file`。
- 宿主发现规则各不相同；本仓库只保证目录形态符合 DSH 的一层扫描约定。
- 预检与 doctor 只读；安装仅通过用户同意后的 `setup.py --yes`（git clone 到私有目录并锁定 testedVersion + pip），系统级组件只提示；不自动更新依赖；gorden 的 `apply_update.py` 被有意替换为只读的 `check_update.py`。路由不按用途分流，不替用户判断 gorden 模板的商用授权（维护者决策，2026-11-05）。
- `verify_deck.py` 只查结构（可见页数、占位残留、整页图、孤儿页、本地资源），不查排版；内容适配和视觉检查仍靠渲染后逐页核对。
- 许可证边界（维护者决策，2026-10-26）：原创部分维持 CC BY-NC 4.0，不加内部使用豁免；公司内部/商业使用按许可原文需维护者书面授权，README 保留白话提示，编排层不替用户判断。
- 浏览器探测覆盖 Edge / Chrome / Firefox 的常见安装路径（`anyCommands`），任一命中即可；探测不到只提示，不阻塞构建。
- `evals/` 本地化意味着公开 CI 不覆盖路由行为；这是有意的取舍。

`clean_deck.py` 是显式输出的新成品清理器：从包根关系遍历删除不可达部件，同步 Content_Types、sections 和应用属性；保留其余可达部件字节，拒绝覆盖输入。清理后重新 verify 和视觉检查；verify 的含占位孤儿为 FAIL，其他孤儿为 WARN；HTML 递归检查本地 CSS、@import 和 url，防循环。
