# nfcraft — current project state

Updated: 2026-09-06 (Asia/Tokyo). Current local version: **0.2.2**. Treat this file as the index for the next agent, not as evidence in place of test logs.

## Phone writer reliability — Card Writer 0.2.0 (2026-09-16)

`android/` holds Card Writer, a native single-card rewrite tool that needs no PC. It shares `nfcraft/ndef.py`'s encoder through a Java port, and `android/tools/parity.sh` diffs the two byte for byte on every run.

The bench problem it was written to fix was **write reliability, not correctness**. One presentation issues around thirty radio exchanges and the first build attempted each exactly once, so a weakly coupled wooden card failed roughly half of all taps and the operator had to nudge it until a pass survived. Every exchange is now retried with reconnection, writes are retried safely and confirmed by read-back, NAK codes are separated into transient and final, FAST_READ steps down before falling back to plain READ, and only pages that would change are written. The screen says "weak contact" while it is happening and the receipt records what the link cost.

**This is checked, not qualified.** 1,087 pruned-plan states and 10 link behaviours pass on a desktop JVM against a simulated misbehaving card, alongside the encoder parity check. None of it has met a wooden card since the change, and the recipient-facing check — tapping a written card on a *different* phone — remains NOT_RUN. See `android/README.md` for the full list of what is and is not proved.

## Desktop launch repair — 0.2.2

The prior shortcut hid/minimized the native window. A dedicated GUI executable now opens directly, while the console entry remains compatible. The actual installed shortcut is verified visible and non-minimized at 1320x920; the app was left open for the owner. No owner UI approval or card write was automated. **118 Python / 16 Worker** checks pass, with packaged library, native lifecycle and real ShellExecute shortcut acceptance. Current portable ZIP: `dist/nfcraft-0.2.2-windows-unsigned.zip`.

See [desktop repair report](../reports/2026-09-06-desktop-launch/REPORT.md). The normal startup target is `dist/nfcraft/nfcraft-desktop.exe`; the PowerShell installer only creates/configures shortcuts. Do not restore the old hidden launcher or assume IsWindowVisible alone means a usable window; require non-minimized dimensions too.

## Identity and guide checkpoint — 0.2.1

Reviewed IconFlow assets now serve the executable, native window, tray, app sidebar and browser. The offline English / Traditional Chinese guide is `nfcraft/web/guide.html`, linked from the app. Two content-addressed desktop shortcuts open the native app and guide. **114 Python / 16 Worker** tests pass; packaged bilingual guide, 56-card workflow and native lifecycle checks pass. No recipient service or physical acceptance claim changed.

Original source staging is preserved as the root commit of the owner's working repository. The explicit GitHub checkpoint request resolved source backup: a verified account, a repository-local GitHub noreply identity, and a remote for the working history. The session report records final checks and push confirmation. Initial hosted Windows runs exposed an 8.3 TEMP-alias test assumption; the test now verifies filesystem identity, and failed verification output is visible in CI. See the latest GitHub run for cross-platform status. Current package: `dist/nfcraft-0.2.1-windows-unsigned.zip`; old ZIPs remain available. See [checkpoint report](../reports/2026-09-06-checkpoint/REPORT.md).

## Card workshop milestone — 0.2.0

Implemented searchable inventory (batch/label/URL/UID), combined filters, 25-row UI pagination, matching CSV, quarantine shortcut, and per-card evidence details. Public profile edits have a live preview sharing the public Worker renderer, explicit saved/unsaved state and restore. Public export now has a review step with exact saved content, destinations, included/excluded counts, shared-profile impact and checksum-based stale-content refusal. Export records preparation only, never remote availability.

**113 Python and 16 Worker tests pass.** The 56-card synthetic browser acceptance covers pagination, filter/export parity, empty/review states, shared-profile warning, cross-window stale review, safe preview, focus stability and narrow layout. Real local Worker/D1 and 375px recipient-page/vCard browser checks pass. No journal or public manifest schema changed. Source, packaged workflows and native lifecycle evidence are indexed in [the current report](../reports/2026-09-06-library/REPORT.md).

The new unsigned package is `dist/nfcraft`; `dist/nfcraft-0.2.0-windows-unsigned.zip` was the 0.2.0 local ZIP. The prior 0.1.1 ZIP is retained. Remote publication, physical NFC and phone/printed-QR QA remain blocked on the already documented inputs. Git author identity was unresolved at this earlier milestone; see 0.2.1 above. Publication receipts, workspace namespace/equal-revision conflict handling, and automated sync remain **unimplemented**.

## Historical Windows bootstrap result

Native Windows 11, Python 3.12.10 in `.venv`, Node 24.18.0. **101 Python tests and 13 Worker tests pass**, together with compilation, syntax and daemon/CLI/MCP checks. Initial Windows failures were reproduced and fixed: byte-lock contention, locale-dependent JSON/startup output, and smoke-test child cleanup. A separate startup-error shutdown deadlock regression is fixed. Approval now exposes a bounded attempt cap and 15–600 second expiry; recovery remains one identity.

Source and unsigned packaged app passed isolated Edge workflow acceptance with ten simulated cards, duplicate/foreign/locked/wrong-chip refusal, interruption/recovery, expiry, exports/QR, backup, Unicode profile and restart without re-arming. Native desktop and packaged desktop/tray launch/close passed. Package and workspace paths containing spaces/Chinese characters passed. Backup/restore with recovery passed on synthetic copies.

Real **local** Wrangler 4.129.0 + D1 integration passed, including repeated and older-revision imports, exact card paths, vCard, 404/410/405, HEAD, escaping and security headers. Tooling has an npm lockfile; Windows Python resolution is captured in `requirements-windows.lock`.

Artifacts: `dist/nfcraft/nfcraft.exe` and `dist/nfcraft-0.1.1-local-windows-unsigned.zip` (ignored local output). **Not signed; not clean-machine-qualified.** See [session report](../reports/2026-09-06-bootstrap/REPORT.md) for evidence, reproduction and remaining gates.

Read-only discovery found no connected Windows smart-card reader; PC/SC reports unavailable and the Smart Card service is stopped. No service/driver changes or physical commands were attempted. Physical NFC and phone/print QA are **BLOCKED**. Cloud account/hostname/profile approval is unresolved; remote preview and production are **BLOCKED**. No remote resources or DNS were changed.

No `.git` existed in the handoff. A local `work/local-bootstrap` branch was initialized; the original source is staged and preserved in an ignored binary patch. At bootstrap, commits awaited author identity and no remote existed; 0.2.1 supersedes that blocker. No owner journal was opened or migrated.

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
| App UI | Windows source/packaged browser workflow passed; configurable bounded approval added |
| Windows .cmd/.ps1 setup/packaging | Unsigned local build and source/native packaged startup/restart checks passed; clean-machine and tray-menu visual QA outstanding |
| Hardware adapter | Experimental and read-only by default; no physical command trace or write evidence |
| Public Worker and vCard | Handler tests pass using a D1 mock; not deployed |
| Local Wrangler D1 integration | PASS on Windows using real local Wrangler/D1 with synthetic exports |
| Automatic sync/publication receipt | Not implemented; export/import is manual and reviewed |
| Search, filters, card details, live recipient preview | Implemented in 0.2.0; browser acceptance passed |
| Public export review | Implemented with stale-content refusal and shared-profile warning; not deployment/receipt tracking |
| Multiple profiles, advanced labels, multilingual UI | Backlog, not shipped |
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
