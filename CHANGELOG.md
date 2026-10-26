# Changelog

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
- `python -m unittest discover -s tests`
- 路由干跑：A–F 分支、冲突拦截、负向风格词、依赖缺失、只要大纲、工作区保护。
- 真实端到端：至少一条公司模板 PPTX 或 HTML 分支，检查解析、交接与成品。

## 0.9.0 — 2026-10-26

最后一版捆绑式工作区：5 个 Skill（1 个编排 + 4 个制作）与演示资产同仓，路由按内容偏好分流，保留“使用性质”之外的新口径。作为迁移回滚点保留。
