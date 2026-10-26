# 设计说明（维护者）

本仓库只维护一个编排 Skill：`ppt-planner-maker`。制作能力是外部依赖。设计目标不是“把五个 Skill 装进一个仓库”，而是让编排层可以单独安装、单独升级、单独测试。

## 一、三条边界

1. **路由层**：`SKILL.md` §四决定“哪个分支、用哪个逻辑 ID、输出什么格式”。它不写物理路径。
2. **解析层**：`scripts/deps.json` + `scripts/resolve_skills.py` 把逻辑 ID 解析成绝对根目录，并检查能力。解析失败是阻塞项。
3. **委派层**：`references/production.md` 只加载选中依赖的 `SKILL.md`，传交接清单；不复制依赖内容，不改依赖文件。

运行产物属于用户工作区，不属于 Skill 包。Skill 目录在任务期间只读。

## 二、单一事实源

| 问题 | 权威位置 | 镜像/派生 |
|---|---|---|
| 选哪个分支、用哪个 Skill | `SKILL.md` §四决策表（带 `分支` 列） | `README.md` / `README.en.md` 路由摘要 |
| 分支怎么执行 | `references/production.md` 的 A–F 小节 | — |
| 依赖的 ID、上游、分支、能力 | `scripts/deps.json` | `references/dependencies.md` 人类可读表 |
| 依赖安装、解析顺序、许可 | `references/dependencies.md` | `README` 安装段、`docs/install.md` |
| 路由期望值 | 本地 `evals/cases.md` | 评测报告 |
| 安装与宿主发现 | `docs/install.md` | `README` 安装段 |
| 迁移 | `docs/migration.md` | `CHANGELOG.md` |

判断标准：出现冲突时，以 `SKILL.md` §四和 `scripts/deps.json` 为准；其余位置是摘要，必须跟着改。

### 改路由的同步清单

1. 改 `SKILL.md` §四的决策表（分支、条件、Skill ID、设计依据）。
2. 改 `references/production.md` 对应分支小节的 `{skill:<id>}` 与约束。
3. 改 `README.md` 与 `README.en.md` 的路由摘要表。
4. 改本地 `evals/cases.md` 的期望分支/Skill，补一条反例。
5. 跑：

   ```bash
   python scripts/check_skill.py
   python -m unittest discover -s tests
   ```

6. 干跑评测（见「五、评测」），把报告写到 `evals/reports/`。

只改文档不改表、只改表不改评测，都会被 `check_skill.py` 的分支集合比较或干跑发现。

## 三、分支模型

| 分支 | 条件 | Skill ID | 输出 |
|---|---|---|---|
| A | 必须使用公司模板 | `ppt-master` | 可编辑 PPTX |
| B | 非公司模板 + 专业简洁 | `ppt-master` | 可编辑 PPTX |
| C | 非公司模板 + 复杂豪华（默认） | `gorden-ppt-skill` | 可编辑 PPTX |
| D | 非公司模板 + 常规 HTML | `html-ppt` | HTML |
| E | 非公司模板 + 杂志风/瑞士风/设计感 HTML | `guizang-ppt-skill` | HTML |
| F | 修改/美化现有 PPTX | `ppt-master` | 可编辑 PPTX |

- 分支只看模板要求、输出格式、内容偏好和真实风格意图；不看商业/个人用途。
- 分支 C 必须在需求表展示 gorden 模板的非商业许可提示；快速模式也不省略。
- 分支 E 的触发是负向敏感的：否定词、材料正文里的设计词、“复杂豪华”“高级/好看”都不触发。
- 分支 F 的内容/结构大改要回到入口②，不在入口③静默重构。

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
    "deck:中国电子云": { "path": "templates/decks/中国电子云", "for": ["A"] }
  },
  "install": { "type": "git", "url": "…", "targetName": "ppt-master" }
}
```

- `capabilities` 的 `path` 相对依赖根目录。
- `required: true` 表示任何使用该依赖的分支都需要。
- `for: ["A"]` 表示只在分支 A 需要；解析器按 `--branches` 判定。
- 只有目录型依赖可用：`<root>/<id>/SKILL.md`。扁平 `<id>.md` 标为 `invalid`。
- `status`：`ok` / `incomplete` / `missing` / `invalid`。
- `testedVersion` 只记录验证过的版本，不强制用户安装同版；升级后重跑检查和评测。

解析根顺序（项目级优先于用户级）：

```text
--skills-dir / PPT_PLANNER_SKILLS_DIR
<workspace>/.dsh/skills
<workspace>/.agents/skills
<workspace>/skills          # 旧布局兼容
$DSH_HOME/skills
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
- 结构：根目录 `SKILL.md` 唯一；不存在嵌套 `SKILL.md`；`VERSION` 是 semver；`CHANGELOG.md` 提到当前版本；运行目录 `projects/`、`output/`、`_build/` 不存在。
- 可选：本地 `evals/cases.md` 出现时必须只用 A–F 分支。

## 七、新增一个制作 Skill

1. 在 `scripts/deps.json` 增加条目：ID、上游、许可证、`branches`、能力探针、安装信息。
2. 在 `SKILL.md` §四增加分支行（或扩展现有分支），只写逻辑 ID。
3. 在 `references/production.md` 增加对应分支手册，路径用 `{skill:<id>}`。
4. 在 `references/dependencies.md` 增加安装、能力、许可条目；在 `THIRD_PARTY_NOTICES.md` 增加许可证行。
5. 在 `README.md` 与 `README.en.md` 的摘要表增加分支行。
6. 在本地 `evals/cases.md` 增加正例和误触发反例。
7. 跑 `check_skill.py`、单测和干跑；确认新增依赖缺失时会阻塞而不是误路由。

## 八、升级一个依赖

1. 在依赖目录 checkout/pull 到目标版本。
2. 跑 `resolve_skills.py`，确认 `status` 与 `missingRequired`。
3. 更新 `deps.json` 的 `testedVersion` 与必要的 `capabilities`。
4. 跑 `check_skill.py`、单测、干跑；需要时做一条真实端到端。
5. 不修改依赖源码；能力不兼容时改本仓库的适配层或回退版本。

## 九、已知限制

- 路由是自然语言规则，不是可执行代码；静态检查只能保证结构一致，模型行为要靠干跑。
- 能力探针只检查路径存在，不检查依赖内部版本或接口语义。
- 宿主发现规则各不相同；本仓库只保证目录形态符合 DSH 的一层扫描约定。
- 本 Skill 不自动安装依赖、不自动更新依赖，也不替用户判断 gorden 模板的商用授权。
- `evals/` 本地化意味着公开 CI 不覆盖路由行为；这是有意的取舍。
