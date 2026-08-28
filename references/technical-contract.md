# Cherry Real Mini App technical contract

This is the author-facing contract extracted from Cherry Studio PR #19475. It is pinned to the upstream commit in [source-provenance.md](source-provenance.md).

## Package and manifest

A mini app is a static web app in a `.miniapp` zip. `manifest.json` must be at the archive root; a single wrapper directory is also accepted. Bundle every runtime asset—remote scripts, styles, fonts, images, and modules are blocked.

Required manifest fields:

- `id`: lowercase reverse-DNS host syntax, at most 120 characters; no underscore or leading/trailing hyphen. The first label cannot be `con`, `prn`, `aux`, `nul`, `com0`–`com9`, or `lpt0`–`lpt9`. `com.cherrystudio.*` is reserved.
- `name`: non-empty string or locale table containing at least `en` or `zh`; each value at most 64 characters, at most 20 locales.
- `description`: same localization shape, each value at most 200 characters.
- `version`: valid semver, at most 32 characters.
- `entry`: existing regular package-relative POSIX path. It cannot be absolute, contain `..` or backslashes, or start with `__cherry`.

Optional fields:

- `icon: { path, sha256 }`: both fields required together; lowercase SHA-256 of an icon no larger than 5 MB.
- `releaseNotes`: localized plain text, at most 500 characters per value.
- `permissions` and `optionalPermissions`: at most 32 declarations each. Required and optional sets cannot overlap after wildcard expansion.
- `network`: at most 20 unique bare hostnames. No scheme, path, port, wildcard, IP literal, or numeric final label.
- `update: { url, urlCn? }`: remote distribution endpoints; ignored for packages installed from a local file.

Package limits: 50 MB archive, 100 MB actual extracted bytes, 2,000 entries, 256 KB manifest. Symlinks, devices, FIFOs, sockets, path escape, and a top-level `__cherry` directory are refused.

## Sandbox

The entry runs at `cherry-miniapp://<appId>/` in a per-app session partition and sandboxed webview.

- The document has an opaque origin. `location.origin` is `"null"`.
- Node and Electron globals are absent. `require`, `process`, and `ipcRenderer` do not exist.
- Page-level outbound network, frames, workers, service workers, popups, external navigation, form submission, downloads, WebRTC, and browser permission requests are blocked.
- Web Storage, IndexedDB, cookies, Cache API, and `navigator.clipboard` are unavailable.
- Use `cherry.storage`, `cherry.file`, `cherry.network`, `cherry.notification`, and `cherry.clipboard` instead.
- Package-relative `fetch()` works for bundled files. Canvas, WebGL/WebGPU, Web Audio, WebAssembly, inline scripts, and hash/history routing work.
- Browser downloads and file-system pickers do not work. Use `<input type="file">` for import and `cherry.file.export` for export.
- Do not rely on Page Visibility, `navigator.language`, unload events, or remote CDN assets.

## Permission model

Grantable leaves:

```text
ai.chat
storage.get storage.set storage.delete storage.keys
file.save file.load file.list file.delete file.export
notification.show
clipboard.read clipboard.write
network.fetch
```

Namespace wildcards such as `storage.*` expand to current leaves at consent time. They do not silently grant methods added in a later Cherry version.

Ungated: `app.getInfo`, `app.getPermissions`, `ai.cancel`, and events. Sibling accessors—`ai.getCapabilities`, `storage.usage`, and `file.usage`—work when any leaf in their namespace is granted.

Required permissions are accepted together at install and cannot later be revoked. Optional permissions are offered ticked by default, can be unticked during install, and may be revoked or restored later. Re-read grants whenever the app becomes visible. A `network.*` permission and at least one declared hostname must appear together.

## API behavior

Every method except `cherry.on` returns a Promise. Rejections are plain `{ name, message }` objects, not `Error` instances. Branch on one of seven stable names: `PermissionDenied`, `QuotaExceeded`, `RateLimited`, `Unavailable`, `InvalidArgument`, `Cancelled`, `Internal`.

### App

- `app.getInfo()` → `{ appId, version, hostVersion, locale }`.
- `app.getPermissions()` → current state for every declared leaf.
- `cherry.on('app.visibilityChange' | 'app.localeChange', handler)` → unsubscribe function.

Theme is not an API field. Use `prefers-color-scheme`.

### AI

- `ai.getCapabilities({ model?: 'default' | 'quick' })` returns `{ available: false }` or `{ available: true, reasoning, contextWindow }`.
- `ai.chat({ messages, reasoning?, model? }, { onChunk, callId? })` streams text and resolves `{ ok: true }`.
- `ai.cancel(callId)` is idempotent.

