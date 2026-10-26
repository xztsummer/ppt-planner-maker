# ppt-planner-maker

[中文](README.md) | **English**

An **orchestration-only** agent skill: it turns a presentation request into a confirmed page-by-page plan, then routes production to one of four external production skills that build editable PPTX or HTML.

> This repository ships no production engine. `ppt-master`, `gorden-ppt-skill`, `html-ppt` and `guizang-ppt-skill` are separate dependencies. See [docs/install.md](docs/install.md) and [references/dependencies.md](references/dependencies.md).

## What it does

- **Three entries**: plan an outline from a topic, build from an existing outline or source material, or edit/beautify an existing PPTX.
- **Staged confirmation**: requirements, narrative and the page-by-page outline/edit plan are shown in full before they are written; engine-internal artifacts go straight to the project workspace.
- **Orchestration only**: it does not draw slides or build decks. It hands the confirmed plan and constraints to the selected production skill, then checks the handoff and the deliverable.
- **Resolvable dependencies**: routing uses logical IDs; `scripts/resolve_skills.py` resolves physical roots. A missing dependency stops the branch with an install command instead of silently switching routes.
- **Portable**: the repository root is the skill, so a clone or symlink into a scanned skills root is enough. Runtime artifacts go to the user workspace, never into the skill package.

## Install

### 1. Install this skill

DSH user scope (recommended):

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.dsh/skills/ppt-planner-maker
```

Project scope on Windows (directory junction, no admin required):

```bat
mklink /J "<workspace>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

Project scope on macOS / Linux:

```bash
ln -s /path/to/ppt-planner-maker <workspace>/.dsh/skills/ppt-planner-maker
```

DSH discovers skills one level deep: `<root>/<name>/SKILL.md`. Do not wrap this repository in another `skills/` directory. Claude Code and other hosts follow the same rule for their own skills roots.

### 2. Install production dependencies

Install at least the dependencies for the branches you use; installing all four is fine. `<skills-dir>` is any skills root scanned by your host.

```bash
# Branches A / B / F; branch A requires this fork for the company decks
git clone https://github.com/xztsummer/ppt-master.git <skills-dir>/ppt-master

# Branch C
git clone https://github.com/GordenSun/GordenPPTSkill.git <skills-dir>/gorden-ppt-skill

# Branch D
git clone https://github.com/lewislulu/html-ppt-skill.git <skills-dir>/html-ppt

# Branch E
git clone https://github.com/op7418/guizang-ppt-skill.git <skills-dir>/guizang-ppt-skill
```

You can also keep dependencies in a custom directory and point the resolver at it:

```bash
# Windows PowerShell
$env:PPT_PLANNER_SKILLS_DIR = "D:\path\to\ppt-skills"
# macOS / Linux
export PPT_PLANNER_SKILLS_DIR="$HOME/path/to/ppt-skills"
```

### 3. Verify

```bash
python scripts/resolve_skills.py --check --branches A,B,C,D,E,F
```

Every dependency should report `OK`. On Windows, use `python` if `python3` opens the Microsoft Store stub. Missing items print an install command; see [references/dependencies.md](references/dependencies.md) for details.

## Quick start

Default flow (recommended for a first run):

> Make a 15-page presentation on "trusted data spaces" for a customer audience, 30 minutes, professional and concise.

Three entries:

- **① Plan an outline**: start from a topic or scattered material; research, align on the narrative, then plan page by page.
- **② Build from an existing outline**: keep the original order and meaning, fill page-level gaps, then produce. PDFs, screenshots and old PPTX files can be treated as source material.
- **③ Edit/beautify an existing PPTX**: either edit in place, or keep the content and redesign the visuals. The source file is never overwritten.

Outline only:

> Give me a page-by-page outline first; do not build the deck.

If you are in a hurry, explicitly authorize a fast mode:

> One confirmation is enough.

> Skip confirmation and build it.

