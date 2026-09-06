# Changelog

## 0.2.1 — 2026-09-06 local checkpoint

- Ship reviewed IconFlow card identity across Windows executable/window/tray and web UI.
- Add responsive offline English / Traditional Chinese app guide, linked in-app and on the desktop.
- Add static allowlist regression, guide syntax and desktop/mobile bilingual browser acceptance.
- Preserve original source in a separate root commit and prepare the authorized private GitHub checkpoint.
- Keep card identities, schemas and safety boundaries unchanged; physical and remote acceptance remain separate.
- Expose hosted verification failures and compare Windows short/long workspace aliases by filesystem identity.


## 0.2.0 — Card workshop (local milestone) — 2026-09-06

### Added

Searchable card library with combined batch/write-result/route-intent filters, 25-row UI pages, matching CSV export and a quarantine shortcut. Per-card details distinguish simulated/local verification, public export eligibility, unchecked availability and unrecorded phone QA; private UID and verification evidence are progressively disclosed.

Live recipient preview shares its escaped markup/styles with the public Worker. Drafts show saved/unsaved state and can restore the saved local profile. Preview actions remain inert. Public export review shows exact saved fields, encoded origins, enabled/suspended counts, excluded unverified matches, route entries and checksum. It warns that shared profile imports affect other routes. Download refuses content changed since review and records export preparation without claiming publication.

### Validation and compatibility

113 Python tests and 16 Worker tests; source/packaged browser flows, dedicated 56-card library acceptance, native lifecycle and real local Worker/D1 with a 375px recipient-browser check. Schema 1, URLs, assignments and CLI/MCP aliases remain compatible. The agent manifest endpoint remains available. No remote publication, physical qualification, schema migration or signing is claimed.

## Windows bootstrap foundation (included in 0.2.0) — 2026-09-06

### Fixed

Windows workspace-lock contention now returns `WORKSPACE_BUSY` and closes the contender's handle. CLI/MCP and startup output use UTF-8 independently of the Windows code page. Startup cleanup does not call blocking server shutdown before its serving thread starts. The disposable smoke test terminates Windows venv child processes and tests Unicode/space-containing paths. Windows launchers now forward explicit arguments.

### Added

Operator controls for maximum attempts and a 15–600 second approval window; recovery stays limited to one identity. Native Windows lock/startup regressions. Repeatable source/packaged browser, native desktop, packaged Windows, backup/restore and real local Wrangler/D1 smoke scripts. Pinned Wrangler 4.129.0 with generated npm lockfile; resolved Windows optional/build dependencies in `requirements-windows.lock`.

### Verified locally

101 Python and 13 Worker handler tests; source/unsigned executable browser workflows; native desktop and packaged desktop/tray start/close/restart; local Worker/D1 route/vCard/security and stale-revision checks; synthetic backup/restore. An unsigned portable folder and ZIP were produced. Physical NFC, phone/print QA, clean-machine distribution and remote publication remain unqualified. See `reports/2026-09-06-bootstrap/REPORT.md`.

## 0.1.1 — nfcraft local-agent handoff — 2026-09-05

### Changed

Renamed product, Python package/imports, UI, package/distribution metadata and MCP server to **nfcraft**. Added canonical `nfcraftctl` entry point and retained `nfcctl` / `nfc_*` MCP compatibility. Centralized runtime version metadata. Schema 1 and card URL/identity formats are unchanged.

### Fixed

Prevent initialization from overwriting nonzero bytes hidden inside the planned write region behind an empty NDEF TLV; untouched nonzero tail data remains preserved. Tightened public manifest validation before SQL generation: exact schema/fields, explicit simulation marker, checksum, duplicate IDs, revisions, URL-to-slug consistency and rejection of UID/private fields. SQL output no longer silently replaces an existing reviewed output file. The agent CLI ignores ambient HTTP proxies and refuses redirects so loopback capability tokens are not forwarded through those paths.

### Added

Legacy workspace detection; explicit, non-destructive schema-1 importer with source locking, backup-copy verification and no runtime-token transfer. Windows launchers prefer the repo venv. Added preflight, a unified hardware-free verification runner, child-process daemon/CLI/MCP smoke, migration/manifest/regression tests, CI configuration, preview/production templates and no-dependency public-site test scripts.

Comprehensive local-agent bootstrap/continuation prompts; project state, product brief, task plan, UI direction, deployment/quality gates, migration/rollback/release docs. Original prototype test report/screenshots retained under `docs/history/v0.1.0` as historical evidence.

### Not claimed

No physical NFC qualification, actual Windows/desktop build, real agent-client integration, Android app, live Cloudflare deployment, automatic sync, phone/printed-card QA or signed installer. See current test report for exact executed checks. CI configuration was supplied, not run on a remote repository.

## 0.1.0 — original NFC Card Ops prototype

Original supplied source archive. Its logs and screenshots are historical. The baseline was re-run before creating 0.1.1; no prior hardware/deployment claims have been promoted to current validation.
