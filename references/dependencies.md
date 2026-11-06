# 外部制作 Skill 依赖

本 Skill 只做调研、策划、确认和路由，**不包含任何制作引擎**。四个制作 Skill 按需安装到宿主可扫描的 skills 根目录；路由层只引用逻辑 ID，物理路径由 `scripts/resolve_skills.py` 解析。

## 依赖清单

| ID | 用途 | 适用分支 | 上游 | 已测版本 | 许可 |
|---|---|---|---|---|---|
| `ppt-master` | 公司模板 PPTX、自由设计 PPTX、原生编辑、美化 | A / B / F | [xztsummer/ppt-master](https://github.com/xztsummer/ppt-master) | `bc72031`（v6.8.0，fork main，2026-11-06） | MIT |
| `gorden-ppt-skill` | 中文内置模板 PPTX（复杂豪华） | C | [GordenSun/GordenPPTSkill](https://github.com/GordenSun/GordenPPTSkill) | 1.0.20（`7d4a61c`，2026-06-22） | MIT（代码）/ 非商业（内置模板） |
| `html-ppt` | 常规 HTML 演示文稿 | D | [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) | `fd16290`（main，2026-09-14） | MIT |
| `guizang-ppt-skill` | 杂志风 / 瑞士风 HTML 演示文稿 | E | [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) | `93d21bf`（main，2026-10-30） | AGPL-3.0 |

> `ppt-master` **必须使用上表中的 fork**：它定期同步 `hugohe3/ppt-master`（当前 v6.8.0），并新增了中国电子云、中国电信、中汽研 deck。分支 A 选择已安装 deck 时需要 `templates/decks/` 下至少一个 deck；换成上游原版会缺失 deck 机制与这三套模板。用户自带 `.pptx` / `.potx` 模板文件时不需要预装 deck，预检显式加 `--company-template-file`。

> `gorden-ppt-skill` 的“复杂豪华”来自模式 A 内置模板；模式 C 原创是简洁兜底，不能承接复杂豪华。分支 C 的触发与模式选择见 `SKILL.md` §四与 [`production.md`](production.md) 分支 C。

机器可读清单见 [`../scripts/deps.json`](../scripts/deps.json)；改依赖时以该文件为准，并同步本表。

## 安装

**推荐用 `setup.py`（见「缺失时怎么办」）**：装到私有目录 `~/.ppt-planner/skills`（`PPT_PLANNER_HOME` 可覆盖）。宿主不扫描它，只有本编排 Skill 会响应“做 PPT”；制作 Skill 由编排层按绝对路径加载，无需被宿主发现。宿主限制读取用户目录时，用 `--skills-dir` 指定工作区内目录。

手动安装时，`<skills-dir>` 可以是私有目录，也可以是宿主扫描的根目录（此时宿主可能绕过编排层直接调用，`doctor.py` 会提示）。常见选择：

- DSH 用户级：`~/.dsh/skills`
- DSH 项目级：`<工作区>/.dsh/skills`
- ZCode 用户级：`~/.zcode/skills`
- ZCode 项目级：`<工作区>/.zcode/skills`
- Claude Code：`~/.claude/skills`
- 其他宿主：按其 skills 目录约定

只安装当前任务需要的依赖即可；四个全装也可以。

```bash
# 分支 A / B / F 必需（公司模板必须用此 fork）
git clone https://github.com/xztsummer/ppt-master.git <skills-dir>/ppt-master

# 分支 C 必需
git clone https://github.com/GordenSun/GordenPPTSkill.git <skills-dir>/gorden-ppt-skill

# 分支 D 必需
git clone https://github.com/lewislulu/html-ppt-skill.git <skills-dir>/html-ppt

# 分支 E 必需
git clone https://github.com/op7418/guizang-ppt-skill.git <skills-dir>/guizang-ppt-skill
```

安装位置也可以不放进宿主扫描目录，而是集中放在自定义目录，再通过环境变量传给解析器：

```bash
# Windows PowerShell
$env:PPT_PLANNER_SKILLS_DIR = "D:\path\to\ppt-skills"
# macOS / Linux
export PPT_PLANNER_SKILLS_DIR="$HOME/path/to/ppt-skills"
```

该变量支持多个目录，Windows 用 `;`、macOS/Linux 用 `:` 分隔。`--skills-dir` 参数优先级更高，可重复传入。

### 安装本 Skill

把本仓库放到宿主的扫描根目录下，目录名建议与 Skill 名一致：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.dsh/skills/ppt-planner-maker
```

项目级安装可用目录联接（Windows，无需管理员）：

```bat
mklink /J "<工作区>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

macOS / Linux 使用软链：

```bash
ln -s /path/to/ppt-planner-maker <工作区>/.dsh/skills/ppt-planner-maker
```

DSH 的技能发现只扫描一层：`<root>/<name>/SKILL.md` 或 `<root>/<name>.md`。因此**不要把本仓库再套一层 `skills/` 目录**，否则不会被发现。

## 解析顺序

`scripts/resolve_skills.py` 按以下顺序查找同名目录，第一个命中即使用，其余记录为 `shadowed`：

| 优先级 | 来源 | 路径 |
|---|---|---|
| 1 | 显式参数 / 环境变量 | `--skills-dir`、`PPT_PLANNER_SKILLS_DIR` |
| 2 | 项目 DSH | `<工作区>/.dsh/skills` |
| 3 | 项目 ZCode | `<工作区>/.zcode/skills` |
| 4 | 项目 Agents | `<工作区>/.agents/skills` |
| 5 | 旧工作区兼容 | `<工作区>/skills` |
| 6 | 私有目录 | `$PPT_PLANNER_HOME/skills`（默认 `~/.ppt-planner/skills`，宿主不扫描） |
| 7 | 用户 DSH | `$DSH_HOME/skills`（默认 `~/.dsh/skills`） |
| 8 | 用户 ZCode | `$ZCODE_HOME/skills`（默认 `~/.zcode/skills`） |
| 9 | 用户 Agents | `$DSH_AGENTS_HOME/skills`（默认 `~/.agents/skills`） |
| 10 | Claude 用户级 | `~/.claude/skills` |

项目级优先于用户级，便于同一台机器上不同项目锁定不同版本。只接受**目录型**依赖（`<id>/SKILL.md`）；只有扁平 `<id>.md` 时标记为 `invalid`，因为制作引擎需要自己的 `templates/`、`scripts/`、`assets/` 等同级资源。

## 能力探针

解析器不只看 `SKILL.md` 是否存在，还会检查关键能力：

| ID | 必需 | 分支专属 |
|---|---|---|
| `ppt-master` | `SKILL.md`、`workflows/routing.md`、`scripts/`、`requirements.txt` | 分支 A 选择已安装 deck：`templates/decks/` 下至少一个 deck，且该 deck 含 `templates/design_spec.md`；`templates/decks/decks_index.json` 存在。用户自带公司模板文件并传 `--company-template-file` 时，这两项只探测、不阻塞 |
| `gorden-ppt-skill` | `SKILL.md`、`manifest.json`、`templates/`、`templates/INDEX.md`、`scripts/build_pptx.py` | — |
| `html-ppt` | `SKILL.md`、`assets/themes`、`templates/` | — |
| `guizang-ppt-skill` | `SKILL.md`、`assets/`、`references/` | — |

`requireAnyChild` 的能力状态：`ok`（目录存在且至少一个子目录）、`empty`（目录存在但没有符合条件的子目录）、`missing`（路径不存在）。分支 A 的 `decks` 还设置 `childPath`，要求至少一个子目录里存在 `templates/design_spec.md`；`deck-index` 单独检查 `decks_index.json`。`--company-template-file` 只适用于用户自带 `.pptx` / `.potx` 文件，会取消这两项的 required 标记；默认及选择已安装 deck 时仍必须通过。

`status` 取值：

- `ok`：依赖存在且所需能力齐全。
- `incomplete`：目录存在，但缺少当前分支必需的某个能力。
- `missing`：所有根目录都没有该依赖。
- `invalid`：只找到扁平 `.md`，或不是有效的目录型 Skill。

## 运行时依赖

路径探针回答“装没装”，不回答“能不能跑”。分支确定后同时运行：

```text
python "{SKILL_DIR}/scripts/doctor.py" --workspace {工作区} --branches {选中分支} --brief
```

`doctor.py` 只读，合并路径解析与运行时检查；需要单独看某一层时再跑 `resolve_skills.py` / `check_runtime.py`。`--brief` 输出一行摘要；需要排查时用 `--json`。本文件中的 `{SKILL_DIR}` 指本 Skill 的 `SKILL.md` 所在绝对目录，不是当前工作目录。

| ID | 必需 Python 包 | 可选 | 命令 | 说明 |
|---|---|---|---|---|
| `ppt-master` | PyYAML、python-pptx、XlsxWriter、skia-pathops、uharfbuzz | edge-tts、PyMuPDF | `soffice`（可选） | PPTX 构建；`soffice` 用于 `.ppt` 转换与视觉预览 |
| `gorden-ppt-skill` | python-pptx | — | — | 编排层只跑只读的 `scripts/check_update.py`，不执行 `apply_update.py` |
| `html-ppt` | — | — | 浏览器任一（Edge/Chrome/Firefox） | 视觉检查用；`anyCommands` 探测常见安装路径，缺失只提示不阻塞构建 |
| `guizang-ppt-skill` | — | — | 浏览器任一（Edge/Chrome/Firefox） | 视觉检查用；离线放映需先验证字体/图标 |

安装：

```bash
# 分支 A / B / F
python -m pip install -r <skills-dir>/ppt-master/requirements.txt

# 分支 C
python -m pip install python-pptx
```

- `requirements.txt` 里的 `edge-tts`、`PyMuPDF` 是可选能力；后者是 AGPL-3.0，分发前先看其许可。
- `skia-pathops`、`uharfbuzz` 在部分平台需要编译工具；过新的 Python 可能缺少可用 wheel，建议改用 3.11/3.12 等带 wheel 的版本；`setup.py` 在 pip 失败时会给出这条提示。
- Windows 上 `soffice` 常不在 PATH，脚本会尝试 `C:\Program Files\LibreOffice\program\soffice.exe` 等常见位置。
- gorden 入口要求先跑会改写安装的 `apply_update.py`；为保持锁定版本，编排层改跑只读的 `check_update.py`，有新版本时告知用户，同意后才更新（见 production.md 分支 C）。无网时如实记录并继续，不假装已更新。
- guizang 的品牌色主题需要 node（`scripts/gz-theme.mjs`），只用预设主题时不需要。
- 运行时检查会实际 `import` 每个 Python 包（不是只查 `find_spec`），因此缺 DLL、初始化失败等问题会被发现；但它不验证版本、ABI 或接口兼容，也不检查浏览器。`OK` 不代表成品已验证。

## 缺失时怎么办

1. 运行 doctor 看结论：

   ```text
   python "{SKILL_DIR}/scripts/doctor.py" --workspace {工作区} --branches {选中分支} --brief
   ```

   需要单独排查某一层时再跑 `resolve_skills.py` / `check_runtime.py`（都支持 `--brief` / `--json`）。
2. 按输出的“下一步”安装；或向用户索取已有的安装位置，用 `--skills-dir` 传入。安装目标可以是 `~/.dsh/skills`、`~/.zcode/skills` 或工作区下的 `.dsh/.zcode/.agents/skills`，选宿主实际扫描的那个。
3. 用户同意后代为安装：先 `python "{SKILL_DIR}/scripts/setup.py" --workspace {工作区} --branches {选中分支}` 看计划，用户确认后加 `--yes` 执行（git clone 到私有目录并锁定 testedVersion 的 commit，`--latest` 跳过锁定；pip 装缺包）。系统级组件（LibreOffice、浏览器）只提示不代装；安装目标在 Skill 包内会被拒绝。
4. 安装后重跑 doctor；全部 `ok` 再进入制作。
5. **不要**改用其他制作 Skill、不要把路径猜成 `skills/<id>`、不要从别处复制一份来路不明的引擎。依赖缺失属于阻塞项，写进执行记录并告知用户。未经用户同意，不得执行任何安装。

## `{skill:<id>}` 占位

`production.md` 中的 `{skill:<id>}` 表示解析结果里的绝对根目录。例如：

```text
{skill:ppt-master}/templates/decks/<deck 名称>
```

解析器输出中的 `root` 字段即该值；不要在正文里写死工作区相对路径或 `~/.dsh/skills` 之类的固定位置。

## 手工解析（脚本不可用时）

如果宿主不能执行 Python，按「解析顺序」逐个检查以下文件是否存在，并记录实际路径：

```text
<root>/<id>/SKILL.md
```

同时检查「能力探针」中当前分支需要的能力路径。只记录找到的第一个根目录；同名目录出现在多个根目录时，按优先级取第一个，并在执行记录中写明 `shadowed`。

## 版本与更新

- 依赖各自升级：`gorden-ppt-skill` 的更新脚本、`guizang-ppt-skill` 的更新检查、`ppt-master` 的 fork 更新，都由其自身流程负责；编排层不在任务中自动改写依赖文件。
- `deps.json` 的 `testedVersion` 记录本仓库验证过的版本/提交，`setup.py` 默认锁定到它；`doctor.py` 在已装版本不一致时只提示、不阻塞，读不到版本时显示“未知”。
- 手动安装时可 checkout 对应 commit；不要修改依赖源码来适配本 Skill。

## 许可与商用边界

| 依赖 | 许可 | 商用边界 |
|---|---|---|
| `ppt-master`（含公司 deck） | MIT | 允许；保留其版权与许可声明。公司 logo、品牌素材的商标权不随 MIT 授予。 |
| `gorden-ppt-skill` 代码 | MIT | 允许。 |
| `gorden-ppt-skill` 内置模板与预览素材 | 非商业许可，见其 `NOTICE.md` | **禁止商用**；仅限个人学习与研究。商用需自行取得模板作者授权。 |
| `html-ppt` | MIT | 允许；保留版权声明。 |
| `guizang-ppt-skill` | AGPL-3.0 | 允许商用；修改后分发或作为网络服务提供时，须按 AGPL 开源对应源码。 |

本编排 Skill 自身为 CC BY-NC 4.0（见根目录 [`LICENSE`](../LICENSE)），与上述依赖许可相互独立。生成物的版权与可用范围取决于所用模板、素材和模型服务条款，不自动适用本仓库许可。

## 旧工作区兼容

旧版把四个制作 Skill 放在 `<工作区>/skills/` 下；解析顺序第 5 项仍支持这种布局。迁移到新布局后，建议用 `setup.py` 把依赖装到私有目录，并删除旧的 `skills/` 副本，避免同名依赖出现两个版本。


显式 --skills-dir 仅检查目标根目录，其他副本只提示；默认仅复用 drift=match 的副本，drift/unknown 则计划装入私有目录（PPT_PLANNER_HOME 可覆盖）。目标已有不同或未知版本需手动处理，不覆盖、不自动切换；项目级旧副本可能抢占，须按警告处理。执行顺序为 clone → pin → pip，requirements 取锁定后的目标副本。

PyYAML 无 wheel 时，setup.py 仅向 pip 子进程传 PYYAML_FORCE_LIBYAML=0 以使用纯 Python 构建；requirements 安装失败也提供 PyYAML、skia-pathops、uharfbuzz 提示，不修改全局环境。
