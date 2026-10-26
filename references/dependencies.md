# 外部制作 Skill 依赖

本 Skill 只做调研、策划、确认和路由，**不包含任何制作引擎**。四个制作 Skill 按需安装到宿主可扫描的 skills 根目录；路由层只引用逻辑 ID，物理路径由 `scripts/resolve_skills.py` 解析。

## 依赖清单

| ID | 用途 | 适用分支 | 上游 | 已测版本 | 许可 |
|---|---|---|---|---|---|
| `ppt-master` | 公司模板 PPTX、自由设计 PPTX、原生编辑、美化 | A / B / F | [xztsummer/ppt-master](https://github.com/xztsummer/ppt-master) | `0e8d92c`（fork main，2026-10-21） | MIT |
| `gorden-ppt-skill` | 中文内置模板 PPTX（复杂豪华） | C | [GordenSun/GordenPPTSkill](https://github.com/GordenSun/GordenPPTSkill) | 1.0.20（`7d4a61c`，2026-06-22） | MIT（代码）/ 非商业（内置模板） |
| `html-ppt` | 常规 HTML 演示文稿 | D | [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) | `fd16290`（main，2026-09-14） | MIT |
| `guizang-ppt-skill` | 杂志风 / 瑞士风 HTML 演示文稿 | E | [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) | `c91369c`（main，2026-08-07） | AGPL-3.0 |

> `ppt-master` **必须使用上表中的 fork**：它基于 `hugohe3/ppt-master` v6.7.2，新增了中国电子云、中国电信、中汽研 deck。分支 A 依赖 `templates/decks/中国电子云`；换成上游原版会缺失公司模板。

机器可读清单见 [`../scripts/deps.json`](../scripts/deps.json)；改依赖时以该文件为准，并同步本表。

## 安装

`<skills-dir>` 指本机任一被宿主扫描的 skills 根目录。常见选择：

- DSH 用户级：`~/.dsh/skills`
- DSH 项目级：`<工作区>/.dsh/skills`
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
| 3 | 项目 Agents | `<工作区>/.agents/skills` |
| 4 | 旧工作区兼容 | `<工作区>/skills` |
| 5 | 用户 DSH | `$DSH_HOME/skills`（默认 `~/.dsh/skills`） |
| 6 | 用户 Agents | `$DSH_AGENTS_HOME/skills`（默认 `~/.agents/skills`） |
| 7 | Claude 用户级 | `~/.claude/skills` |

项目级优先于用户级，便于同一台机器上不同项目锁定不同版本。只接受**目录型**依赖（`<id>/SKILL.md`）；只有扁平 `<id>.md` 时标记为 `invalid`，因为制作引擎需要自己的 `templates/`、`scripts/`、`assets/` 等同级资源。

## 能力探针

解析器不只看 `SKILL.md` 是否存在，还会检查关键能力：

| ID | 必需 | 分支专属 |
|---|---|---|
| `ppt-master` | `SKILL.md`、`workflows/routing.md`、`scripts/` | 分支 A：`templates/decks/中国电子云` |
| `gorden-ppt-skill` | `SKILL.md`、`manifest.json`、`templates/`、`templates/INDEX.md`、`scripts/build_pptx.py` | — |
| `html-ppt` | `SKILL.md`、`assets/themes`、`templates/` | — |
| `guizang-ppt-skill` | `SKILL.md`、`assets/`、`references/` | — |

`status` 取值：

- `ok`：依赖存在且所需能力齐全。
- `incomplete`：目录存在，但缺少当前分支必需的某个能力。
- `missing`：所有根目录都没有该依赖。
- `invalid`：只找到扁平 `.md`，或不是有效的目录型 Skill。

## 缺失时怎么办

1. 运行解析器，确认具体缺的是哪个 ID 或哪个能力：

   ```text
   python scripts/resolve_skills.py --workspace {工作区} --branches A --json
   ```

2. 按输出的 `install` 提示安装；或向用户索取已有的安装位置，用 `--skills-dir` 传入。
3. 安装后重跑解析器；`status` 为 `ok` 再进入制作。
4. **不要**改用其他制作 Skill、不要把路径猜成 `skills/<id>`、不要从别处复制一份来路不明的引擎。依赖缺失属于阻塞项，写进执行记录并告知用户。

## `{skill:<id>}` 占位

`production.md` 中的 `{skill:<id>}` 表示解析结果里的绝对根目录。例如：

```text
{skill:ppt-master}/templates/decks/中国电子云
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
- `deps.json` 的 `testedVersion` 记录本仓库验证过的版本/提交。升级依赖后重跑 `scripts/check_skill.py` 和路由评测；不要求与上游最新版完全一致。
- 需要锁定版本时，在安装命令后 checkout 对应 tag 或 commit；不要修改依赖源码来适配本 Skill。

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

旧版把四个制作 Skill 放在 `<工作区>/skills/` 下；解析顺序第 4 项仍支持这种布局。迁移到新布局后，建议把依赖装到用户级或项目级 skills 根目录，并删除旧的 `skills/` 副本，避免同名依赖出现两个版本。
