# 安装与宿主发现

本 Skill 的仓库根目录就是 Skill 根目录：`SKILL.md` 在根下，`references/`、`scripts/`、`docs/` 与它同级。宿主发现规则决定它能不能被加载；运行时产物则写到用户工作区，不写进这个目录。

## 一、宿主如何发现 Skill

以 DSH 的本地 Skill provider 为例：

- 只扫描**一层**：`<root>/<name>/SKILL.md` 或 `<root>/<name>.md`；嵌套的 `**/SKILL.md` 不会被发现。
- 默认扫描根（按优先级）：

  | 优先级 | 来源 | 路径 |
  |---|---|---|
  | 100 | 项目 DSH | `<项目根>/.dsh/skills` |
  | 200 | 项目 Agents | `<项目根>/.agents/skills` |
  | 300 | 自定义 | `customSkillDirs` |
  | 400 | 用户 DSH | `~/.dsh/skills` |
  | 500 | 用户 Agents | `~/.agents/skills` |
  | 600 | 内置 | `$DSH_BUNDLED_SKILL_DIR` |

- 项目根是最近的含 `.git` 的祖先目录；没有 `.git` 时取当前工作目录。
- frontmatter 必须有 `name`（kebab-case）和 `description`；catalog 里的 description 会被截断到配置上限（默认 500 字符）。
- 新增、改名、删除 Skill 或改 frontmatter 会自动刷新 catalog；编辑 `references/`、`scripts/`、`assets/` 等资源不会触发刷新。

其他宿主（Claude Code、ZCode 等）的 skills 根目录不同，但目录形态相同：把本仓库放到 `<skills-root>/ppt-planner-maker` 即可。

## 二、安装本 Skill

### 用户级（推荐）

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.dsh/skills/ppt-planner-maker
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

## 四、验证

```bash
python scripts/resolve_skills.py --check --branches A,B,C,D,E,F
```

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

- 退出码 `0`：所选依赖全部 `ok`。
- 退出码 `1`：有依赖 `missing` / `incomplete` / `invalid`；stderr 会列出未就绪的 ID。
- 退出码 `2`：参数或依赖清单错误。

`--json` 输出机器可读结果，适合交给代理继续处理；`--out <file>` 可把 JSON 写到文件（例如项目的 `_build/`）。解析器只读文件系统，不写入 Skill 目录。

## 五、按分支只装需要的依赖

| 分支 | 依赖 | 典型任务 |
|---|---|---|
| A | `ppt-master`（含公司 deck） | 必须套中国电子云/中国电信/中汽研等模板 |
| B | `ppt-master` | 非公司模板、专业简洁 PPTX |
| C | `gorden-ppt-skill` | 非公司模板、复杂豪华 PPTX |
| D | `html-ppt` | 常规 HTML 演示 |
| E | `guizang-ppt-skill` | 杂志风/瑞士风 HTML |
| F | `ppt-master` | 修改/美化现有 PPTX |

只要大纲、不进入制作时，不需要安装任何制作依赖。

## 六、更新与卸载

- **更新本 Skill**：在仓库目录 `git pull`；软链/联接安装会立即生效。
- **更新依赖**：进入对应依赖目录 `git pull`，或按各依赖自己的更新机制执行。升级后重跑解析器和 `python scripts/check_skill.py`。
- **卸载本 Skill**：删除 `~/.dsh/skills/ppt-planner-maker`（或项目级软链/联接）。依赖按需保留或删除。
- **锁定版本**：安装后 `git -C <skills-dir>/<id> checkout <tag-or-commit>`；不要修改依赖源码来适配本 Skill。

## 七、故障排查

### catalog 里看不到本 Skill

1. 确认文件是 `<skills-root>/ppt-planner-maker/SKILL.md`，不是 `<skills-root>/ppt-planner-maker/skills/ppt-planner-maker/SKILL.md`。
2. 检查 frontmatter 的 `name` 是否为 kebab-case、`description` 是否非空。
3. 确认该根目录在宿主的扫描列表里；项目级根目录要求项目根有 `.git`（DSH）。
4. 新开一个会话或下一步再看 catalog；资源文件改动不会触发刷新，改 `SKILL.md` 会。

### 解析器找不到依赖

1. 先看输出的 `roots` 列表，确认目标目录在不在里面。
2. 依赖必须是目录型：`<root>/<id>/SKILL.md`；只有 `<root>/<id>.md` 会被标为 `invalid`。
3. 用 `--skills-dir` 或 `PPT_PLANNER_SKILLS_DIR` 指向实际目录。
4. 分支 A 还要求 `ppt-master/templates/decks/中国电子云` 存在；只有引擎没有 deck 会标为 `incomplete`。

### Windows 中文路径或编码

- 用 `python`，不要依赖 `python3`。
- 临时 PowerShell 脚本保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`；无 BOM 的 UTF-8 会被 PowerShell 5.1 按 GBK 读取。
- 路径含空格时加引号；联接目标用绝对路径。
