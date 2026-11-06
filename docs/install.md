# 安装与宿主发现

本 Skill 的仓库根目录就是 Skill 根目录：`SKILL.md` 在根下，`references/`、`scripts/`、`docs/` 与它同级。宿主发现规则决定它能不能被加载；运行时产物则写到用户工作区，不写进这个目录。

## 一、宿主如何发现 Skill

以 DSH 的本地 Skill provider 为例：

- 只扫描**一层**：`<root>/<name>/SKILL.md` 或 `<root>/<name>.md`；嵌套的 `**/SKILL.md` 不会被发现。
- 默认扫描根（按优先级）：

  | 优先级 | 来源 | 路径 |
  |---|---|---|
  | 100 | 项目 DSH | `<项目根>/.dsh/skills` |
  | 110 | 项目 ZCode | `<项目根>/.zcode/skills` |
  | 200 | 项目 Agents | `<项目根>/.agents/skills` |
  | 300 | 自定义 | `customSkillDirs` |
  | 400 | 用户 DSH | `~/.dsh/skills` |
  | 410 | 用户 ZCode | `~/.zcode/skills` |
  | 500 | 用户 Agents | `~/.agents/skills` |
  | 600 | 内置 | `$DSH_BUNDLED_SKILL_DIR` |

- 项目根是最近的含 `.git` 的祖先目录；没有 `.git` 时取当前工作目录。
- frontmatter 必须有 `name`（kebab-case）和 `description`；catalog 里的 description 会被截断到配置上限（默认 500 字符）。
- 新增、改名、删除 Skill 或改 frontmatter 会自动刷新 catalog；编辑 `references/`、`scripts/`、`assets/` 等资源不会触发刷新。

其他宿主（ZCode、Claude Code 等）的 skills 根目录不同，但目录形态相同：把本仓库放到 `<skills-root>/ppt-planner-maker` 即可。ZCode 常见位置是 `~/.zcode/skills` 或 `<工作区>/.zcode/skills`；本仓库的解析器也默认搜索这两个位置。

## 二、安装本 Skill

### 用户级（推荐）

DSH：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.dsh/skills/ppt-planner-maker
```

ZCode：

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.zcode/skills/ppt-planner-maker
```

### 项目级

Windows 目录联接（无需管理员，PowerShell 里用 `cmd /c` 包一层）：

```bat
mklink /J "<项目根>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

```powershell
cmd /c mklink /J "$PWD\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

macOS / Linux：

```bash
mkdir -p <项目根>/.dsh/skills
ln -s /path/to/ppt-planner-maker <项目根>/.dsh/skills/ppt-planner-maker
```

也可以直接复制目录；软链/联接的好处是改仓库后宿主能立即看到。

### 不要这样做

```text
<skills-root>/ppt-planner-maker/skills/ppt-planner-maker/SKILL.md   # 多套了一层，发现不了
```

## 三、安装制作依赖

四个制作 Skill 不随本仓库分发。`<skills-dir>` 指任一被宿主扫描的 skills 根目录；只安装当前任务需要的分支也可以。

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

如果不想装进宿主扫描目录，可以集中放在自定义目录：

```bash
# Windows PowerShell
$env:PPT_PLANNER_SKILLS_DIR = "D:\path\to\ppt-skills"
# macOS / Linux
export PPT_PLANNER_SKILLS_DIR="$HOME/path/to/ppt-skills"
```

多个目录用系统路径分隔符分隔（Windows `;`，macOS/Linux `:`）。`--skills-dir` 参数优先于环境变量，可重复传入。

依赖的版本、能力要求和许可边界见 [../references/dependencies.md](../references/dependencies.md)；机器可读清单见 [../scripts/deps.json](../scripts/deps.json)。

### 安装 Python 运行时依赖

`git clone` 只装“引擎”，PPTX 分支还需要 Python 包：

```bash
# 分支 A / B / F（ppt-master）
python -m pip install -r <skills-dir>/ppt-master/requirements.txt

# 分支 C（gorden）
python -m pip install python-pptx
```

- 分支 D / E 无 Python 运行时依赖；视觉检查需要浏览器。
- `requirements.txt` 里的 `edge-tts`、`PyMuPDF` 是可选能力（旁白音频、PDF 解析），不用可以跳过；PyMuPDF 是 AGPL-3.0。
- `skia-pathops`、`uharfbuzz` 在部分平台需要编译工具；装不上时用官方 wheel 或换 Python 版本。
- Windows 上优先用 `python`，不要依赖 `python3`（可能是 Microsoft Store 占位程序）。

