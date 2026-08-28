---
name: cherry-miniapp-builder
description: Create, improve, package, or brainstorm polished Cherry Studio Real Mini Apps from natural-language requests. Use when a user wants an installable .miniapp, a Cherry mini-app prototype, domain ideas, or a conversion from HTML/tool/workflow into the sandboxed window.cherry platform; not for ordinary websites or changes to Cherry Studio itself.
---

# Cherry Mini App Builder

Turn an idea into a usable, installable Cherry Studio mini app. Favor a complete working artifact over a plan or tutorial.

## Route the request

- **Build or convert an app:** read [references/technical-contract.md](references/technical-contract.md), [references/build-playbook.md](references/build-playbook.md), and [references/quality-bar.md](references/quality-bar.md).
- **Brainstorm or select a domain:** run `python3 scripts/search_templates.py "<request>"`; read only the returned templates. Use [references/domain-index.md](references/domain-index.md) when the request is too broad to search well.
- **Regulated or high-stakes domain:** also read [references/high-stakes-domains.md](references/high-stakes-domains.md).
- **Publish or update a remotely distributed package:** also read the distribution section of [references/technical-contract.md](references/technical-contract.md).
- **Audit an existing app:** validate it, then compare its behavior against the technical contract and quality bar. Do not rebuild it unless requested.

## One-shot defaults

When the user has supplied a useful goal, proceed without asking them to choose a framework, layout, color, storage shape, or permission list.

1. Search the domain catalog and combine at most three relevant patterns.
2. Infer a narrow primary user, one core job, and a start-to-finish success path.
3. Default to bundled HTML, CSS, and JavaScript with no build step or remote assets. Use another stack only when requested or materially useful; ship its built static output.
4. Start from `python3 scripts/scaffold_app.py --id <reverse.dns.id> --name <name> --description <description> --output <directory>` when creating a new app.
5. Replace all starter copy and sample logic. Include realistic example data, an immediately understandable first screen, and a complete empty/loading/error/success flow.
6. Request the least privilege that makes the core job work. Put enhancement-only capabilities in `optionalPermissions`. Do not request network access without exact known hosts.
7. Make the app useful without AI when possible. When AI is essential, check `ai.getCapabilities()` first, stream visibly, support cancel, preserve the user's input, and provide a retry path.
8. Persist meaningful state as it changes. Treat every start as crash recovery and `app.visibilityChange(false)` as a checkpoint, not as a guaranteed shutdown.
9. Adapt to Cherry theme, keyboard use, narrow panes, dark mode, locale changes, and revoked optional permissions.
10. Run `python3 scripts/validate_app.py <directory>`, fix every error and relevant warning, then run `python3 scripts/package_app.py <directory>`.

If the user does not control a reverse-DNS namespace, use `com.example.<slug>` and clearly identify it as a replaceable development id. Never use the reserved `com.cherrystudio.*` namespace.

## Product judgment

- Build a small product, not a capability demo. Every visible control must support the primary job.
- Prefer one coherent workflow over a dashboard containing unrelated AI buttons.
- AI should transform, explain, classify, draft, simulate, or coach with explicit source context. Do not add a generic chat panel unless conversation is the product.
- Keep calculations deterministic in code. Use AI for interpretation or explanation, never arithmetic that the app can compute exactly.
- For external data, prefer file import, paste, or a public credential-free API. Never embed secrets in the package; mini-app source and storage are not a secret vault.
- Make domain assumptions visible and editable. Label estimates, generated content, and stale data.
- A template is inspiration, not authorization to make medical, legal, financial, safety, or employment decisions for the user.

## Required deliverable

For a build request, finish with:

- the source directory;
- an installable `.miniapp` archive;
- a short summary of the core workflow, requested permissions, and validation result;
- any unavoidable configuration item, such as a user-owned API hostname.

Do not claim installation or runtime behavior was tested unless it actually ran inside a compatible Cherry Studio build. Packaging validation is not a sandbox runtime test.

## Resources

- [Technical contract](references/technical-contract.md) — authoritative author-facing constraints derived from PR #19475.
- [Build playbook](references/build-playbook.md) — implementation sequence and robust capability patterns.
- [Quality bar](references/quality-bar.md) — usability and completion criteria.
- [Domain index](references/domain-index.md) — 25 families and 200 reusable templates.
- [High-stakes domains](references/high-stakes-domains.md) — medical, legal, financial, employment, industrial, and public-sector boundaries.
- [Source provenance](references/source-provenance.md) — exact upstream snapshot and source mapping.
- `assets/starter/` — dependency-free starter copied by the scaffolder.
- `assets/cherry.d.ts` — ambient API types for TypeScript projects.
