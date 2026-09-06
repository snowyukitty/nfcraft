# nfcraft — current project state

Updated: 2026-09-05. Handoff version: **0.1.1**. Treat this file as the index for the next agent, not as evidence in place of test logs.

## Confirmed decisions

- Product/repo/package: `nfcraft`. Local operator app for NTAG215 wooden cards, with CLI/MCP automation and a separate public contact-page service.
- Existing implementation is retained: Python, SQLite, plain HTML/CSS/JavaScript, optional pyscard and desktop extras, Cloudflare Worker/D1 source.
- Owner's primary environment: Windows 11 with WSL available. Detect the actual session; do not assume the container used to generate this bundle is the target environment.
- One unique durable public URL per card; private UID mapping; no AI call per card; no irreversible tag writes.
- USB PC/SC is the main intended workstation. ACR1552U PICC is an experimental qualification target, not certified support. Android/Web NFC are future capability-specific adapters.

## State of the delivered implementation

| Surface | State |
|---|---|
| Brand/imports/package/launchers/version | Renamed to nfcraft 0.1.1; consistency tests added |
| Mock engine, durable identity, bounded approval, readback, quarantine/recovery | Implemented; hardware-independent tests pass |
| Guard for hidden nonzero bytes under an empty TLV | Added in 0.1.1; refuses a planned overwrite |
| Public export validation | Added strict fields/types/checksum/UID-exclusion/URL-slug/duplicate checks |
| Legacy workspace recognition and opt-in copy | Implemented and unit tested; actual owner's Windows data not migrated here |
| CLI + newline-delimited MCP stdio | Loopback client disables proxies/redirects; implemented; child-process smoke passed; real agent-client integration remains to be checked |
| App UI | Existing interface retained and renamed; normal target-browser/desktop acceptance remains local work |
| Windows .cmd/.ps1 setup/packaging | Source recipes supplied; not executed on Windows in this handoff |
| Hardware adapter | Experimental and read-only by default; no physical command trace or write evidence |
| Public Worker and vCard | Handler tests pass using a D1 mock; not deployed |
| Local Wrangler D1 integration | NOT RUN in this handoff |
| Automatic sync/publication receipt | Not implemented; export/import is manual and reviewed |
| Multiple profiles, search, advanced labels, multilingual UI | Backlog, not shipped |
| Android or iPhone writing app | Not implemented |
| Signed installer, auto-update, physical write protection | Not implemented |

`docs/TEST-REPORT.md` is the current evidence summary. Original prototype screenshots/results live in `docs/history/v0.1.0/`; they are explicitly historical, not fresh nfcraft UI or hardware results.

## Unresolved material inputs

Exact NFC reader/model/firmware, NFC-capable phone available for QA, approved long-lived public hostname, approved public profile fields, intended Cloudflare account and preview/production resource IDs. No purchase, ownership, account selection or publication permission is inferred from earlier proposed examples.

## First local objectives

Run the supplied checks in a local venv; exercise the app in a real browser; resolve target-OS startup and packaging problems; inspect attached hardware read-only if available. Prepare/test the public site locally even if hardware is absent. Move through `QUALITY-GATES.md`, marking independent blockers rather than stopping all development.

## Deliberate compatibility

`nfcctl.py`, installed `nfcctl`, and MCP names such as `nfc_status` remain supported aliases. Canonical CLI is `nfcraftctl.py` / `nfcraftctl`; MCP server name is `nfcraft`. SQLite/public manifest schema remains **1**. Slugs, card URLs and existing assignment formats are unchanged.

The default data root changed from `NfcCardOps` to `nfcraft`. A legacy journal blocks silent creation of a fresh default workspace. Explicit `--data-dir` and the opt-in importer are documented in `MIGRATION.md`.
