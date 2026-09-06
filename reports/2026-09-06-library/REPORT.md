# Card library milestone

Execution note: retain the Windows desktop workstation and its web interface. Deliver searchable/paged inventory, matching exports, shared recipient preview, and explicit public export review with stale-content refusal. No card/URL/schema migration, cloud mutation, or new hardware authority. Validate selection and export safety in Python; shared rendering in Worker tests; real UI and local D1; rebuild the unsigned Windows package. Rollback is code/package replacement against the unchanged schema-1 journal after stopping and backing up.

Baseline: `scripts/verify.py --require-node --output .local/evidence/library-baseline` PASS (101 Python, 13 Worker tests plus compilation/syntax/process smoke). The earlier source checkpoint remains staged; commits still await owner Git identity. This session holds the `nfcraft` Atlas lease as `codex-nfcraft`.

## Outcome

Delivered **0.2.0 — Card workshop** on Windows 11, native Python 3.12.10/Node 24.18.0, using the existing `.venv` and project-local Wrangler 4.129.0. No new framework or database was substituted for the app. The architectural recommendation is a Windows desktop workstation (with the same browser UI available) plus a separate responsive recipient page. See [ADR 0002](../../docs/adr/0002-card-workshop.md) for the research and decisions.

### Implemented behavior

- Card library: Unicode/case-insensitive search by batch label, URL, UID or error; combined batch/write-state/route-intent filters; 25-row UI pagination; quick quarantine/verified views; clear empty states. CSV uses all matching rows across pages, not only the visible page.
- Card details: stable physical label/URL with separate local verification, export eligibility, unchecked public availability and unrecorded phone-QA facts. Private UID and verification timestamp/hash/error are available in an expandable section. No new physical/issuance attestations are fabricated.
- Recipient preview: the public Worker and local preview share `public-card.mjs`. Profile edits render immediately and safely; preview actions are inert. Unsaved changes are marked and the saved draft can be restored. The local CSP stays unchanged; a constructed stylesheet scopes the trusted shared CSS to the preview's shadow root.
- Reviewed export: exact saved profile content, encoded origins, enabled/suspended routes, excluded unverified matches, route entries and checksum. Download rechecks the current content while holding the engine lock and refuses a changed review with `EXPORT_CHANGED`. Export preparation is audited with `deployed: false`.
- Shared-profile warning: filtered route selection is not profile isolation. Review reports additional locally verified routes sharing the included profiles and warns that importing the profile can update other public cards too. The remote database may contain further routes that this local app cannot count.
- Python/UI/npm metadata now report 0.2.0. An unsigned portable folder and ZIP were built. The prior 0.1.1 ZIP is retained.

### Paths changed in this increment

New: `nfcraft/library.py`, `nfcraft/web/library.js`, `nfcraft/web/public-card.mjs`, `tests/test_library.py`, `scripts/smoke_library.mjs`, `scripts/smoke_recipient.mjs`, `docs/adr/0002-card-workshop.md`, this report.

Updated: `nfcraft/server.py`, `nfcraft/store.py`, `nfcraft/web/app.js`, `nfcraft/web/index.html`, `nfcraft/web/style.css`, `cloudflare/worker.mjs`, `cloudflare/worker.test.mjs`, `scripts/smoke_browser.mjs`, `scripts/smoke_public.py`, `scripts/verify.py`, `nfcraft/__init__.py`, `pyproject.toml`, `cloudflare/package.json`/generated lockfile, `README.md`, `AGENTS.md`, changelog/state/test/backlog documents. The bootstrap report has a note identifying its now-historical executable path. Earlier bootstrap code changes remain intact.

## Verification evidence

Fresh evidence is ignored under `.local/evidence/`; the final unified build verification is under `.local/verification/`. No historical delivery evidence was overwritten.

| Result | Actual command/check | Evidence |
|---|---|---|
| PASS | Baseline `scripts/verify.py --require-node --output .local/evidence/library-baseline` | `library-baseline/summary.json` — 101 Python / 13 Worker |
| PASS | `python -m unittest discover -s tests -p test_library.py -v` | `library-tests.txt` — 12 new regressions |
| PASS | `scripts/build-windows.ps1`, including `scripts/verify.py --require-node` | `library-build.txt`, `.local/verification/summary.json` — **113 Python / 16 Worker**, compilation, app/library/Worker syntax, daemon/CLI/MCP |
| PASS | `node scripts/smoke_browser.mjs` | `library-browser.txt`; source write/recovery workflow |
| PASS | `node scripts/smoke_library.mjs` | `library-acceptance.txt`, `library-QPmvAn/summary.json` and screenshots |
| PASS | `node scripts/smoke_library.mjs --packaged` | `library-packaged-acceptance.txt`, `library-Av6LU3/summary.json` and screenshots; final shared-profile warning included |
| PASS | `node scripts/smoke_browser.mjs --packaged` | `library-packaged-workflow.txt`, `browser space 測試-Fs4B8c/summary.json` |
| PASS | `scripts/smoke_desktop.py` | `library-native.txt` — real source WebView2 loads connected DOM and closes cleanly |
| PASS | `scripts/smoke_packaged_windows.py` | `library-packaged-native.txt`, `native package 測試 kq0rb8qh/summary.json` — packaged desktop/tray start, close, restart persistence |
| PASS | `scripts/smoke_public.py --browser` | `library-public-browser.txt`, `public-vdl2qg3z/summary.json`, `browser.log`, `recipient-mobile.png` |
| PASS | `scripts/smoke_backup.py` | `library-backup.txt` — synthetic restore, identity-preserving recovery, archive unchanged |
| PASS | `pip check`, launcher/CLI `--version`, `git diff --check` | No broken requirements/whitespace errors; both report 0.2.0 |
| PASS | ZIP content inspection and SHA-256 | `library-artifacts.json`; required JS assets present, no journal/runtime token/virtual tags/MCP cache |
| BLOCKED | Read-only `nfcraftctl.py --mode hardware doctor` | `PCSC_UNAVAILABLE`; no hardware commands/writes performed |

