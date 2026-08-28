# Source provenance

This skill was derived from Cherry Studio PR [#19475](https://github.com/CherryHQ/cherry-studio/pull/19475), `feat(mini-app): add real local mini apps in a sandbox`.

- Reviewed upstream commit: `6f04e529a6331752fc10b9ecede4da2e7aa82819`
- Merge-base used for the complete diff: `d2b300751c33757469203f74b9c9604b6bbf43cf`
- Scope at extraction: 221 files, 33,528 insertions, 384 deletions
- Extraction date: 2026-08-28

## Contract sources

The author-facing rules were cross-checked against:

- `docs/references/mini-app/README.md`
- `manifest.md`, `sandbox.md`, `capabilities.md`, `lifecycle.md`, `theming.md`, `packaging.md`, `activity-log.md`, and `cherry.d.ts`
- `src/shared/types/miniAppManifest.ts` and `miniAppQuota.ts`
- `src/shared/ipc/schemas/miniAppBridge.ts`
- `src/preload/miniAppBridge.ts`
- `src/main/features/miniApp/{capabilities,install,runtime}` and their tests
- renderer install, consent, update, detail, permission, and attention flows
- migration, path, activity-log, usage-attribution, and packaging changes in the PR

The skill intentionally records the public author contract rather than copying host internals. Internal recovery, database, session, and IPC implementation details matter to Cherry maintainers but are not APIs a mini app may rely on.

## Updating this skill

Before changing a public rule, compare the latest upstream versions of the source list above. Treat `MINI_APP_METHODS`, the manifest schemas, the bridge schema, `cherry.d.ts`, and runtime contract tests as stronger evidence than prose when they disagree. Record the new commit here and add or update validator coverage for any changed invariant.
