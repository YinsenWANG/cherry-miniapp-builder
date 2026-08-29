# Cherry Mini App Builder

An open-source Codex skill that turns a natural-language idea into a polished, installable Cherry Studio Real Mini App.

It combines the capability and sandbox contract introduced by [Cherry Studio PR #19475](https://github.com/CherryHQ/cherry-studio/pull/19475) with a searchable catalog of application patterns. The goal is not to generate a toy page: the skill supports a complete user flow, least-privilege permissions, validation, and `.miniapp` packaging.

## Install

Copy or clone this repository into your Codex skills directory:

```bash
git clone https://github.com/YinsenW/cherry-miniapp-builder.git ~/.codex/skills/cherry-miniapp-builder
```

Restart or reload Codex, then invoke it explicitly or ask naturally for a Cherry Studio mini app:

```text
Use $cherry-miniapp-builder to build a bilingual salary calculator with scenario comparison and an exportable report.
```

## What is included

- A concise skill router and one-shot build workflow.
- A versioned technical contract with core build rules and on-demand capability, distribution, and audit appendices.
- Currently 200 cross-domain patterns across 25 families, searchable by Chinese or English keywords.
- A dependency-free starter that works without a build tool or CDN.
- Standard-library scripts to search templates, scaffold, validate, and package an app.
- High-stakes guardrails for medical, legal, financial, employment, industrial, and public-sector use cases.

## Utilities

```bash
python3 scripts/search_templates.py "工业设备预测性维护"
python3 scripts/scaffold_app.py --id com.example.maintenance --name "维护助手" --description "管理设备点检并分析异常趋势" --output /tmp/maintenance-app
python3 scripts/validate_app.py /tmp/maintenance-app
python3 scripts/package_app.py /tmp/maintenance-app
python3 -B scripts/test_tools.py
python3 -B scripts/validate_catalog.py
```

The validator catches authoring errors and common sandbox incompatibilities; packaging prints relevant heuristic warnings but rejects only errors. The tool checks use `-B` to avoid creating bytecode in the skill tree. A green result does not replace testing in a Cherry Studio build that contains the Real Mini App runtime.

## Upstream status

The technical contract is pinned to the PR snapshot recorded in [references/source-provenance.md](references/source-provenance.md). PR #19475 was still under review when this repository was created, so re-check the upstream contract before publishing production packages.

## License

MIT
