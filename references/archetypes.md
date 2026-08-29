# Product archetypes

Use the archetype named by a domain template as the structural starting point. Keep the domain language and workflow from the template; borrow only the interaction shape from this file.

## `calculator`

Inputs → live deterministic result → assumptions → scenarios → optional export. Show units beside every value, keep formulas in a pure function, seed one realistic scenario, and verify a normal case, a boundary, and an invalid input.

## `analyzer`

Import or paste → map/clean → overview → inspect records → action summary. Preserve the source, make filters reversible, compute metrics locally, expose provenance and timestamps, and never send raw data to AI by default.

## `dashboard`

Status overview → exception queue → detail → action/owner. Start with a small fictional dataset, show the reporting period and metric definitions, and make every chart carry a textual conclusion.

## `tracker`

Create record → update status/evidence → history → review/export. Use a versioned data envelope, stable ids, visible save state, correction/delete paths, and an immediately usable sample record.

## `planner`

Goal and constraints → generated draft → conflict view → manual adjustment → publish/export. Keep scheduling or allocation deterministic, explain infeasible constraints, and never let AI silently change them.

## `checklist`

Select context → guided checks → evidence/notes → exceptions → sign-off report. Work offline, show progress, make skipped/not-applicable distinct, and require a human confirmation for completion.

## `studio`

Source material → structured controls → draft/preview → review → export/copy. Keep source and generated output side by side, preserve versions, mark AI-generated text, and make fact checking a visible step.

## `coach`

Goal/context → one focused interaction → feedback → practice → reflection. Bound the AI role, avoid pretending to be a licensed professional, preserve the user's answer, and offer the smallest useful next step.

## `simulator`

Model and assumptions → controls → deterministic run → compare scenarios → limitations. Make equations and ranges visible, prevent impossible states, label uncertainty, and separate model output from AI explanation.

## `game`

Play immediately → deterministic rules/state → feedback/hints → progress → replay. Keep scoring and answer validation in code, make AI narration optional unless generation is the game, and support keyboard and reduced motion.

## `comparator`

Candidates → normalized criteria → hard filters → weighted or side-by-side comparison → decision record. Show missing data, preserve user weights, explain sensitivity, and do not hide trade-offs behind a single score.

## `coordinator`

Shared objective → work items/owners → status and blockers → handoff → review. Avoid pretending to send or assign externally unless a real capability exists; produce an exportable handoff instead.

## Completion contract

Regardless of archetype, a one-shot result needs realistic fictional sample data, empty/loading/error/permission states, a complete primary loop, responsive layout, accessible controls, domain assumptions, and a reset/delete path. Templates guide product shape; the technical contract remains authoritative for permissions and runtime behavior.
