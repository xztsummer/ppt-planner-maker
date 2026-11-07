# ppt-planner-maker

[中文](README.md) | **English**

An **orchestration-only** agent skill: it turns a presentation request into a confirmed page-by-page plan, then routes production to one of four external production skills that build editable PPTX or HTML.

> This repository ships no production engine. `ppt-master`, `gorden-ppt-skill`, `html-ppt` and `guizang-ppt-skill` are separate dependencies. See [docs/install.md](docs/install.md) and [references/dependencies.md](references/dependencies.md).

## What it does

- **Three entries**: plan an outline from a topic, build from an existing outline or source material, or edit/beautify an existing PPTX.
- **Scenario first, route second**: ask what the deck is for, who will see it, and what feeling is wanted. Scenarios such as promotion/interview, thesis defense, teaching/lesson planning, Party/government, annual review, retrospective, data visualization and operations match gorden's template library, so the default recommendation is gorden (built-in template mode A) with exactly 3 preview candidates plus “show another batch”; when the host cannot embed images, it gives absolute `preview.png` paths. If the scenario does not match or you want full customization, choose company deck / ready-made template / free design. "You decide" maps to gorden when the scenario matches, otherwise free design.
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

Claude Code user scope:

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.claude/skills/ppt-planner-maker
```

ZCode user scope:

```bash
git clone https://github.com/xztsummer/ppt-planner-maker.git ~/.zcode/skills/ppt-planner-maker
```

Project scope on Windows (directory junction, no admin required):

```bat
mklink /J "<workspace>\.dsh\skills\ppt-planner-maker" "D:\path\to\ppt-planner-maker"
```

Project scope on macOS / Linux:

```bash
ln -s /path/to/ppt-planner-maker <workspace>/.dsh/skills/ppt-planner-maker
```

DSH discovers skills one level deep: `<root>/<name>/SKILL.md`. Do not wrap this repository in another `skills/` directory. ZCode uses the same shape: install to `~/.zcode/skills/ppt-planner-maker` or `<workspace>/.zcode/skills/ppt-planner-maker`. Claude Code and other hosts follow the same rule for their own skills roots.

### 2. Install production dependencies

Install at least the dependencies for the branches you use; installing all four is fine. `<skills-dir>` is any skills root scanned by your host. No company deck is bundled: branch A needs at least one deck when using an installed deck (the fork ships 中国电子云 / 中国电信 / 中汽研). A user-supplied `.pptx` template plus new content defaults to Edit Native and does not require an installed deck.

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

### 2.1 Install Python runtime dependencies

`git clone` only installs the engine; PPTX branches also need Python packages:

```bash
# Branches A / B / F (ppt-master)
python -m pip install -r <skills-dir>/ppt-master/requirements.txt

