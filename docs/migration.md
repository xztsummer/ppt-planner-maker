# 从旧版迁移

本页面向两类用户：

1. 用过 0.9.0 及更早的**捆绑式工作区**（仓库内含 `skills/`、`projects/`、`output/`、示例成品）；
2. 在旧工作区里保留了 `<工作区>/skills/` 布局，想继续用旧路径。

## 一、变化一览

| 项目 | 旧版（≤ 0.9.0） | 新版（1.0.0） |
|---|---|---|
| 仓库形态 | 工作区 + `skills/` 下 5 个 Skill | 仓库根目录即 `ppt-planner-maker` 一个 Skill |
| 制作 Skill | 随仓库分发在 `skills/` 下 | 外部依赖，按需安装到宿主 skills 根目录 |
| 路径写法 | `{工作区}/skills/ppt-master` | 逻辑 ID + `{skill:ppt-master}`，由解析器给出绝对路径 |
| 运行产物 | 仓库内的 `projects/`、`output/` | 目标工作区的 `projects/`，Skill 包只读 |
| 路由依据 | 曾按“商业/个人用途”分流 | 只看内容偏好（复杂豪华/专业简洁）与模板/格式要求 |
| 评测用例 | `tests/` 本地 | `evals/` 本地，不随仓库分发；`tests/` 只放 Python 单测 |
| 许可 | 原创部分 CC BY-NC 4.0 | 不变；外部依赖许可单独列出 |

## 二、保留/取回旧版

旧版仍可从标签 `v0.9.0` 取回：

```bash
git worktree add ../ppt-agent-kit-v0.9 v0.9.0
```

或在 GitHub 的 Tags 页面下载 `v0.9.0` 的源码包。旧版包含四个制作 Skill 与只读效果样例，适合对照或临时应急；不建议在新任务里继续使用旧路径。

## 三、迁移提示词

旧提示词里的 `skills\ppt-master`、`skills\gorden-ppt-skill` 等不再是本仓库内的路径。迁移方式：

1. 按 [install.md](install.md) 安装需要的依赖。
2. 把提示词里的路径改成 Skill 名或直接自然语言：

```text
# 旧
使用 skills\ppt-master 技能，严格套中国电子云模板……

# 新
用 ppt-master，严格套中国电子云模板……
```

```text
# 旧
使用 skills\guizang-ppt-skill 技能，做一份杂志风 HTML……

# 新
用 guizang-ppt-skill，做一份杂志风 HTML……
```

3. 仍想指定路径时，用 `--skills-dir` 或 `PPT_PLANNER_SKILLS_DIR` 指向依赖目录，不要把路径写进需求文档。

## 四、迁移旧工作区

旧工作区通常长这样：

```text
old-workspace/
├── skills/                  # 四个制作 Skill 的旧副本
├── references/              # 用户素材
├── projects/                # 历史项目
└── output/                  # 历史成品
```

建议：

1. 把 `projects/`、`output/`、`references/` 移到新的目标工作区（或保持原位，作为工作区继续使用）。
2. 安装新版依赖到 `~/.dsh/skills` 或该工作区的 `.dsh/skills`。
3. 删除 `skills/` 下的旧副本，避免同名依赖出现两个版本；如果暂时保留，解析器仍会按第 4 优先级使用 `<工作区>/skills`，并在 `shadowed` 中记录其他副本。
4. 历史项目不需要迁移：`需求调研.md`、确认版大纲和成品都是纯文件，继续按原目录读取即可。

`projects/` 里的旧项目没有 `依赖解析` 记录，续作时按当前依赖重新解析一次即可，不必补写历史记录。

## 五、路由行为变化

- **不再按用途分流**。需求表不记录商业/个人用途；非公司模板 PPTX 由内容偏好决定：复杂豪华 → `gorden-ppt-skill`（分支 C），专业简洁 → `ppt-master`（分支 B）。
- **复杂豪华是默认偏好**。用户未说明偏好时走分支 C；需求表会加一行“模板许可提示：gorden 内置模板仅限个人学习研究，商用需自行取得授权”。
- **快速模式不跳过许可提示**。授权直出仍会展示该提示；`confirmation.md` 里旧的“使用许可判断（默认走 ppt-master）”已删除。
- **依赖缺失是阻塞项**。不再回退到“碰巧装了的另一个制作 Skill”，而是停止并给安装命令。
- **只要大纲无需依赖**。入口①②的调研、思路和逐页策划不依赖制作引擎。

## 六、破坏性变更

- 仓库根目录不再有 `skills/`；按旧路径读取 `skills/ppt-planner-maker/SKILL.md` 的脚本会失败。
- `AGENTS.md` 不再声明“默认执行 `skills\ppt-planner-maker`”；默认入口改为宿主 catalog 中的 `ppt-planner-maker`。
- `THIRD_PARTY_NOTICES.md` 从“随仓库分发的第三方组件”改为“外部依赖许可矩阵”。
- `LICENSE` 的适用范围改为本仓库原创文件；旧版 `skills/` 下的第三方代码不再随仓库分发。

## 七、回滚

- 代码回滚：`git checkout v0.9.0`（或上面的 worktree）。
- 依赖回滚：在依赖目录 checkout 旧 tag/commit；`scripts/deps.json` 的 `testedVersion` 记录了本仓库验证过的版本。
- 数据回滚：`projects/`、`output/`、`references/` 只是被移动，不删除；按原路径放回即可。

如迁移中遇到路径或依赖问题，先运行：

```bash
python scripts/resolve_skills.py --workspace <工作区> --branches A --json
```

把输出里的 `roots`、`status`、`missingRequired` 一并提供，便于定位。
