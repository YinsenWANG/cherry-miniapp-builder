---
name: cherry-miniapp-builder
description: Create, improve, package, or brainstorm Cherry Studio Real Mini Apps. Use for installable .miniapp packages, Cherry mini-app prototypes, domain ideas, or conversion into the sandboxed window.cherry platform; not ordinary websites or Cherry Studio changes.
metadata:
  compatibility: Agent Skills-compatible hosts including Claude Code, Codex, Pi Agent, and Cherry Studio. Python 3.9+ is required for bundled helpers.
---

# Cherry Mini App Builder

Turn an idea into a usable, installable Cherry Studio mini app. This portable Agent Skill works with Claude Code, Codex, Pi Agent, and Cherry Studio; the host only builds files and never expands the target `window.cherry` runtime permissions.

## Route the request

- **Build or convert:** read [technical contract](references/technical-contract.md) and [build playbook](references/build-playbook.md); read a capability appendix only when used.
- **Brainstorm or domain workflow:** run `python3 scripts/search_templates.py "<request>"` from this directory and read returned records; use the [domain index](references/domain-index.md) for broad exploration.
- **Regulated/high-stakes:** also read [high-stakes domains](references/high-stakes-domains.md). **Remote publishing:** read the distribution appendix. **Audit:** validate first, then compare against the contract and playbook.

## Three principles

- Manifest, sandbox, permissions, and package rules are hard contracts. Request the least permission leaves; enhancement-only leaves belong in `optionalPermissions`, and network needs exact hosts.
- Templates and archetypes are inspiration only: they do not authorize permissions or dictate functionality, data model, information architecture, or high-stakes decisions.
- Keep assets local and dependency-free; do not embed secrets. High-stakes output is assistive, reviewable, and bounded.

## Build and handoff

- For a clear goal, proceed without arbitrary framework, layout, color, storage, or permission questions. Start from the dependency-free starter where useful; `--template-id` and `--archetype` are starting surfaces, not requirements.
- Build one coherent primary job with realistic fictional data, understandable first-run and empty/loading/error/success states, editable assumptions, and graceful optional-permission fallback.
- Use AI only with bounded context and a useful non-AI path where practical. Check availability, stream visibly, preserve input, support cancel and retry.
- Persist meaningful state as it changes; treat startup as recovery and hidden state as a checkpoint. Adapt to theme, keyboard use, narrow panes, locale changes, and revoked permissions.
- When using a modal, follow the technical contract and keep close/cancel available while work is pending.
- Validate, then package with `python3 scripts/package_app.py <directory>`; optionally add `--handoff` on macOS to copy/reveal the archive and navigate to the Mini Apps list.
- The user then chooses `+ → Package`, selects the located file, and personally reviews and confirms permissions; navigation does not prefill a file, open the install panel, or confirm consent.
- Deliver the source directory, `.miniapp`, core-flow and permission summary, validation result, and necessary user-owned configuration. Do not claim runtime testing without a compatible Cherry build.

Use `com.example.<slug>` as a replaceable development id when needed; never use `com.cherrystudio.*`. Resolve resources relative to this file; use the host's normal tools, and disclose if Python helpers could not run.

## Resources

- [Technical contract](references/technical-contract.md), [build playbook](references/build-playbook.md), [archetypes](references/archetypes.md), [quality bar](references/quality-bar.md), [domain index](references/domain-index.md), and [high-stakes domains](references/high-stakes-domains.md).
- `assets/starter/` and `assets/cherry.d.ts`; `scripts/scaffold_app.py`, `validate_app.py`, `package_app.py`, and optional `search_templates.py`.
- Keep sources and generated archives separate from skill resources during app work.
