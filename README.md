# ppt-agent-kit

**中文** | [English](README.en.md)

面向 AI 助手的演示文稿技能工具包：从需求调研、大纲策划到制作与修改，支持可编辑 PPTX 和 HTML 演示文稿。

**PPT Agent Kit** 集成 5 个 Agent Skill，可在 ZCode、Claude Code 等支持 Agent Skill 的 AI 工具中使用。你用自然语言描述主题、提供材料或提出修改要求，助手按需完成需求调研、大纲策划与确认，再调用合适的制作 Skill 生成并检查成品。

- **从主题到成品**：支持从零策划、基于已有大纲制作，以及修改或美化现有 PPTX。
- **多种制作方式**：公司模板、自由设计、内置中文模板，以及常规、杂志风和瑞士风网页演示。
- **两类输出格式**：可编辑 PowerPoint（`.pptx`）与 HTML 网页演示，按需求选择。
- **统一流程与归档**：默认由 `ppt-planner-maker` 编排，需求、确认稿、素材和成品按任务保存；熟悉流程后也可直接指定制作 Skill。

克隆仓库后，用支持 Agent Skill 的 AI 工具打开项目目录，即可按下方说明开始使用。模型调用及部分增强功能需要联网，文档与成品在本地生成和保存。

> ⚠️ **商用前必读**：本仓库原创部分（`ppt-planner-maker`、根目录文档、`tests/`）采用 **CC BY-NC 4.0，禁止商业使用**；`gorden-ppt-skill` 的内置模板与素材同样禁止商用。其余第三方组件按各自许可证使用：`ppt-master`、`html-ppt` 为 MIT，`guizang-ppt-skill` 为 AGPL-3.0。详见 [许可与商用范围](#许可与商用范围)、[`LICENSE`](LICENSE) 和 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 【资深用户】先选 Skill（推荐先看这一节）

**【推荐】资深用户可以直接手动指定 Skill**，跳过默认的调研与策划编排，一句话下达制作任务即可，效率最高。

一般场景推荐：

| 场景 / 需求 | 推荐 Skill | 输出格式 |
|---|---|---|
| 严格套用公司模板（中国电子云、中国电信、中汽研等） | `skills\ppt-master` | 可编辑 PPTX |
| 自由设计 PPTX（商业/企业用途默认），或修改/美化现有 PPTX | `skills\ppt-master` | 可编辑 PPTX |
| 个人学习研究套用内置中文模板（21 套复杂/豪华或简洁模板，非商用） | `skills\gorden-ppt-skill` | 可编辑 PPTX |
| 汇报、类 PPT、常规演示 | `skills\html-ppt` | HTML |
| 杂志风、瑞士风、设计感、演讲分享 | `skills\guizang-ppt-skill` | HTML |

没有明确偏好时，直接用自然语言描述需求即可。按 `AGENTS.md` 的约定，项目默认执行 `skills\ppt-planner-maker`，由它完成需求调研、大纲/修改方案策划和制作路由，再自动选择上面的制作 Skill。

几点约束：

- **严格套公司模板时只能输出可编辑 PPTX**，不能同时要求 HTML；两者冲突时流程会先请你调整需求。
- `gorden-ppt-skill` 的内置模板与其素材**仅限个人学习和研究，禁止商业用途**。商业演示、客户提案、企业内部经营用途请改用 `ppt-master` 自由设计，或使用公司模板。
- HTML 是网页演示，不是 PowerPoint；不要把 HTML 文件改名为 `.pptx`。

### 制作任务示例

**自由设计 PPTX（ppt-master）**

```text
使用 skills\ppt-master 技能
读取源文件 `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md`，基于其完整内容生成一份可直接放映的 PPT 演示文稿。
整体风格简洁、专业、高级感，白底蓝色科技风格，蓝色十六进制色号是： #0058FF
最后生成的文件输出到 /output 目录，命名为：TREMAC与可信数据空间技术融合探索_qoder+ds41flash+pptmatster.pptx
```

**杂志风 / 设计感 HTML（guizang-ppt-skill）**

```text
使用 skills\guizang-ppt-skill 技能
读取源文件 `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md`，基于其完整内容生成一份可直接放映的 PPT 演示文稿。
整体风格简洁、专业、高级感，白底蓝色科技风格，蓝色十六进制色号是： #0058FF
最后生成的文件输出到 /output 目录，命名为：TREMAC与可信数据空间技术融合探索_wb+minimax31+guizang
```

**公司模板 PPTX（ppt-master + 中国电子云 deck）**

```text
使用 skills\ppt-master 技能
以及  skills\ppt-master\templates\decks\中国电子云  deck模板
读取源文件 `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md`，基于其完整内容生成一份可直接放映的 PPT 演示文稿。
整体风格简洁、专业、高级感
最后生成的文件输出到 /output 目录，命名为：TREMAC与可信数据空间技术融合探索_中国电子云_qoder+ds41flash+pptmatster.pptx
```

**复杂豪华 PPTX（gorden-ppt-skill）**

```text
使用 skills\gorden-ppt-skill 技能
读取源文件 `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md`，基于其完整内容生成 PPT 演示文稿。
PPT整体风格复杂、豪华、专业、高级，白底蓝色科技风格，蓝色十六进制色号是： #0058FF
最后生成的文件输出到 /output 目录，命名为：TREMAC与可信数据空间技术融合探索_qoder+ds41flash+gordenppt豪华蓝.pptx
```

输出目录、文件名和源文件都可以替换；HTML 分支建议在文件名后显式补上 `.html` 扩展名。

## 【普通用户】快速开始

### 1. 准备环境

先克隆仓库，并用 AI 工具打开 `ppt-agent-kit` 目录：

```bash
git clone https://github.com/xztsummer/ppt-agent-kit.git
cd ppt-agent-kit
```

环境要求：

- 支持 Agent Skill 的 AI 工具（ZCode、Claude Code、Cursor 等）
- Python 3.10+（运行 `ppt-master` 与 `gorden-ppt-skill` 的制作脚本）
- Node.js 18+（可选，用于 guizang 的演讲者模式与 Swiss deck 校验脚本）
- Google Chrome（可选，用于把 HTML 页面渲染成 PNG 做视觉检查）

### 2. 安装依赖

```bash
pip install -r skills/ppt-master/requirements.txt
```

`ppt-master` 的多数脚本只用标准库；上面的依赖用于 SVG 转 PPTX、PDF/Word/Excel 解析、AI 生图、旁白音频等增强能力。`gorden-ppt-skill` 所需的 `python-pptx` 也已包含在内。

### 3. 放入素材（可选）

把参考文档、旧 PPT、图片等放进 `references/`，对话时直接说明文件名即可。素材只作为信息来源，不会被覆盖。

### 4. 向 AI 提出需求

默认流程（推荐第一次使用）：

> 帮我做一份 15 页的《可信数据空间》汇报 PPT，听众是客户，讲解 30 分钟，风格专业简洁。

手动指定 Skill：

> 用 ppt-master，严格套中国电子云公司模板，把 `references/方案.docx` 做成一份 20 页的汇报 PPT。

> 用 guizang-ppt-skill 做一份杂志风的网页 PPT，主题是“AI 与设计”，用于线下分享。

> 用 html-ppt 做一份 8 页的技术分享 slides，白底蓝色科技风。

### 5. 确认并生成

默认流程会逐阶段把**完整内容展示在对话里**，你确认后才保存文档并进入下一步：

1. 确认需求（主题、听众、时长、模板要求、输出格式、视觉风格）
2. 确认规划思路（叙事主线、章节、页数、时间分配；已有大纲或修改现有 PPTX 时跳过）
3. 逐页确认大纲或修改方案（每页标题、结论、内容、呈现建议，或逐页修改清单）
4. 自动路由到制作 Skill，生成并检查成品

### 6. 取成品

所有生成物都在 `projects/` 下，按 `YYYYMMDDHHmm_主题名/` 归档，成品文件与目录同名：

```text
projects/202610220848_可信数据空间/
├── 需求调研.md
├── PPT规划思路.md                     # 入口①
├── PPT详细大纲_确认版.md               # 入口①②
├── 修改方案_确认版.md                  # 入口③
├── sources/                           # 用户材料只读副本（保留原文件名）
├── versions/                          # 已确认稿的历史版本
├── _draft/                            # 可选：未确认草稿
├── 202610220848_可信数据空间.pptx     # PPTX 分支
├── 202610220848_可信数据空间.html     # HTML 分支；双格式需求时两者均交付
├── assets/ 或 images/                 # HTML 的本地资源（如有）
└── _build/<skill 名>/                 # 制作工作区与中间产物（含渲染预览与校验报告）
```

## 目录结构

```text
ppt-agent-kit/
├── AGENTS.md                  # 未指定 Skill 时的默认路由
├── README.md                  # 中文（默认）
├── README.en.md               # English
├── LICENSE                    # 原创部分许可：CC BY-NC 4.0（禁止商用）
├── THIRD_PARTY_NOTICES.md     # 第三方 Skill 的许可证与商用限制
├── skills/
│   ├── ppt-planner-maker/     # 流程编排：调研 → 大纲/修改方案 → 确认 → 制作（默认）
│   ├── ppt-master/            # PPTX：公司模板 / 自由设计 / 模板提炼 / 美化
│   ├── gorden-ppt-skill/      # PPTX：21 套内置中文模板
│   ├── html-ppt/              # HTML：36 主题、36 版式、演讲者模式
│   └── guizang-ppt-skill/     # HTML：电子杂志 / 瑞士国际主义风格
├── references/                # 你提供的参考素材
├── projects/                  # 按任务归档的文档与成品
└── 【只读】不同模型+skill组合效果示例/   # 同主题不同组合的成品样例
```

## 各 Skill 能力速览

### ppt-master

原生可编辑 PPTX 工作流，适合公司模板和正式业务场景。提供五条路线：

- **Generate PPTX**：从材料或主题生成新 deck，支持“复杂豪华”和“专业简洁”两档偏好
- **Beautify**：对已有 PPTX 做 1:1 美化，不改内容结构
- **Image to PPTX**：把页面图片重建为可编辑对象
- **Create Template**：从 PPTX、图片或品牌资产提炼可复用的 Brand / Style / Layout / Deck 模板
- **Edit Native PPTX**：把新内容填入已有 `.pptx`，未改动页面逐字节保留

内置 `templates/decks/` 下有中国电子云、中国电信、中汽研等公司模板。输出为原生形状、图表、表格、公式和母版继承，不是整页截图。依赖见 `skills/ppt-master/requirements.txt`，使用前会执行归属校验脚本。

### gorden-ppt-skill

内置 **21 套中文 PPT 模板**，覆盖工作汇报、年终总结、述职竞聘、项目复盘、开题答辩、商务提案、教学课件、数据可视化等场景。核心能力是**只替换文字、不破坏原模板的排版、配色和字号**，并带文本框溢出检测和同级标题字号一致性校验；也支持原创简洁版式。

首次使用时 Skill 会运行 `python3 scripts/apply_update.py` 做增量更新；Windows 上若 `python3` 不可用，改用 `python`。**注意：非商业限制只针对其内置模板与素材，代码部分为 MIT**。

### html-ppt

纯静态 HTML 演示文稿，无需构建：

- 36 套主题、15 套整套模板、36 种页面布局、47 种动画（27 个 CSS + 20 个 Canvas FX）
- 键盘翻页、触屏滑动、`S` 键演讲者模式（当前页 / 下一页 / 逐字稿 / 计时器）
- 单文件 HTML，字体走 CDN，断网时回退系统字体
- 自带 headless Chrome 截图脚本（`scripts/render.sh`，默认写死 macOS 的 Chrome 路径，Windows 使用需调整）

适合汇报、技术分享、产品介绍等“类 PPT”场景。

### guizang-ppt-skill

单文件 HTML 横向翻页 PPT，提供两种视觉基调：

- **电子杂志 × 电子墨水**：衬线标题、WebGL 流体/等高线背景、暖色，适合人文分享、行业观察、商业发布
- **瑞士国际主义**：无衬线字体、网格点阵、高反差功能色（IKB 蓝 / 柠檬黄 / 柠檬绿 / 安全橙），适合科技产品、数据汇报、设计工程分享

支持演讲者视图、观众屏同步、讲稿备注、章节幕封、数据大字报、激光笔和圈选。适合线下分享、发布会、demo day 等强个人风格的演讲；大量表格和密集培训内容不适合。

## 默认工作流说明

`skills\ppt-planner-maker` 是流程编排 Skill，本身不直接画页面，负责把“想法”变成可执行的制作任务。它提供三个入口：

- **入口①：规划 PPT 大纲** —— 从主题开始，调研需求、对齐思路、逐页策划，确认后再制作
- **入口②：已有大纲，直接制作** —— 保留原大纲的顺序和原意，补齐逐页制作信息后制作
- **入口③：修改/美化现有 PPTX** —— 保留原版式增量编辑，或保留内容重新设计版式；不覆盖源文件

全程遵循分级确认：需求、规划思路、逐页大纲/修改方案等用户决策文档，先在对话中完整展示，用户明确确认后才落盘；制作引擎内部的 spec、SVG、构建日志和校验报告直接写入项目工作区，阶段结束汇总告知。确认版大纲/修改方案是内容变更的唯一依据；入口③未列入修改的页面以源 PPT 为准。制作阶段可以压缩措辞、拆分文字层级，但不能遗漏结论、数据和约束，也不能擅自改页数或顺序。

赶时间时可以主动授权**快速模式**：说“一次确认就行”会把需求、思路和大纲合并为一次确认；说“不用确认，直接做”会由 AI 补全需求和大纲并直接制作（主题仍需你提供，缺失数据不会被编造）。交付后的错别字、措辞、位置等微调会直接修改并重建，涉及结论、数据、页数等实质改动时才回到确认流程。详见 `skills\ppt-planner-maker\references\confirmation.md`。

制作路由规则（与上面的推荐表一致）：

| 公司模板 | 输出格式 / 用途 | 制作 Skill |
|---|---|---|
| 是 | 可编辑 PPTX | `ppt-master`（公司 deck 模板） |
| 否 | 可编辑 PPTX，商业或企业业务（用途未说明时的默认） | `ppt-master`（自由设计） |
| 否 | 可编辑 PPTX，个人学习研究且符合许可 | `gorden-ppt-skill` |
| 否 | HTML，明确要求杂志风 / 瑞士风 / 杂志感 / 设计感 | `guizang-ppt-skill` |
| 否 | HTML，其余需求 | `html-ppt` |

入口③（修改/美化现有 PPTX）固定输出可编辑 PPTX，走 `ppt-master` 的 Edit Native PPTX 或 Beautify；内容结构大改或换输出格式时转入口②。

成品交付前会按对应格式做检查：PPTX 检查页数、文字可编辑性、排版渲染；HTML 在真实浏览器中检查翻页、资源加载、配色和演讲者视图。

## 效果示例

`【只读】不同模型+skill组合效果示例/` 放了同一主题（TREMAC 与可信数据空间技术融合探索）在不同模型与 Skill 组合下的成品，包括 `ppt-master` 套/不套公司模板、`gorden-ppt-skill`、`html-ppt`、`guizang-ppt-skill` 以及 HTML/PPTX 两种格式，可用于选型时对比效果。

该目录为只读参考，请不要修改或删除其中的文件。

## 常见问题

**必须用公司模板，但想要 HTML 版？** 流程会提示二者冲突。公司模板路线只产出可编辑 PPTX，需要你修改其中一项要求。

**生成的 HTML 能直接发给别人吗？** 可以，但要连同项目内的 `assets/`、`images/` 一起发送并保持相对路径。若使用了 CDN 字体或外部图标，完全离线放映前需实际断网验证。

**为什么 Windows 上 `python3` 没反应？** Windows 可能只有 `python` 命令，或 `python3` 指向 Microsoft Store 的占位程序。改用 `python` 即可。

**Windows 中文路径下临时 PowerShell 脚本报“路径不存在”？** 无 BOM 的 UTF-8 `.ps1` 会被 Windows PowerShell 5.1 按系统 ANSI（中文环境为 GBK）读取，中文路径可能被误解析，甚至吞掉 `\` 并生成乱码目录。临时脚本请保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`。项目自身的 Python 制作流程不受影响。

**项目里的示例文件能改吗？** `【只读】不同模型+skill组合效果示例/` 是只读样例；自己的成品放在 `projects/` 下。

## 许可与商用范围

本仓库的授权是分层的：**原创部分非商业，第三方组件各按原许可证**。对外发布或商用前，请按下表逐项核对：

| 组件 | 许可证 / 来源 | 商业使用 |
|---|---|---|
| `skills/ppt-master` | MIT，Copyright (c) 2025-2026 Hugo He | 允许；保留版权声明与 `LICENSE`、`SPONSORS*.md` |
| `skills/html-ppt` | MIT，Copyright (c) 2026 lewis | 允许；保留版权声明 |
| `skills/guizang-ppt-skill` | AGPL-3.0，© 2026 op7418 | 允许；修改后分发或作为网络服务提供时，须按 AGPL 开放对应源码 |
| `skills/gorden-ppt-skill` 的脚本、`references/` 与元数据 | MIT，Copyright (c) 2026 GordenSun | 允许 |
| `skills/gorden-ppt-skill/templates/` 下的 `.pptx` 与模板预览图 | 第三方模板作者版权，非商业许可（见 `NOTICE.md`） | **禁止**；仅限个人学习与研究 |
| `skills/ppt-planner-maker/`、根目录文档与 `tests/` | CC BY-NC 4.0，Copyright (c) 2026 xztsummer（见 `LICENSE`） | **禁止**商业使用；非商业使用须署名并保留许可链接 |

完整条款见根目录 [`LICENSE`](LICENSE)（原创部分）与 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)（第三方组件）。

