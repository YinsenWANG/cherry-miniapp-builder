# One-shot build playbook

## 1. Frame the product

Write a private one-paragraph product brief before coding:

- primary user and moment of use;
- input the user already has;
- one valuable output;
- shortest complete loop;
- what is deterministic versus AI-assisted;
- what persists and what may leave the sandbox.

When a request includes a domain workflow, asks for ideas, or benefits from comparison, search a few catalog templates for compatible mechanics. Templates and archetypes are inspiration, not permission grants or structural instructions.

Scaffold directly from the primary template when possible:

```text
python3 scripts/scaffold_app.py --id com.example.app --name "App" --description "One useful outcome" --template-id <catalog-id> --output <directory>
```

The scaffold uses the matching interaction shape and permission suggestions as a starting surface. Re-evaluate every permission from actual calls, and replace generic fields and copy with the domain's real inputs, results, and actions.

## 2. Choose capabilities

Start with no permissions, then add only what the flow proves it needs.

| Need | Capability choice |
|---|---|
| Small durable settings or structured state | required `storage.get`, `storage.set`; add `delete`/`keys` only if exposed |
| Larger imported/generated artifact | narrow `file.*` leaves; add `file.export` only for a visible export action |
| AI is the product's core | required `ai.chat` |
| AI is an enhancement | optional `ai.chat` and a deterministic fallback |
| Public API | optional or required `network.fetch` plus exact hosts; never placeholder hosts |
| User reminder | optional `notification.show`; app must remain useful if disabled |
| Explicit copy/paste workflow | narrow clipboard leaf; trigger from click/focus |

Do not request `storage.*` or `file.*` merely for convenience when two leaves suffice. Never embed API secrets.

`file.save`/`file.load` data and `network.fetch` request/response bodies are Base64; for text, use a correct UTF-8/Base64 conversion rather than passing ordinary strings.

## 3. Shape the information architecture

Common shapes to take inspiration from include:

1. A compact header naming the job and current status.
2. A primary workspace with one obvious call to action.
3. A secondary history/settings/help surface that does not compete with the task.

For dense analytical apps, consider overview → inspect → act. For calculators, consider inputs → live result → assumptions → export. For creative tools, consider source → controls → preview → save. For games, show play immediately and move rules/settings aside. Products may reduce, merge, or choose another structure.

Use [archetypes.md](archetypes.md) for the full twelve-pattern completion contract. Do not blend archetypes into a portal; choose one dominant loop and borrow at most one secondary mechanic.

## 4. Build for first-run success

- Ship realistic fictional sample data when the user's own data is not yet available.
- Explain the first action in one sentence, not a tour.
- Make import and paste tolerant of headers, whitespace, and common delimiters.
- Keep destructive actions reversible or confirmed.
- Show units, time ranges, formula assumptions, provenance, and staleness beside results.
- Use domain language, not generic labels such as “Submit” or “Process”.
- When applicable, keep large datasets responsive with pagination, filtering, aggregation, or virtualization; give charts textual summaries; and check deterministic calculations against at least three meaningful cases including an edge case.

## 5. Implement resilient host access

Centralize `window.cherry` calls in a small adapter. The UI should not scatter permission and error branching across components.

At startup:

1. read `app.getInfo()` and `app.getPermissions()`;
2. subscribe to locale and visibility events;
3. load one coherent state value and migrate its version if necessary;
4. render a usable state before optional AI or network work;
5. check `ai.getCapabilities()` before showing an enabled AI action.

On visible again, re-read permissions and refresh stale external data only from an explicit, bounded policy. On hidden, checkpoint state and stop initiating AI/network work.

Map public errors to useful recovery:

- `PermissionDenied`: explain the disabled feature and how to grant it; do not retry.
- `QuotaExceeded`: show usage, offer deletion/export/compaction.
- `RateLimited`: back off and let the user retry; hidden-budget failures wait until visible.
- `Unavailable`: preserve work and offer retry.
- `InvalidArgument`: keep input and identify the field without exposing internals.
- `Cancelled`: keep partial AI output and mark it incomplete.
- `Internal`: show a neutral failure with retry, never fabricate success.

## 6. Persist safely

Use a versioned state envelope such as:

```json
{"schema":1,"updatedAt":"2026-08-28T12:00:00Z","data":{}}
```

Keep values that must agree in one JSON document. Debounce rapid UI changes below the write-rate limit, but flush meaningful milestones immediately. Never store an in-progress flag that is cleared only during shutdown. Read back after startup and recover idempotently.

## 7. Make AI domain-specific

Give the model a bounded role and explicit evidence. A strong request includes:

- the user's goal and audience;
- structured input or selected records;
- the calculation or facts already determined by code;
- an exact output structure and length;
- instructions to flag missing information and avoid inventing values.

Keep the prompt inside the app's declared purpose. Stream into an accessible live region, provide cancel, and prevent duplicate submissions. Do not send unrelated stored data “for context”.

## 8. Package and verify

Run the validator before packaging. Inspect the output archive to ensure `manifest.json` and the entry are at its root. For remote distribution, separately compute the archive hash and size, then create the external distribution manifest—never place its `package` block inside the archive.

Treat validator warnings as review prompts. Remove unused permissions and known blocked browser APIs; suppress nothing merely to get a green line. Static checks can miss dynamic property access and cannot prove runtime behavior.

Runtime-check, when a compatible Cherry build is available:

- first run and reload;
- dark and light mode;
- narrow pane and detached window;
- denied and revoked optional permissions;
- no configured model and cancelled streaming;
- hidden then visible;
- quota/error copy;
- clear data, update, and rollback when relevant.
