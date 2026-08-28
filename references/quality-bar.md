# Quality bar

A one-shot app is complete only when a user can understand, trust, and finish its primary job without editing source.

## Product completeness

- One-sentence value is visible on first load.
- Primary task works end to end with realistic data.
- Sample data is fictional, useful, and removable.
- Empty, loading, success, error, and permission-denied states exist.
- All controls work; no placeholder buttons, lorem ipsum, fake charts, or TODOs remain.
- Results expose units, assumptions, provenance, and timestamps where relevant.
- The app has a clear reset/delete path and confirms destructive actions.

## Interface

- Looks intentional from 360 px to a wide detached window.
- Uses Cherry semantic theme variables and follows dark mode.
- Keyboard focus is visible; forms have labels; status is not color-only.
- Touch targets and controls are comfortably sized.
- Large datasets remain responsive through pagination, filtering, aggregation, or virtualization.
- Charts have textual summaries and do not imply precision the data lacks.
- Motion pauses when hidden and respects reduced-motion preferences.

## Host integration

- Manifest purpose and permission list agree with actual behavior.
- Optional capabilities fail gracefully and can be revoked while the app is installed.
- AI availability, streaming, cancellation, rate limits, and partial output are handled.
- State is saved before likely eviction and recovered after an unclean end.
- No direct external fetch, CDN, remote font, popup, service worker, browser storage, or browser clipboard dependency remains.
- External API calls use exact allowlisted hosts and treat non-2xx as results.
- File import does not assume access to a filesystem path; export goes through `cherry.file.export`.

## Domain integrity

- Deterministic calculations are tested against at least three meaningful cases including an edge case.
- Generated interpretation cannot silently change source facts.
- High-stakes output is advisory, reviewable, and bounded by explicit jurisdiction, policy, source, or date.
- Sensitive sample data is fictional and permissions are minimized.

## Final evidence

The handoff states what was validated. A passing static validator proves package shape and catches known incompatibilities; it does not prove the app ran inside Cherry. If runtime testing was unavailable, say so plainly.
