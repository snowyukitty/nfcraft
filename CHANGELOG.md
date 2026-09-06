# Changelog

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