### 一键安装（可选，需确认）

手动 clone / pip 之外，可以用 `setup.py` 代装。默认只打印计划，**不安装**：

```bash
python "<skill-dir>/scripts/setup.py" --workspace <工作区> --branches A,F
```

确认后加 `--yes` 执行：缺失依赖 `git clone` 到私有目录 `~/.ppt-planner/skills`（`PPT_PLANNER_HOME` 或 `--skills-dir` 可覆盖，宿主不扫描）并锁定到 `deps.json` 记录的 commit（`--latest` 跳过），缺的 Python 包用 `pip` 安装。LibreOffice、浏览器等系统级组件只提示不代装；安装目标在 Skill 包内会被拒绝。

### 安装渲染器（可选但推荐）

PPTX 视觉检查与旧版 `.ppt` 转换需要 LibreOffice。`soffice` 不在 PATH 时，`check_runtime.py` 会尝试常见安装目录（如 `C:\Program Files\LibreOffice\program\soffice.exe`）并给出实际路径。仍找不到时，按 [../references/production.md](../references/production.md) 如实报告“结构检查通过、视觉检查未完成”。

## 四、验证

```bash
python "<skill-dir>/scripts/doctor.py" --workspace <工作区> --branches A,B,C,D,E,F
```

`doctor.py` 只读，把路径、能力和运行时检查合成一份结论；缺什么按“下一步”装，装完重跑。需要单独排查时再用：

```bash
python "<skill-dir>/scripts/resolve_skills.py" --check --branches A,B,C,D,E,F
python "<skill-dir>/scripts/check_runtime.py" --check --branches A,B,C,D,E,F
```

`<skill-dir>` 是本仓库根目录（含 `SKILL.md` 的目录），不是当前工作区。路径检查全部 `OK` 只代表目录与能力就绪；运行时检查通过才代表能构建。两者是两件事。加 `--brief` 可只输出一行摘要；需要排查时去掉 `--brief` 或加 `--json`。

期望输出（路径随机器变化）：

```text
workspace: D:\work\demo
skill root: C:\Users\you\.dsh\skills\ppt-planner-maker
roots:
   1. project-dsh      D:\work\demo\.dsh\skills  (missing)
   ...
skills (branches: A,B,C,D,E,F):
  ppt-master           OK          A,B,F    D:\ppt-skills\ppt-master
  gorden-ppt-skill     OK          C        D:\ppt-skills\gorden-ppt-skill
  html-ppt             OK          D        D:\ppt-skills\html-ppt
  guizang-ppt-skill    OK          E        D:\ppt-skills\guizang-ppt-skill
```

```text
branches: A,B,C,D,E,F
  ppt-master           INCOMPLETE  A,B,F
      missing required: pathops, uharfbuzz
      command soffice: D:\Program Files\LibreOffice\program\soffice.exe  (not on PATH)
      install: python -m pip install -r <ppt-master>/requirements.txt
  gorden-ppt-skill     OK          C
  html-ppt             OK          D
  guizang-ppt-skill    OK          E
```

- 退出码 `0`：所选依赖全部 `ok`。
- 退出码 `1`：有依赖 `missing` / `incomplete` / `invalid`，或运行时缺必需包/命令；stderr 会列出未就绪的 ID。
- 退出码 `2`：参数或依赖清单错误。

`--json` 输出机器可读结果，适合交给代理继续处理；`--out <file>` 可把 JSON 写到文件（例如项目的 `_build/`）。解析器只读文件系统，不写入 Skill 目录。

## 五、按分支只装需要的依赖

| 分支 | 依赖 | 运行时 | 典型任务 |
|---|---|---|---|
| A | `ppt-master` + 已安装 deck（自带模板文件时免） | Python 包 + 可选 `soffice` | 套中国电子云/中国电信/中汽研、自备 deck 或公司模板文件 |
| B | `ppt-master` | Python 包 + 可选 `soffice` | 从零设计、可编辑 PPTX |
| C | `gorden-ppt-skill` | `python-pptx` + 首次联网 | 用现成设计模板（gorden 内置模板库）、可编辑 PPTX |
| D | `html-ppt` | 浏览器（视觉检查） | HTML 常规演示 |
| E | `guizang-ppt-skill` | 浏览器（视觉检查） | 杂志风/瑞士风 HTML |
| F | `ppt-master` | Python 包 + 可选 `soffice` | 修改/美化现有 PPTX |

