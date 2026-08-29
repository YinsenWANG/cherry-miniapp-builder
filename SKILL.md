---
name: cherry-miniapp-builder
description: Create, improve, package, or brainstorm Cherry Studio Real Mini Apps. Use for installable .miniapp packages, Cherry mini-app prototypes, domain ideas, or conversion into the sandboxed window.cherry platform; not ordinary websites or Cherry Studio changes.
---

# Cherry Mini App Builder

Turn an idea into a usable, installable Cherry Studio mini app.

## Route the request

- **Build or convert:** read [technical contract](references/technical-contract.md) and [build playbook](references/build-playbook.md); read a capability appendix only when that capability is used.
- **Brainstorm, domain workflow, or requests for ideas:** you may run `python3 scripts/search_templates.py "<request>"` and read returned records; use the [domain index](references/domain-index.md) for broad exploration.
- **Regulated or high-stakes work:** also read [high-stakes domains](references/high-stakes-domains.md).
- **Remote publishing:** also read the distribution appendix in the technical contract.
- **Audit:** validate first, then compare requested behavior with the contract and playbook; do not rebuild unless asked.

## Three principles

- Manifest, sandbox, permissions, and package rules are hard contracts. Request the least permission leaves; enhancement-only leaves belong in `optionalPermissions`, and network needs exact hosts.
- Templates are inspiration only: they do not authorize permissions or decide functionality, data model, information architecture, or high-stakes decisions.
- Keep runtime assets local and dependency-free; do not embed secrets. High-stakes output is assistive, reviewable, and bounded.

## Build and handoff

- For a clear goal, proceed without requesting arbitrary framework, layout, color, storage, or permission choices. Start from the dependency-free starter where useful and replace its sample copy and logic.
- Build one coherent primary job with realistic fictional data, understandable first-run and empty/loading/error/success states, editable assumptions, and graceful optional-permission fallback.
- Use AI only with bounded context and a useful non-AI path where practical. Check availability, stream visibly, preserve input, support cancel and retry.
- Persist meaningful state as it changes; treat startup as recovery and hidden state as a checkpoint. Adapt to theme, keyboard use, narrow panes, locale changes, and revoked permissions.
- Run `python3 scripts/validate_app.py <directory>`, address errors and relevant warnings, then `python3 scripts/package_app.py <directory>`.
- Deliver the source directory, `.miniapp`, core-flow and permission summary, validation result, and any necessary user-owned configuration. Do not claim runtime testing without a compatible Cherry build.

Use `com.example.<slug>` as a replaceable development id when the user does not control a reverse-DNS namespace; never use `com.cherrystudio.*`.

## Resources

- [Technical contract](references/technical-contract.md) — manifest, sandbox, permissions, lifecycle, theme, and appendices for AI, files/network, distribution, and activity log.
- [Build playbook](references/build-playbook.md) — implementation patterns and conditional completion checks.
- [Domain index](references/domain-index.md) — catalog navigation; records are not permission grants.
- [High-stakes domains](references/high-stakes-domains.md) — domain boundaries.
- [Source provenance](references/source-provenance.md) — upstream snapshot and mapping.
- `assets/starter/` — no-build starter; `assets/cherry.d.ts` — ambient API types.
- `scripts/scaffold_app.py`, `validate_app.py`, and `package_app.py` — local creation, checks, and deterministic packaging.
- `scripts/search_templates.py` — optional catalog exploration only.
- [Quality bar](references/quality-bar.md) — compatibility link to the playbook checks.
- Keep source and generated archives separate from the skill resources during app work.
