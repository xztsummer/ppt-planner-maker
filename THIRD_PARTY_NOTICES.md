# 第三方依赖声明

本仓库**不包含**第三方 Skill 的源码。运行时依赖以下外部项目；它们不属于根目录 [`LICENSE`](./LICENSE)（CC BY-NC 4.0）的授权范围，各自保留原有许可证与版权声明。

## 依赖清单

| ID | 上游 | 许可证 | 商业使用 |
|---|---|---|---|
| `ppt-master` | [xztsummer/ppt-master](https://github.com/xztsummer/ppt-master)（同步自 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)，当前 v6.8.0，含公司 deck） | MIT | 允许；保留版权与许可声明 |
| `gorden-ppt-skill`（脚本、`references/`、元数据） | [GordenSun/GordenPPTSkill](https://github.com/GordenSun/GordenPPTSkill) | MIT | 允许 |
| `gorden-ppt-skill/templates/`（`.pptx` 与预览图） | 同上；模板来自公开中文模板渠道，见其 `NOTICE.md` | 第三方模板作者版权，非商业许可 | **禁止**；仅限个人学习与研究 |
| `html-ppt` | [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) | MIT | 允许；保留版权声明 |
| `guizang-ppt-skill` | [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) | AGPL-3.0 | 允许；修改后分发或作为网络服务提供时，须按 AGPL 开放对应源码 |

安装、版本与能力要求见 [`references/dependencies.md`](./references/dependencies.md)；机器可读清单见 [`scripts/deps.json`](./scripts/deps.json)。

## 说明

- **`gorden-ppt-skill` 的模板素材**：商用授权只能由模板原作者授予，本仓库维护者无权转授。使用其内置模板做商业演示、客户提案或企业内部经营汇报前，须自行取得授权。
- **`ppt-master` 的公司 deck**：MIT 覆盖代码，不覆盖公司 logo、品牌名称和商标；这些标识归各自权利人所有，使用前须确认品牌使用规范。
- **第三方资产**：依赖内部可能含图标、音效、字体等独立许可资源，见各依赖目录内的声明。
- **AGPL-3.0**：`guizang-ppt-skill` 为强 copyleft 许可；修改后分发，或通过网络向他人提供修改版本时，须按 AGPL 提供对应源码。
- **生成物**：使用各 Skill 生成的 PPT / HTML 成品，其版权与可用范围取决于所用模板、素材和模型服务条款，不自动适用本仓库的任何许可证。

## 本仓库原创部分

`SKILL.md`、`references/`、`scripts/`、`docs/`、`tests/`、`README.md`、`README.en.md`、`AGENTS.md`、`VERSION`、`CHANGELOG.md` 及本文件由维护者原创，采用 CC BY-NC 4.0，详见根目录 [`LICENSE`](./LICENSE)。`evals/` 为本地评测目录，不随仓库分发。
