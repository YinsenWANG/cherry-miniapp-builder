# Cherry Mini App Builder

An open-source, cross-agent [Agent Skill](https://agentskills.io/) that turns a natural-language idea into a polished, installable Cherry Studio Real Mini App.

It combines the capability and sandbox contract introduced by [Cherry Studio PR #19475](https://github.com/CherryHQ/cherry-studio/pull/19475) with a searchable catalog of 200 application patterns across 25 domain families. The goal is not to generate a toy page: the skill drives a complete user flow, realistic sample data, least-privilege permissions, resilient state, error handling, validation, and `.miniapp` packaging in one pass.

The same `SKILL.md`, references, templates, and Python tools work with Claude Code, Codex, Pi Agent, and Cherry Studio. These products are build hosts; the generated application always targets Cherry Studio's sandboxed `window.cherry` runtime and receives no extra privileges from the host that created it.

## Install

The repository root is the skill directory. Install that same directory in any supported host; no generated wrapper or platform-specific fork is needed.

### Claude Code

```bash
git clone https://github.com/YinsenW/cherry-miniapp-builder.git ~/.claude/skills/cherry-miniapp-builder
```

### Codex

```bash
git clone https://github.com/YinsenW/cherry-miniapp-builder.git ~/.codex/skills/cherry-miniapp-builder
```

If `CODEX_HOME` is configured, clone it under `$CODEX_HOME/skills/cherry-miniapp-builder` instead.

### Pi Agent

```bash
git clone https://github.com/YinsenW/cherry-miniapp-builder.git ~/.pi/agent/skills/cherry-miniapp-builder
```

Pi also supports project-scoped `.pi/skills/` and the cross-tool `.agents/skills/` location.

### Cherry Studio

In a Cherry Studio build containing the Real Mini App and managed-skills runtime from PR #19475, either:

- open **Settings → Skills**, import the cloned repository directory, and enable it for the desired agent; or
- open the Skills marketplace, choose **GitHub**, and install `https://github.com/YinsenW/cherry-miniapp-builder/blob/main/SKILL.md`.

Cherry Studio injects the enabled skill into its supported Claude Code and Pi Agent runtimes, so there is still only one maintained copy of the skill.

### Shared project source

For a repository used by multiple agents, keep one checkout at `.agents/skills/cherry-miniapp-builder`. Pi Agent and Cherry Studio can discover that cross-tool location directly. If another host only scans its own directory, expose the same checkout with a symlink instead of copying it, for example:

```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/cherry-miniapp-builder .claude/skills/cherry-miniapp-builder
```

On systems where symlinks are unavailable, install the repository in the host-specific directory above.

## Use

Invoke it explicitly using the syntax supported by the host, or ask naturally for a Cherry Studio mini app. This wording works across all four hosts:

```text
Use the cherry-miniapp-builder skill to build a bilingual salary calculator with scenario comparison and an exportable report.
```

Codex can invoke it as `$cherry-miniapp-builder`. Pi Agent additionally exposes it as `/skill:cherry-miniapp-builder` when skill commands are enabled.

## What is included

- A concise skill router and one-shot build workflow.
- One platform-neutral skill package for Claude Code, Codex, Pi Agent, and Cherry Studio.
- A versioned technical contract covering the manifest, sandbox, permissions, quotas, lifecycle, theming, packaging, updates, and activity log.
- 200 cross-domain patterns searchable by Chinese or English intent, backed by a 40-query regression set.
- Twelve product archetypes spanning calculators, analyzers, dashboards, trackers, planners, checklists, studios, coaches, simulators, games, comparators, and coordinators.
- A dependency-free starter that can inherit a template's product structure, core permissions, optional enhancements, and AI role without a build tool or CDN.
- Standard-library scripts to search templates, scaffold, validate, and deterministically package an app.
- High-stakes guardrails for medical, legal, financial, employment, industrial, and public-sector use cases.

## Utilities

```bash
python3 scripts/search_templates.py "工业设备预测性维护"
python3 scripts/scaffold_app.py --id com.example.maintenance --name "维护助手" --description "管理设备点检并分析异常趋势" --template-id manufacturing-maintenance --output /tmp/maintenance-app
python3 scripts/validate_app.py /tmp/maintenance-app
python3 scripts/package_app.py /tmp/maintenance-app
python3 scripts/validate_catalog.py
python3 scripts/test_tools.py
```

Use `python` or `py -3` instead of `python3` on hosts that expose Python 3 under those names. The validator catches manifest errors, unused permissions, and common sandbox incompatibilities. A green result does not replace testing in a Cherry Studio build that contains the Real Mini App runtime. GitHub Actions runs the catalog and toolchain tests on Windows, macOS, and Linux with Python 3.9 and the current Python line.

`agents/openai.yaml` contains optional Codex UI metadata only. Claude Code, Pi Agent, and Cherry Studio ignore it and consume the shared `SKILL.md` directly.

## Upstream status

The technical contract is pinned to the live PR snapshot recorded in [references/source-provenance.md](references/source-provenance.md). PR #19475 remains open at that snapshot and may still change, so re-check the upstream contract before publishing production packages.

## License

MIT