只要大纲、不进入制作时，不需要安装任何制作依赖。本 Skill 不预置公司模板；分支 A 的 deck 来自 `ppt-master/templates/decks/`。

## 六、更新与卸载

- **更新本 Skill**：在仓库目录 `git pull`；软链/联接安装会立即生效。
- **更新依赖**：进入对应依赖目录 `git pull`，或按各依赖自己的更新机制执行。升级后重跑解析器和 `python "<skill-dir>/scripts/check_skill.py"`。
- **卸载本 Skill**：删除 `~/.dsh/skills/ppt-planner-maker`（或项目级软链/联接）。依赖按需保留或删除。
- **锁定版本**：安装后 `git -C <skills-dir>/<id> checkout <tag-or-commit>`；不要修改依赖源码来适配本 Skill。

## 七、故障排查

### catalog 里看不到本 Skill

1. 确认文件是 `<skills-root>/ppt-planner-maker/SKILL.md`，不是 `<skills-root>/ppt-planner-maker/skills/ppt-planner-maker/SKILL.md`。
2. 检查 frontmatter 的 `name` 是否为 kebab-case、`description` 是否非空。
3. 确认该根目录在宿主的扫描列表里；项目级根目录要求项目根有 `.git`（DSH）。
4. 新开一个会话或下一步再看 catalog；资源文件改动不会触发刷新，改 `SKILL.md` 会。

### 解析器找不到依赖

1. 先跑 `python "<skill-dir>/scripts/doctor.py" --workspace <工作区> --branches A` 看结论；需要代装时用 `setup.py`（先看计划，确认后 `--yes`）。
2. 依赖必须是目录型：`<root>/<id>/SKILL.md`；只有 `<root>/<id>.md` 会被标为 `invalid`，且不会遮蔽后面找到的有效目录。
3. 用 `--skills-dir` 或 `PPT_PLANNER_SKILLS_DIR` 指向实际目录。
4. 分支 A 选择已安装 deck 时还要求 `ppt-master/templates/decks/` 下至少一个 deck（含 `templates/design_spec.md`）和 `decks_index.json`；只有引擎没有 deck 会标为 `incomplete`。用户自带公司 `.pptx` / `.potx` 文件时给 `resolve_skills.py` / `doctor.py` / `setup.py` 加 `--company-template-file`，这两项不再阻塞，其他检查不变。

### 解析器是 OK，构建却报 ModuleNotFoundError

`resolve_skills.py` 只看目录与能力，不看 Python 包。运行 `python "<skill-dir>/scripts/check_runtime.py" --branches A`，按输出的 `missing required` 安装；ppt-master 用 `python -m pip install -r <skills-dir>/ppt-master/requirements.txt`。

### gorden 更新检查失败

gorden 的入口要求先跑会改写安装的 `scripts/apply_update.py`。为保持锁定版本，编排层改跑只读的 `scripts/check_update.py`，有新版本时告知用户，同意后才更新。无网或代理环境下如实记录并继续，不要假装已更新；Windows 上把命令里的 `python3` 换成 `python`。

### PPTX 视觉检查没做

通常是找不到 `soffice`。运行 `python "<skill-dir>/scripts/check_runtime.py" --branches A` 看 `command soffice` 的实际路径；找到后按 production.md 的要求用渲染器生成预览，仍不可用时如实报告“结构检查通过、视觉检查未完成”。

### Windows 中文路径或编码

- 用 `python`，不要依赖 `python3`。
- 临时 PowerShell 脚本保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`；无 BOM 的 UTF-8 会被 PowerShell 5.1 按 GBK 读取。
- 路径含空格时加引号；联接目标用绝对路径。


显式 --skills-dir 仅检查目标根目录，其他副本只提示；默认仅复用 drift=match 的副本，drift/unknown 则计划装入私有目录（PPT_PLANNER_HOME 可覆盖）。目标已有不同或未知版本需手动处理，不覆盖、不自动切换；项目级旧副本可能抢占，须按警告处理。执行顺序为 clone → pin → pip，requirements 取锁定后的目标副本。