# Branch C (gorden)
python -m pip install python-pptx
```

Branches D / E have no Python runtime dependencies. Inside `requirements.txt`, `edge-tts` and `PyMuPDF` are optional; PyMuPDF is AGPL-3.0. Visual PPTX checks and legacy `.ppt` conversion need LibreOffice (`soffice`); when it is not on PATH the checker looks in common install locations.

### 2.2 One-command install (recommended)

Prefer not to clone and pip by hand? Preview the plan first (read-only, installs nothing):

```bash
python "<skill-dir>/scripts/setup.py" --workspace <workspace> --branches A,F
```

Happy with it? Re-run with `--yes`: missing dependencies are `git clone`d into the private directory `~/.ppt-planner/skills` and pinned to the tested commits in `deps.json`; missing Python packages are installed with `pip`. Hosts do not scan that directory, so only this orchestrator answers "make a PPT" instead of a production skill taking the request; production skills are loaded by absolute path. Override the location with `--skills-dir` or `PPT_PLANNER_HOME`, and use `--latest` for upstream HEAD. System-level components (LibreOffice, browsers) are reported, never installed. **Installation only happens after you say yes.**

### 3. Verify

```bash
python "<skill-dir>/scripts/doctor.py" --workspace <workspace> --branches A,B,C,D,E,F
```

`doctor.py` is read-only and combines path, capability and runtime checks into one verdict. Install what "next step" says and rerun. For individual diagnosis:

```bash
python "<skill-dir>/scripts/resolve_skills.py" --check --branches A,B,C,D,E,F
python "<skill-dir>/scripts/check_runtime.py" --check --branches A,B,C,D,E,F
```

`<skill-dir>` is the repository root containing `SKILL.md`, not the current workspace. An `OK` path check only means the directory is ready; the runtime check must pass for the branch to build. On Windows, use `python` if `python3` opens the Microsoft Store stub.

## Quick start

On the first run it asks what the deck is for, who will see it, what feeling is wanted, and whether to deliver PPTX or HTML. Choose editable PPTX (the default) when others need to keep editing it or it must move through company workflows; choose web HTML for live playback, online sharing, or animation (it cannot be edited in PowerPoint). For example:

```text
Scenario: promotion/interview / thesis defense / teaching or lesson planning / Party or government / annual review / retrospective / data visualization / operations review / client proposal / other
Feeling: formal / clean / rich and luxurious / design-forward / no preference
Output: editable PPTX (default, for further editing and company workflows) / web HTML (for playback, sharing and animation; not editable in PowerPoint)
```

If the scenario matches gorden's 21 Chinese templates, the default recommendation is option 2, with exactly 3 template previews and “show another batch”; hosts that cannot embed images show absolute `preview.png` paths instead. You can also say "free design" or "use our company template". If you already know the production route, choose directly:

```text
1. Company deck (you already have your company's brand template, or the matching deck is installed)
2. Ready-made design template (gorden's built-in library: fixed colors, may contain sample data, no new layouts, sample numbers may be undeletable, commercial use needs permission)
3. Free design (fully editable; pick option 1 if you have a company template, otherwise this one if unsure)
```

You do not need to remember branches A–F, deck or gorden; those are internal names. Just say what the deck is for, who will see it, whether you want PPTX or HTML, and what feeling you want. If unsure, say "you decide"; the scenario decides the recommendation.

When the scenario matches, the recommendation is gorden mode A (built-in template). Its original mode C is explicitly simple and cannot carry a scenario template or a luxurious deck. If you also insist on "no template", you choose once between gorden's simple original mode C and ppt-master's free design. "Complex/luxurious" works the same way and defaults to option 2.

If you have a company `.pptx` template file, give the file path and say "use this template". The planner defaults to ppt-master Edit Native PPTX to fill new content. Create Template is used only for an explicitly requested reusable workspace or a `.potx` that cannot be filled directly. Do not pick option 2, which means gorden's built-in library.

You can also state it up front:

> Make a 15-page presentation on "trusted data spaces" for a customer audience, 30 minutes, free design, professional and concise.

Three entries:

- **① Plan an outline**: start from a topic or scattered material; research, align on the narrative, then plan page by page.
- **② Build from an existing outline**: keep the original order and meaning, fill page-level gaps, then produce. PDFs, screenshots and old PPTX files can be treated as source material.
- **③ Edit/beautify an existing PPTX**: either edit in place, or keep the content and redesign the visuals. The source file is never overwritten.

Outline only:

> Give me a page-by-page outline first; do not build the deck.

If you are in a hurry, fast mode has two different levels:

| You say | Level | Result |
|---|---|---|
| "One confirmation is enough" / "Hurry up, don't ask too much" | Merged confirmation | All documents shown once, one confirmation; you still approve |
| "Skip confirmation, just build it" / "You decide everything" | Direct build | Shown once, then built without waiting for approval |

Authorizing a single field does not enter fast mode:

> You decide the route. → Only the route is decided; standard confirmation still applies.

For "you figure it out" / "whatever", the agent asks once whether you want merged confirmation or full delegation; it does not upgrade by itself.

Fast mode still resolves dependencies, shows the gorden license notice, runs downstream blocking checks and verifies the deliverable. The topic still has to come from you, and missing data is never invented. See [references/confirmation.md](references/confirmation.md).

## Routing summary

| Branch | Trigger | Production skill | Output |
|---|---|---|---|
| A | Route = company deck | `ppt-master` | Editable PPTX |
| B | Route = free design (explicit) | `ppt-master` | Editable PPTX |
| C | Route = ready-made design template (gorden's built-in library); or PPTX + scenario matches gorden's library / "complex/luxurious" (recommended default, mode A) | `gorden-ppt-skill` | Editable PPTX |
| D | HTML, regular | `html-ppt` | HTML |
| E | HTML, magazine / Swiss-style; "design sense" alone asks D/E first | `guizang-ppt-skill` | HTML |
| F | Edit/beautify an existing PPTX | `ppt-master` | Editable PPTX |

The authoritative rules live in [SKILL.md](SKILL.md) §4; the table above is a summary.

Hard constraints:

- **The company-deck route produces editable PPTX only.** If the user explicitly requires both a company deck and HTML, ask them to change one requirement; do not silently rewrite it.
- **There is no default company deck.** If the route is unstated, ask what the deck is for and what feeling is wanted; only when the scenario does not match gorden and there is no "complex/luxurious" preference do you ask the three-way question. Never silently apply a brand deck. "Complex/luxurious" is a signal for gorden branch C, not a reason to use a company deck. If the user hands over a `.pptx` template plus new content, default to ppt-master Edit Native PPTX; use Create Template only for an explicit reusable workspace or a `.potx` that cannot be filled directly.
- **Scenario recommendation is not hard routing.** Promotion/interview, thesis defense, teaching, Party/government, annual review, retrospective, data visualization and operations match gorden, but the skill only recommends branch C mode A and shows exactly 3 previews, “show another batch”, the non-commercial license and capability limits; hosts without inline images show absolute `preview.png` paths. If the user declines or wants full customization, switch to ppt-master free design. Explicit routes and company templates still win.
- **gorden built-in templates are non-commercial.** Branch C (ready-made template, scenario match or the complex/luxurious default) adds a license notice to the requirements table; obtain the template author's permission before commercial use. Mode C original uses no template assets but is simple by design.
- **gorden's scenario templates and rich look come from its built-in templates.** Both default to gorden mode A (built-in template); original mode C is explicitly simple and cannot carry them. If the user insists on no template while also requiring complex/luxurious or "like the ready-made template" effects, choose once between "accept simple mode C" and "switch to ppt-master free design"; never downgrade silently. If they only reject templates without requiring the template effect, treat it as free design without forcing a two-way choice.
- **guizang triggers only on real style intent.** Negations, design words quoted from source material, "rich and elaborate" (HTML context), or "premium/nice" alone do not trigger it; the PPTX "complex/luxurious" case follows branch C.
- **HTML is not PowerPoint.** Do not rename HTML to `.pptx`, and do not claim it is editable.
- **A missing dependency stops the branch.** Report the ID, missing capability and install command; never guess a path or switch production skills.

## Dependency preflight

Production skills are not bundled. **Once the branch is known, before page planning**, run a read-only preflight; do not wait until after three confirmation rounds.

```bash
python "<skill-dir>/scripts/doctor.py" --workspace <workspace> --branches <selected branches>
```

`doctor.py` is read-only and combines installation, capability and runtime checks into one verdict; install what "next step" says and rerun. For individual diagnosis:

```bash
python "<skill-dir>/scripts/resolve_skills.py" --workspace <workspace> --branches <selected branches> --brief
python "<skill-dir>/scripts/check_runtime.py" --branches <selected branches> --brief
```

The first checks installation and capabilities; the second checks Python packages and commands. `--brief` prints one line; use `--json` for diagnosis. Re-run both with the final workspace before production. Runtime metadata lives in the `runtime` field of `scripts/deps.json`.

Root precedence (first hit wins):

1. `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`
2. `<workspace>/.dsh/skills`
3. `<workspace>/.zcode/skills`
4. `<workspace>/.agents/skills`
5. `<workspace>/skills` (legacy layout)
6. `~/.ppt-planner/skills` (default `setup.py` target, not scanned by hosts)
7. `~/.dsh/skills`
8. `~/.zcode/skills`
9. `~/.agents/skills`
10. `~/.claude/skills`

The resolver also probes capabilities. Branch A, for example, requires at least one deck under `ppt-master`'s `templates/decks/` when an installed deck is selected; a directory without any deck is reported as `incomplete`, not usable. For a user-supplied company `.pptx` / `.potx`, add `--company-template-file` to preflight so no installed deck is required. The full catalog and manual fallback are in [references/dependencies.md](references/dependencies.md).

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
│   ├── resolve_skills.py    # dependency root/capability resolver
│   ├── check_runtime.py     # Python package / command runtime probe
│   ├── doctor.py            # one-command readiness summary
│   ├── setup.py             # installer (plan-only by default; private root, pinned)
│   ├── clean_deck.py        # remove unreachable OPC parts into a new output
│   └── verify_deck.py       # finished-deck structural check
├── docs/
│   ├── install.md           # install and host discovery
│   ├── migration.md         # migrate from 0.9 and the old workspace layout
│   └── design.md            # maintainers: single source of truth and extension
├── README.md / README.en.md
├── AGENTS.md                # repository development conventions
├── VERSION / CHANGELOG.md
├── LICENSE                  # CC BY-NC 4.0 for original parts
└── THIRD_PARTY_NOTICES.md   # external dependency license matrix
```

`evals/` and `tests/` hold local evaluations and unit tests and are not distributed with the repository; see [docs/design.md](docs/design.md).

## Development and verification

Run these from the repository root; at runtime the orchestrator uses absolute `{SKILL_DIR}/scripts/...` paths.

```bash
# Static checks: frontmatter, relative links, routing consistency, forbidden paths
python scripts/check_skill.py

# Runtime probe (add --check to fail on missing packages)
python scripts/check_runtime.py --branches A,B,C,D,E,F

# Unit tests, when the local tests/ directory is available
python -B -m unittest discover -s tests
```

When routing changes, follow the sync checklist in [docs/design.md](docs/design.md): update `SKILL.md`, `production.md`, both READMEs, `scripts/deps.json`, `references/dependencies.md` and local `evals/cases.md`, then run the applicable checks above. CI runs static checks; the repository uses only the Python standard library.

## FAQ

**The skill is not discovered after cloning.** It is not inside a scanned skills root. Put it at `~/.dsh/skills/ppt-planner-maker`, or create a junction/symlink at `<workspace>/.dsh/skills/ppt-planner-maker`. DSH scans one level only.

**A dependency is reported missing.** Run `python "<skill-dir>/scripts/doctor.py" --workspace <workspace> --branches A` for a verdict and next steps. To let the agent install for you, preview `python "<skill-dir>/scripts/setup.py" --workspace <workspace> --branches A` and re-run with `--yes` after you agree. Or pass an existing dependency directory via `--skills-dir` / `PPT_PLANNER_SKILLS_DIR`. Do not guess paths.

**The resolver says OK but the build fails with ModuleNotFoundError.** A path check is not a runtime check. Run `python "<skill-dir>/scripts/check_runtime.py" --branches A` and install ppt-master's `requirements.txt`.

**I have my own company `.pptx` template. How do I use it?** Give the file path and say "use this template". The planner defaults to ppt-master Edit Native PPTX for new content; Create Template is only for an explicit reusable workspace or a `.potx` that cannot be filled directly. Do not pick the ready-made design template route, which means gorden's built-in library.

**Is internal company use commercial use?** CC BY-NC 4.0's "non-commercial" definition does not clearly cover every internal-use scenario. Check your organization's policy or ask the maintainer for written permission before rolling it out internally. This is not legal advice.

**`python3` does nothing on Windows.** Use `python`; `python3` may be the Microsoft Store stub.

**Can I send the generated HTML to someone?** Yes, but include the project's `assets/` or `images/` and keep relative paths. If it uses CDN fonts or icons, test offline playback before promising it works offline.

**Can I use it without a company deck?** Yes. Pick the free-design route; no template is needed.

**I need a company template and HTML.** That is a conflict. The company-deck route produces editable PPTX only; one requirement has to change.

**Does "hurry up" skip confirmation?** No. It only merges the three documents into one confirmation, and the production route still has to be answered. To skip approval, say "skip confirmation, just build it". "You decide the route" only decides the route and is not fast mode.

**Do old `skills\ppt-master` prompts still work?** Not recommended. Dependencies are external now; install them and use skill names. See [docs/migration.md](docs/migration.md).

**Can I commit `projects/` or deliverables back into the repository?** Please don't. The repository is the skill package; keep runtime artifacts in the workspace. `.gitignore` already excludes them.

## License

In one sentence: personal study, research and teaching are allowed; confirm with the maintainer before internal company or commercial use.

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

Explicit --skills-dir checks only that target; other copies are informational. Without it, only drift=match copies are reused; drift/unknown plans a private install (PPT_PLANNER_HOME supported). Existing conflicting target versions require manual action and are never overwritten or switched. Higher-priority project copies may shadow the install: follow the warning. Execution is clone → pin → pip using the pinned target requirements.