Fast mode still resolves dependencies, shows the gorden license notice, runs downstream blocking checks and verifies the deliverable. The topic still has to come from you, and missing data is never invented. See [references/confirmation.md](references/confirmation.md).

## Routing summary

| Branch | Scenario | Production skill | Output |
|---|---|---|---|
| A | Company template required | `ppt-master` | Editable PPTX |
| B | No company template, professional and concise | `ppt-master` | Editable PPTX |
| C | No company template, rich and elaborate (default density) | `gorden-ppt-skill` | Editable PPTX |
| D | Regular HTML | `html-ppt` | HTML |
| E | Magazine / Swiss-style or explicit design intent | `guizang-ppt-skill` | HTML |
| F | Edit/beautify an existing PPTX | `ppt-master` | Editable PPTX |

The authoritative rules live in [SKILL.md](SKILL.md) §4; the table above is a summary.

Hard constraints:

- **A company template produces editable PPTX only.** If the user explicitly requires both a company template and HTML, ask them to change one requirement; do not silently rewrite it.
- **gorden built-in templates are non-commercial.** Branch C adds a license notice to the requirements table; obtain the template author's permission before commercial use.
- **guizang triggers only on real style intent.** Negations, design words quoted from source material, "rich and elaborate", or "premium/nice" alone do not trigger it.
- **HTML is not PowerPoint.** Do not rename HTML to `.pptx`, and do not claim it is editable.
- **A missing dependency stops the branch.** Report the ID, missing capability and install command; never guess a path or switch production skills.

## Dependency resolution

Production skills are not bundled. Before production, run:

```bash
python scripts/resolve_skills.py --workspace <workspace> --branches <selected branches> --json
```

Root precedence (first hit wins):

1. `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`
2. `<workspace>/.dsh/skills`
3. `<workspace>/.agents/skills`
4. `<workspace>/skills` (legacy layout)
5. `~/.dsh/skills`
6. `~/.agents/skills`
7. `~/.claude/skills`

The resolver also probes capabilities. Branch A, for example, requires `ppt-master`'s `templates/decks/中国电子云`; a directory without it is reported as `incomplete`, not usable. The full catalog and manual fallback are in [references/dependencies.md](references/dependencies.md).

## Workspace and artifacts

The target workspace defaults to the current session directory; an explicit user choice wins. **The skill package is read-only**; task artifacts never go into this repository.

```text
<workspace>/
└── projects/YYYYMMDDHHmm_topic/
    ├── 需求调研.md                    # requirements research
    ├── PPT规划思路.md                 # entry 1
    ├── PPT详细大纲_确认版.md           # entries 1 and 2
    ├── 修改方案_确认版.md              # entry 3
    ├── sources/                       # read-only copies of user material
    ├── versions/                      # confirmed-plan history
    ├── _draft/                        # optional unconfirmed drafts
    ├── YYYYMMDDHHmm_topic.pptx        # PPTX branch
    ├── YYYYMMDDHHmm_topic.html        # HTML branch
    ├── assets/ or images/             # local HTML assets
    └── _build/<skill-name>/           # production workspace and logs
```

If the current directory is the skill root (it contains `SKILL.md`), the orchestrator asks for a workspace instead of creating `projects/` inside the package.

## Repository layout

```text
ppt-planner-maker/
├── SKILL.md                 # runtime entry and routing table
├── references/
│   ├── intake.md            # requirements research
│   ├── planning.md          # narrative and page planning
│   ├── edit.md              # edit/beautify an existing PPTX
│   ├── production.md        # branches A–F playbooks
│   ├── confirmation.md      # confirmation, fast mode, post-delivery edits
│   └── dependencies.md      # external dependency install, resolution, licenses
├── scripts/
│   ├── deps.json            # machine-readable dependency catalog
│   └── resolve_skills.py    # dependency root/capability resolver
├── docs/
│   ├── install.md           # install and host discovery
│   ├── migration.md         # migrate from 0.9 and the old workspace layout
│   └── design.md            # maintainers: single source of truth and extension
├── tests/                   # Python unit tests
├── README.md / README.en.md
├── AGENTS.md                # repository development conventions
├── VERSION / CHANGELOG.md
├── LICENSE                  # CC BY-NC 4.0 for original parts
└── THIRD_PARTY_NOTICES.md   # external dependency license matrix
```