AI is text-only, with no image input or tool calling. Maximum 64 messages and 256 KB UTF-8 prompt input; two calls in flight and 60 starts per minute per app. While hidden, only five new calls are allowed until visible again. `callId` is at most 64 characters. Check model availability before exposing the action, preserve partial output, and handle both a resolved cancellation and `Cancelled` rejection.

### Storage

`get`, `set`, `delete`, `keys`, and `usage` operate on string keys and values. Total serialized state is 1 MB and 1,000 keys; keys are at most 256 UTF-8 bytes. Writes are limited to 20 per second and a byte-rate bucket. There are no multi-key transactions: save related state in one JSON value.

### Files

`save`, `load`, `list`, `delete`, `usage`, and `export` use a flat logical namespace. Binary payloads are base64. Names are 1–128 characters with no slash or backslash and cannot be `.` or `..`. Maximum 10 MB per file, 20 MB and 200 files per app. `export` works only while visible, opens one host-owned save dialog, and never reveals a path.

### Notifications

`notification.show({ title, body? })` is one-way. Title and body are truncated to 64 and 256 characters. Maximum five calls per minute. The host identifies the originating app; no click event is delivered.

### Clipboard

`clipboard.read()` and `clipboard.write({ text })` handle plain text only. They require both a visible pane and keyboard focus, so call them from a user action. Maximum text is 1,048,576 characters; rates are 10 reads and 30 writes per minute.

### Network

`network.fetch({ url, method?, headers?, body? })` is the only outbound channel. It accepts HTTPS on the default port to exact declared hosts; no redirects, cookies, credentials, IP literals, or non-global resolved addresses. Non-2xx is a normal result. Request and response bodies are base64, capped at 1 MB and 5 MB. At most 32 headers; hop-by-hop headers plus host, origin, referer, cookie, and content-length are rejected. Timeout is 30 seconds; rates are 60 per minute and four in flight. While hidden, only ten new requests are allowed until visible again. A documented DNS-rebinding residual remains between the pre-check and Chromium connection.

## Lifecycle and persistence

The app may be destroyed without notice when a tab closes, the keep-alive pool evicts it, Cherry quits, a renderer crashes, or an update quiesces it. No unload hook is reliable and in-flight work may disappear.

- Commit meaningful state when it changes; do not wait for shutdown.
- Save atomically related values together.
- Treat startup as crash recovery.
- Pause timers, animation, audio, AI, and network work on `app.visibilityChange({ visible: false })`; resume and refresh permissions on `true`.
- The host may keep a hidden app alive with `display: none`, so `document.visibilityState` is misleading.
- Theme changes come from `matchMedia`; locale changes come from `app.localeChange`.
- Update, rollback, reinstall, clear-data, and uninstall quiesce instances. Capability calls then reject `Unavailable`.

The same app can have multiple live instances. JavaScript memory is per instance; storage and files are shared per app with last-write-wins semantics.

## Theme and interface

Include `<link rel="stylesheet" href="/__cherry/theme.css">`. Use the stable semantic variables such as `--background`, `--foreground`, `--card`, `--primary`, `--muted`, `--border`, `--success`, `--warning`, `--error`, and `--radius`. The stylesheet supplies light and dark values but no reset or component styles. Bundle icons and compiled CSS locally.

## Distribution, updates, and data

A remote distribution manifest repeats the packaged manifest and adds:

```json
"package": {
  "url": "https://example.com/app/1.1.0.miniapp",
  "urlCn": "https://cn.example.com/app/1.1.0.miniapp",
  "iconUrl": "https://example.com/app/icon.png",
  "sha256": "<archive sha256>",
  "size": 12345
}
```

Package URLs must share origins with their respective update URLs, answer directly without redirects, and serve identical bytes across mirrors. `update.urlCn` and `package.urlCn` appear together. Distribution manifests and packaged manifests must agree on shared fields.

Normal updates require a strictly greater semver. New required permissions, newly optional permissions, and added hosts are reviewed; updates are offered, never silently installed. Storage and files survive updates and rollback. One previous-version snapshot is retained. Clear-data removes app state and session data but keeps the package and grants; uninstall removes everything including the activity log.

Packages are not signed in this release. Hashes provide integrity for pinned remote bytes and icons, not author identity.

## Activity log

The host records every refusal, outward capability call, permission decision, and aggregate counts for local calls. It records metadata such as duration, host, byte counts, model slot, and outcome—never prompts, payloads, storage keys, file names, clipboard text, or notification copy. Design denied and failed states as visible UI; repeated hidden failures will also be visible to the user in this log.