The new regression suite covers Unicode/literal search (including SQL-like text), combined filters, stable pagination, invalid/repeated query rejection, all-matches CSV, public UID exclusion, unverified-only export refusal, exact reviewed checksum, profile/route change invalidation, audit semantics, and agent denial of operator review/export endpoints. Existing agent manifest access remains compatible. Worker regressions verify shared rendering, inert preview, escaping and invalid route/credential-link suppression.

The dedicated browser fixture creates 56 synthetic cards, including one quarantined identity. It checks non-overlapping 25-row pages, matching CSV, empty/review states, card detail facts, cross-window profile edits invalidating an open review, exact re-reviewed export, safe literal script text in preview, restore/dirty state, focused-row stability across polling and a narrow layout without horizontal overflow. Both source and packaged acceptance use isolated Edge and only test-owned demo capabilities.

The public test runs actual local Wrangler/workerd/D1, checks valid/unknown/suspended/method/HEAD/vCard/security behavior and idempotent/older-revision imports, then opens the actual served card route at 375px. Contact download and layout pass. **A narrow desktop browser is not physical phone QA.** Screenshots of recipient preview, export review, inventory and the actual local recipient page were visually inspected.

No final failing check remains. Physical NFC, phone/printed-QR QA and remote deployment remain BLOCKED. Clean-machine/AV acceptance, tray-menu visual QA, hosted CI and an actual external agent-client configuration are NOT_RUN. Signing is not implemented; Authenticode reports `NotSigned`.

## Package and launch

- Current EXE: `dist/nfcraft/nfcraft.exe`; keep the complete `_internal` directory with it.
- Current ZIP: `dist/nfcraft-0.2.0-windows-unsigned.zip`, **23,782,785 bytes**.
- EXE SHA-256: `b6b0bfc7baaadc7af8bcb73130d4524290e292fd8e01af3520313720d0efcfe6`.
- ZIP SHA-256: `bf4d94eb78fc3ea79034fdfc9a0901bec4eadd47f64cace50426e0ee8909fdd1`.

Recommended local use: double-click `Start Desktop.cmd`; close the native window to stop. Browser mode remains `Start nfcraft.cmd`, stopped with Ctrl+C in the terminal. Packaged desktop: `dist\nfcraft\nfcraft.exe --desktop`; optional `--tray`. Default remains demo. The normal per-user demo/hardware data separation is unchanged. Tests used ephemeral loopback ports and stopped their own processes.

Try **Public profile** to edit and preview; **Card inventory** to filter; click a card label for details; choose **Review public export** before downloading. The review creates a file only. Changing a local profile or route does not change public data until an independently approved import/deployment occurs.

## Compatibility, rollback and limitations

Journal and public manifest schemas remain **1**. Card UIDs, assigned slugs/URLs, compatibility CLI/MCP names and guarded memory writes are unchanged. There was no owner-data migration or reset. The only additional persisted behavior is an ordinary hash-chained `public_export_prepared` audit event. Existing code treats event kinds as data.

The prior unsigned 0.1.1 ZIP is retained for code rollback. Stop, back up and select one authoritative workspace before changing app versions; never roll back by replacing/deleting the journal or recycling identities. The old version can read this unchanged schema, but its export UI lacks this version's review checks.

Paging currently bounds visible DOM rows. The legacy state endpoint and in-memory selection still read the full inventory; no large-fleet throughput claim is made. Profile sharing is explicit, not isolated per filtered export. No workspace namespace, equal-revision import conflict protection, automatic cloud sync, publication acknowledgment, persisted phone QA or ready-to-distribute badge was added.

Owner input still needed: approved Cloudflare account/hostname/public profile, reader/phone access and later explicit one-card write approval; Git author name/email for commits. No destination or author identity was inferred from the request to keep improving the app. The original source remains staged with the ignored baseline patch preserved; new changes remain reviewable on top. No remote was created or pushed.

The next product increment is an authoritative publication plan/receipt with workspace namespace and conflict-safe imports; it must prove destination and exact URLs before claiming availability. Hardware qualification can proceed independently when a reader is available. Research references and their influence are recorded in ADR 0002, with Cloudflare CLI/type checks separate from runtime evidence.

Lease: released after final checks with `uv run atlas lease release nfcraft --agent codex-nfcraft`; Atlas confirmed release. No subagents were used.