关于“禁止商用”的几点说明：

- **原创部分的“禁止商用”来自根目录 `LICENSE`**：`ppt-planner-maker`、README/AGENTS 与 `tests/` 采用 CC BY-NC 4.0，商业使用须另行取得书面授权；该许可不影响 `skills/` 下的第三方 Skill。
- **不要给 MIT / AGPL 组件追加“禁止商用”**：MIT 明确允许商业使用，AGPL-3.0 也允许商用（仅附带开源义务）。在上游代码上再写“禁止商用”，与上游许可证不一致，再分发时还会冲突。
- **分发本仓库时**：必须保留各目录下的 `LICENSE`、`NOTICE.md`、`SPONSORS*.md` 与版权声明，不得删除或改写；根目录 `LICENSE` 与 `THIRD_PARTY_NOTICES.md` 也应一并保留。
- **`gorden-ppt-skill` 的代码与模板是两套条款**：其 `LICENSE` 末尾已注明 MIT 仅覆盖代码，模板另见 `NOTICE.md`。README 中不要笼统写成“该 Skill 禁止商用”。

### 商用自查

| 你的用法 | 结论 |
|---|---|
| 用公司模板或 `ppt-master` 自由设计做客户提案、销售物料、企业内部经营汇报 | 可以（MIT） |
| 用 `gorden-ppt-skill` 的 21 套内置模板做上述任何商业用途 | **不可以**；改用 `ppt-master` 或公司模板 |
| 用 `guizang-ppt-skill` / `html-ppt` 做商业发布会、产品介绍 | 可以；但分发或改造 Skill 本身时须遵守 AGPL / MIT |
| 将 `ppt-planner-maker`、本仓库文档或 `tests/` 用于付费课程、付费产品 / 服务、客户交付 | **不可以**（CC BY-NC 4.0）；需取得维护者书面授权 |
| 在非商业分享、教学或研究中署名使用上述原创部分 | 可以；注明来源并附 CC BY-NC 4.0 许可链接 |
| 把本仓库打包出售、做成付费 SaaS，或作为付费课程附赠 | 逐项核对：原创部分禁止商用（CC BY-NC 4.0），MIT 部分须保留声明，AGPL 部分须开源，`gorden-ppt-skill` 模板不可包含 |

> 以上是使用层面的说明，不构成法律意见；正式商用前请以根目录 `LICENSE`、`THIRD_PARTY_NOTICES.md` 及各目录下的许可证原文为准，并注意 `ppt-master` 内置图标、音效等第三方资产的独立许可。