`evals/` is a local routing evaluation directory and is not distributed with the repository; see [docs/design.md](docs/design.md).

## Development and verification

```bash
# Static checks: frontmatter, relative links, routing consistency, forbidden paths
python scripts/check_skill.py

# Unit tests for the resolver and the checker
python -m unittest discover -s tests
```

When routing changes, follow the sync checklist in [docs/design.md](docs/design.md): update `SKILL.md`, `production.md`, the README summary and local `evals/cases.md`, then run the checks above. CI is optional; the repository uses only the Python standard library.

## FAQ

**The skill is not discovered after cloning.** It is not inside a scanned skills root. Put it at `~/.dsh/skills/ppt-planner-maker`, or create a junction/symlink at `<workspace>/.dsh/skills/ppt-planner-maker`. DSH scans one level only.

**A dependency is reported missing.** Run `python scripts/resolve_skills.py --workspace <workspace> --branches A` and install what it prints, or pass an existing dependency directory via `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`. Do not guess paths.

**`python3` does nothing on Windows.** Use `python`; `python3` may be the Microsoft Store stub.

**Can I send the generated HTML to someone?** Yes, but include the project's `assets/` or `images/` and keep relative paths. If it uses CDN fonts or icons, test offline playback before promising it works offline.

**I need a company template and HTML.** That is a conflict. The company-template route produces editable PPTX only; one requirement has to change.

**Do old `skills\ppt-master` prompts still work?** Not recommended. Dependencies are external now; install them and use skill names. See [docs/migration.md](docs/migration.md).

**Can I commit `projects/` or deliverables back into the repository?** Please don't. The repository is the skill package; keep runtime artifacts in the workspace. `.gitignore` already excludes them.

## License

Original parts of this repository (`SKILL.md`, `references/`, `scripts/`, `docs/`, `tests/` and root documents) are licensed under [CC BY-NC 4.0](LICENSE): personal study, research, teaching and non-commercial exchange are allowed; **commercial use is prohibited** without prior written permission.

External production skills are **not distributed** with this repository and keep their own licenses:

| Dependency | License | Commercial use |
|---|---|---|
| `ppt-master` (including company decks) | MIT | Allowed; company logos/trademarks are not granted by MIT |
| `gorden-ppt-skill` code | MIT | Allowed |
| `gorden-ppt-skill` templates/assets | Non-commercial | **Prohibited**; personal study/research only |
| `html-ppt` | MIT | Allowed |
| `guizang-ppt-skill` | AGPL-3.0 | Allowed; modified distribution or network use requires source disclosure |

Commercial self-check:

| Your use | Verdict |
|---|---|
| Use this skill for paid client work, paid products or courses | **Not allowed** (CC BY-NC 4.0); written permission required |
| Use `ppt-master` / `html-ppt` to build a commercial deck | Allowed (MIT); keep copyright notices |
| Use `gorden-ppt-skill` built-in templates for a commercial deck | **Not allowed**; personal study/research only |
| Use `guizang-ppt-skill` for a commercial deck | Allowed; follow AGPL when distributing modifications |
| Sell this repository or run it as a paid SaaS | **Not allowed**; check dependencies separately |

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the full terms. This is not legal advice; consult the original licenses before commercial use.

## Upstream and credits

- [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) (MIT) and [xztsummer/ppt-master](https://github.com/xztsummer/ppt-master) (customized fork)
- [GordenSun/GordenPPTSkill](https://github.com/GordenSun/GordenPPTSkill)
- [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill)
- [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)

This repository maintains only the orchestration layer; production capabilities, templates and assets belong to their respective upstream authors.
