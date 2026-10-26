# ppt-agent-kit

[中文](README.md) | **English**

An agent-skill toolkit for AI assistants that carries a deck from requirement research through outlining, production and revision, and delivers editable PPTX or HTML presentations.

**PPT Agent Kit** bundles five agent skills and works in any AI tool that supports Agent Skills, such as ZCode or Claude Code. Describe a topic, supply materials, or request changes in natural language; the assistant researches the requirement, plans and confirms the outline, then calls the right production skill to build and verify the deck.

- **From topic to finished deck**: plan from scratch, build from an existing outline, or revise and beautify an existing PPTX.
- **Several production routes**: corporate templates, free design, 21 built-in Chinese templates, plus conventional, magazine-style and Swiss-style web decks.
- **Two output formats**: editable PowerPoint (`.pptx`) or an HTML web deck, chosen per request.
- **One orchestrated workflow**: `ppt-planner-maker` runs the process by default and archives requirements, confirmed drafts, source material and deliverables per task; once familiar with the flow you can call a production skill directly.

Clone the repository, open the project folder in an AI tool that supports Agent Skills, and follow the steps below. Model calls and some enhanced features need network access; documents and deliverables are generated and saved locally.

> ⚠️ **Before commercial use**: the original parts of this repository (`ppt-planner-maker`, the root documents and `tests/`) are licensed **CC BY-NC 4.0 — no commercial use**; the built-in templates and assets of `gorden-ppt-skill` are non-commercial as well. Other third-party components follow their own licenses: `ppt-master` and `html-ppt` are MIT, `guizang-ppt-skill` is AGPL-3.0. See [License and commercial scope](#license-and-commercial-scope), [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

> This file is the English translation of [`README.md`](README.md). The Chinese README is the default, and the license files take precedence over any wording here.

## [Experienced users] Pick a skill first (recommended reading)

**Recommended: if you already know your way around, call a skill manually.** Skip the default research-and-planning orchestration and issue a single production request — this is the fastest route.

Typical cases:

| Scenario / requirement | Recommended skill | Output format |
|---|---|---|
| Strictly apply a corporate template (China Electronics Cloud, China Telecom, CATARC, …) | `skills\ppt-master` | Editable PPTX |
| Free-form PPTX design (default for commercial or corporate use), or revise / beautify an existing PPTX | `skills\ppt-master` | Editable PPTX |
| Personal study or research using the built-in Chinese templates (21 elaborate / minimal templates, non-commercial) | `skills\gorden-ppt-skill` | Editable PPTX |
| Reporting, slide-like decks, conventional presentations | `skills\html-ppt` | HTML |
| Magazine style, Swiss style, design-led decks, talks and sharing sessions | `skills\guizang-ppt-skill` | HTML |

If you have no strong preference, just describe the requirement in natural language. As agreed in `AGENTS.md`, the project runs `skills\ppt-planner-maker` by default: it researches the requirement, plans the outline or revision, routes the job to the appropriate production skill above, and drives the build.

A few constraints:

- **Strict corporate templates only produce editable PPTX**, never HTML at the same time; when the two conflict, the workflow asks you to adjust one of the requirements.
- The built-in templates and assets of `gorden-ppt-skill` are **for personal study and research only — no commercial use**. For commercial decks, client proposals or internal business reporting, switch to `ppt-master` free design or a corporate template.
- HTML is a web presentation, not PowerPoint. Do not rename an HTML file to `.pptx`.

### Example production requests

**Free-form PPTX (ppt-master)**

```text
Use the skills\ppt-master skill.
Read the source file `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md` and generate a presentation that can be projected as-is, based on its full content.
Keep the overall style clean, professional and premium: white background with a tech-blue palette, hex #0058FF.
Write the final file to the /output directory and name it: TREMAC与可信数据空间技术融合探索_qoder+ds41flash+pptmatster.pptx
```

**Magazine-style / design-led HTML (guizang-ppt-skill)**

```text
Use the skills\guizang-ppt-skill skill.
Read the source file `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md` and generate a presentation that can be projected as-is, based on its full content.
Keep the overall style clean, professional and premium: white background with a tech-blue palette, hex #0058FF.
Write the final file to the /output directory and name it: TREMAC与可信数据空间技术融合探索_wb+minimax31+guizang
```

**Corporate template PPTX (ppt-master + China Electronics Cloud deck)**

```text
Use the skills\ppt-master skill
and the skills\ppt-master\templates\decks\中国电子云 deck template.
Read the source file `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md` and generate a presentation that can be projected as-is, based on its full content.
Keep the overall style clean, professional and premium.
Write the final file to the /output directory and name it: TREMAC与可信数据空间技术融合探索_中国电子云_qoder+ds41flash+pptmatster.pptx
```

**Elaborate, high-end PPTX (gorden-ppt-skill)**

```text
Use the skills\gorden-ppt-skill skill.
Read the source file `references\TREMAC与可信数据空间技术融合探索_10页发言稿.md` and generate a presentation based on its full content.
Make the deck elaborate, high-end, professional and premium: white background with a tech-blue palette, hex #0058FF.
Write the final file to the /output directory and name it: TREMAC与可信数据空间技术融合探索_qoder+ds41flash+gordenppt豪华蓝.pptx
```

The output directory, file name and source file are all replaceable; for the HTML routes it is a good idea to append an explicit `.html` extension to the file name.

## [General users] Quick start

### 1. Prepare the environment

Clone the repository and open the `ppt-agent-kit` folder in your AI tool:

```bash
git clone https://github.com/xztsummer/ppt-agent-kit.git
cd ppt-agent-kit
```

Requirements:

- An AI tool that supports Agent Skills (ZCode, Claude Code, Cursor, …)
- Python 3.10+ (runs the production scripts of `ppt-master` and `gorden-ppt-skill`)
- Node.js 18+ (optional; used by the presenter mode and Swiss deck validation scripts of guizang)
- Google Chrome (optional; renders HTML pages to PNG for visual checks)

### 2. Install dependencies

```bash
pip install -r skills/ppt-master/requirements.txt
```

Most scripts in `ppt-master` only use the standard library; the dependencies above enable SVG-to-PPTX conversion, PDF/Word/Excel parsing, AI image generation, narration audio and other enhanced features. The `python-pptx` package required by `gorden-ppt-skill` is included as well.

### 3. Drop in source material (optional)

Put reference documents, old decks, images and so on into `references/`, then simply mention the file name in the conversation. Source material is used read-only and never overwritten.

### 4. Ask the assistant

Default flow (recommended for a first run):

> Build a 15-slide deck on "Trusted Data Space" for a client audience, 30-minute talk, professional and clean style.

Calling a skill manually:

> Use ppt-master, strictly apply the China Electronics Cloud corporate template, and turn `references/方案.docx` into a 20-slide business deck.

> Use guizang-ppt-skill to make a magazine-style web deck about "AI and design" for an offline talk.

> Use html-ppt to make an 8-slide technical sharing deck in a white-background tech-blue style.

### 5. Confirm and generate

The default flow **shows the full content in the conversation** stage by stage; documents are written to disk only after you confirm, before the next stage begins:

1. Confirm the requirement (topic, audience, duration, template requirements, output format, visual style)
2. Confirm the plan (narrative spine, sections, page count, time allocation; skipped when you already have an outline or are revising an existing PPTX)
3. Confirm the outline or revision plan page by page (title, conclusion, content and presentation notes per page, or a page-by-page change list)
4. Automatic routing to the production skill, build and verification

### 6. Collect the deliverable

Everything is archived under `projects/` as `YYYYMMDDHHmm_主题名/`, with the deliverable named after the directory:

```text
projects/202610220848_可信数据空间/
├── 需求调研.md
├── PPT规划思路.md                     # entry ①
├── PPT详细大纲_确认版.md               # entries ①②
├── 修改方案_确认版.md                  # entry ③
├── sources/                           # read-only copies of user material (original file names)
├── versions/                          # history of confirmed drafts
├── _draft/                            # optional: unconfirmed drafts
├── 202610220848_可信数据空间.pptx     # PPTX route
├── 202610220848_可信数据空间.html     # HTML route; both delivered when dual format is requested
├── assets/ or images/                 # local HTML resources, if any
└── _build/<skill 名>/                 # build workspace and intermediates (render previews, validation reports)
```

## Repository layout

```text
ppt-agent-kit/
├── AGENTS.md                  # default routing when no skill is named
├── README.md                  # Chinese (default)
├── README.en.md               # English
├── LICENSE                    # license for the original parts: CC BY-NC 4.0 (non-commercial)
├── THIRD_PARTY_NOTICES.md     # licenses and commercial limits of the third-party skills
├── skills/
│   ├── ppt-planner-maker/     # orchestration: research → outline/revision plan → confirm → build (default)
│   ├── ppt-master/            # PPTX: corporate templates / free design / template extraction / beautify
│   ├── gorden-ppt-skill/      # PPTX: 21 built-in Chinese templates
│   ├── html-ppt/              # HTML: 36 themes, 36 layouts, presenter mode
│   └── guizang-ppt-skill/     # HTML: e-magazine / Swiss International Style
├── references/                # your reference material
├── projects/                  # documents and deliverables archived per task
└── 【只读】不同模型+skill组合效果示例/   # sample outputs from the same topic under different model+skill combos
```

## Skill capabilities at a glance

### ppt-master

Native editable PPTX workflow, suited to corporate templates and formal business settings. Five routes:

- **Generate PPTX**: build a new deck from material or a topic, with an "elaborate / premium" or "professional / clean" preference
- **Beautify**: 1:1 visual upgrade of an existing PPTX without changing its content structure
- **Image to PPTX**: rebuild page images as editable objects
- **Create Template**: extract reusable Brand / Style / Layout / Deck templates from PPTX files, images or brand assets
- **Edit Native PPTX**: fill new content into an existing `.pptx`, leaving untouched pages byte-for-byte identical

`templates/decks/` ships corporate templates for China Electronics Cloud, China Telecom, CATARC and others. Output uses native shapes, charts, tables, formulas and master inheritance rather than full-page screenshots. Dependencies live in `skills/ppt-master/requirements.txt`; an attribution check script runs before first use.

### gorden-ppt-skill

Ships **21 Chinese PPT templates** covering work reports, year-end reviews, promotion defenses, project retrospectives, thesis proposals, business proposals, teaching material and data visualization. The core capability is **replacing text only, without disturbing the original layout, palette or font sizes**, backed by text-box overflow detection and same-level heading size consistency checks; original minimal layouts are also supported.

On first use the skill runs `python3 scripts/apply_update.py` for an incremental update; on Windows, use `python` if `python3` is unavailable. **Note: the non-commercial restriction applies only to its built-in templates and assets — the code is MIT.**

### html-ppt

Pure static HTML presentations, no build step:

- 36 themes, 15 full decks, 36 page layouts, 47 animations (27 CSS + 20 Canvas FX)
- Keyboard paging, touch swipe, presenter mode on the `S` key (current slide / next slide / speaker notes / timer)
- Single-file HTML, fonts from CDN with system-font fallback when offline
- Bundled headless Chrome screenshot script (`scripts/render.sh` — the Chrome path is hard-coded for macOS and needs adjusting on Windows)

Suited to reporting, technical sharing, product introductions and other slide-like scenarios.

### guizang-ppt-skill

Single-file horizontal-paging HTML deck with two visual directions:

- **E-magazine × e-ink**: serif headlines, WebGL fluid/contour backgrounds, warm tones — for humanities talks, industry observations and product launches
- **Swiss International Style**: sans-serif type, grid dot patterns, high-contrast functional colours (IKB blue / lemon yellow / lime green / safety orange) — for tech products, data reporting and design-engineering talks

Supports presenter view, synced audience screen, speaker notes, section covers, big-number statements, laser pointer and annotation. Suited to offline talks, launches, demo days and other talk formats with a strong personal style; heavy tables and dense training content are not a good fit.

## The default workflow

`skills\ppt-planner-maker` is the orchestration skill. It does not draw pages itself; it turns "an idea" into an executable production task. Three entry points:

- **Entry ①: plan a deck outline** — start from a topic, research the requirement, align on the approach, plan page by page, build after confirmation
- **Entry ②: ready outline, build directly** — keep the original order and intent of your outline, fill in the per-page production details, then build
- **Entry ③: revise / beautify an existing PPTX** — incrementally edit while preserving the original layout, or redesign the layout while preserving the content; the source file is never overwritten

The process follows staged confirmation: requirement, plan and page-by-page outline/revision documents are shown in full in the conversation and only written to disk after you explicitly confirm; internal spec files, SVGs, build logs and validation reports are written straight into the project workspace and summarised at the end of each stage. The confirmed outline/revision plan is the single source of truth for content changes; for entry ③ any page not listed in the change list follows the source deck. The production stage may tighten wording and split text into levels, but must not drop conclusions, data or constraints, nor silently change page count or order.

When time is short you can explicitly authorise **fast mode**: "one confirmation is enough" merges requirement, approach and outline into a single confirmation; "no confirmation, just build" lets the assistant complete the requirement and outline and build straight away (you still provide the topic, and missing data is never invented). After delivery, typos, wording and positioning are fixed and rebuilt directly; substantive changes to conclusions, data or page count go back through confirmation. See `skills\ppt-planner-maker\references\confirmation.md`.

Routing rules (consistent with the recommendation table above):

| Corporate template | Output format / use | Production skill |
|---|---|---|
| Yes | Editable PPTX | `ppt-master` (corporate deck template) |
| No | Editable PPTX, commercial or corporate business (the default when unspecified) | `ppt-master` (free design) |
| No | Editable PPTX, personal study or research within the license | `gorden-ppt-skill` |
| No | HTML, explicitly magazine / Swiss / editorial / design-led | `guizang-ppt-skill` |
| No | HTML, anything else | `html-ppt` |

Entry ③ (revise / beautify an existing PPTX) always outputs editable PPTX through `ppt-master`'s Edit Native PPTX or Beautify; a major structural change or a different output format moves the job to entry ②.

Before delivery the deck is checked according to its format: for PPTX, page count, text editability and render layout; for HTML, paging, resource loading, palette and presenter view in a real browser.

## Examples

`【只读】不同模型+skill组合效果示例/` holds outputs for one topic (TREMAC and trusted data space technology convergence) produced by different model and skill combinations: `ppt-master` with and without a corporate template, `gorden-ppt-skill`, `html-ppt`, `guizang-ppt-skill`, in both HTML and PPTX. Use it to compare options when choosing a route.

That directory is a read-only reference — please do not modify or delete its files.

## FAQ

**I must use a corporate template but also want an HTML deck?** The workflow flags the conflict. The corporate-template route only produces editable PPTX, so one of the two requirements has to change.

**Can I send the generated HTML to someone else?** Yes, but ship the project's `assets/` or `images/` folders with it and keep relative paths intact. If CDN fonts or external icons are used, verify real offline playback by actually disconnecting the network before presenting.

**Why does `python3` do nothing on Windows?** Windows may only provide the `python` command, or `python3` may point to the Microsoft Store stub. Use `python` instead.

**A temporary PowerShell script fails on a Windows path containing Chinese characters?** Windows PowerShell 5.1 reads a BOM-less UTF-8 `.ps1` as the system ANSI code page (GBK on Chinese Windows). The path may be misdecoded, sometimes swallowing the `\` separator and creating a mojibake directory. Save temporary scripts as UTF-8 with BOM, or use Python / `-EncodedCommand`. The project's Python pipeline is unaffected.

**Can I edit the sample files in the project?** `【只读】不同模型+skill组合效果示例/` is a read-only sample set; keep your own deliverables under `projects/`.

## License and commercial scope

Licensing is layered: **the original parts are non-commercial, third-party components follow their own licenses**. Before publishing or using anything commercially, check each item:

| Component | License / source | Commercial use |
|---|---|---|
| `skills/ppt-master` | MIT, Copyright (c) 2025-2026 Hugo He | Allowed; keep the copyright notice and the `LICENSE` / `SPONSORS*.md` files |
| `skills/html-ppt` | MIT, Copyright (c) 2026 lewis | Allowed; keep the copyright notice |
| `skills/guizang-ppt-skill` | AGPL-3.0, © 2026 op7418 | Allowed; if you modify and distribute it, or offer it as a network service, you must publish the corresponding source under the AGPL |
| `skills/gorden-ppt-skill` scripts, `references/` and metadata | MIT, Copyright (c) 2026 GordenSun | Allowed |
| `.pptx` files and template preview images under `skills/gorden-ppt-skill/templates/` | Copyright of the third-party template authors, non-commercial (see `NOTICE.md`) | **Not allowed**; personal study and research only |
| `skills/ppt-planner-maker/`, the root documents and `tests/` | CC BY-NC 4.0, Copyright (c) 2026 xztsummer (see `LICENSE`) | **No commercial use**; non-commercial use requires attribution and a link to the license |

Full terms: [`LICENSE`](LICENSE) (original parts) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) (third-party components).

Notes on "non-commercial":

- **The non-commercial restriction on the original parts comes from the root `LICENSE`**: `ppt-planner-maker`, the root README/AGENTS documents and `tests/` are CC BY-NC 4.0, and commercial use requires separate written permission. That license does not affect the third-party skills under `skills/`.
- **Do not add "non-commercial" terms to MIT / AGPL components**: MIT explicitly permits commercial use, and AGPL-3.0 permits it too (with source-disclosure obligations). Writing "non-commercial" on top of upstream code is inconsistent with the upstream license and will conflict on redistribution.
- **When redistributing this repository**: keep the `LICENSE`, `NOTICE.md`, `SPONSORS*.md` files and copyright notices in each directory — do not remove or rewrite them. The root `LICENSE` and `THIRD_PARTY_NOTICES.md` should be kept as well.
- **`gorden-ppt-skill` has two sets of terms**: its `LICENSE` states at the end that MIT covers the code only, with templates covered separately by `NOTICE.md`. Do not describe the whole skill as "non-commercial" in documentation.

### Commercial self-check

| Your usage | Verdict |
|---|---|
| Client proposals, sales material or internal business reporting with a corporate template or `ppt-master` free design | Allowed (MIT) |
| Any of the above using the 21 built-in templates of `gorden-ppt-skill` | **Not allowed**; use `ppt-master` or a corporate template instead |
| Commercial launches or product intros with `guizang-ppt-skill` / `html-ppt` | Allowed; but redistributing or modifying the skill itself must follow AGPL / MIT |
| Paid courses, paid products/services or client delivery using `ppt-planner-maker`, these documents or `tests/` | **Not allowed** (CC BY-NC 4.0); written permission from the maintainer is required |
| Non-commercial sharing, teaching or research with attribution | Allowed; credit the source and link to the CC BY-NC 4.0 license |
| Selling this repository as a bundle, a paid SaaS, or a bonus in a paid course | Check item by item: the original parts are non-commercial (CC BY-NC 4.0), MIT parts must retain notices, AGPL parts must be open-sourced, and the `gorden-ppt-skill` templates must not be included |

> The above describes usage, not legal advice. Before commercial use, defer to the root `LICENSE`, `THIRD_PARTY_NOTICES.md` and the license texts in each component directory, and note that third-party assets bundled with `ppt-master` (icons, sound effects, etc.) may carry their own licenses.
