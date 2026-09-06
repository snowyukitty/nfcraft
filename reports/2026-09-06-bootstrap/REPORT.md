# Windows bootstrap session

Date: 2026-09-06, Asia/Tokyo. Product/source version: nfcraft 0.1.1 plus the local changes described here. Objective: retain the existing workstation, establish Windows operation, fix reproduced defects, and complete unblocked package/public-site acceptance.

## Environment and provenance

- Windows 11 build 26200, native PowerShell, Python 3.12.10, Node 24.18.0. Repository-local `.venv`; no global toolchain, driver, service, firewall or execution-policy changes.
- No `.git` existed. Initialized branch `work/local-bootstrap`; original source staged before edits. Git commit failed because no author name/email is configured. The owner has been asked; no identity was invented and no remote/push/release was created.
- Original staged source also preserved in ignored `.local/evidence/source-handoff.patch`. Keep that checkpoint until author identity permits the initial commit. Current implementation changes are unstaged/new files on top of that staged source. Original `MANIFEST.sha256` describes the delivered handoff, not the changed tree; it was not hand-edited.
- Preflight found no legacy journal. Tests used only self-created synthetic workspaces. No owner journal, card assignment, URL or profile was migrated or reset.
- Scope: this repository's runtime/CLI, approval UI, launchers/build recipe, local test tooling and documentation. Atlas lease `nfcraft`, agent `codex-nfcraft`, was claimed before writes; release status is recorded below.

## Reproduced defects and changes

1. **Windows lock contention:** the second opener read a byte already locked by the first writer. Windows raised `PermissionError` before the handler and left an open handle. Size inspection now avoids reading that byte and initialization is inside the error/close boundary. Repeated and cross-process contention tests verify `WORKSPACE_BUSY`, intact owner runtime and subsequent lock acquisition.
2. **Windows encoding:** CLI JSON used cp1252; UTF-8 consumers failed on a middle dot, and a Unicode workspace made startup output crash. CLI/MCP standard streams and startup output now explicitly use UTF-8. The process smoke uses a Chinese/space-containing workspace and UTF-8 MCP decoding.
3. **Windows smoke cleanup:** terminating the venv redirector could leave its child holding SQLite. Cleanup now terminates only that owned test process tree. Baseline cleanup failure remains in the original log; no owner processes were stopped.
4. **Startup error cleanup:** `HTTPServer.shutdown()` can block if `serve_forever()` never ran. Track the serving thread and only shut down a running loop. A forced runtime-file creation failure now returns `STARTUP_IO` promptly and releases the workspace.
5. **Usable bounded approval:** the dialog now lets an operator choose maximum attempts and 15–600 seconds. Recovery fixes the cap at one and preserves its original identity. Backend limits, manual hardware approval and all write guards remain unchanged.
6. **Windows launch/build:** launchers forward explicit arguments. Build dependencies were resolved in the venv and captured in `requirements-windows.lock`; the build can install this snapshot. Wrangler 4.129.0 and its npm-generated lockfile are project-local.
7. **Repeatable acceptance:** added `smoke_browser.mjs`, `smoke_desktop.py`, `smoke_packaged_windows.py`, `smoke_public.py`, `smoke_backup.py`, and three runtime regression tests. No framework replacement or public control API was introduced.

## Actual evidence

All paths below are repository-relative and ignored local evidence. Historical `docs/test-evidence/` and `docs/history/` are unchanged.

| Result | Command/procedure | Evidence |
|---|---|---|
| PASS | `.venv/Scripts/python.exe scripts/preflight.py` | `.local/evidence/preflight.json` |
| FAIL, fixed | Initial `scripts/verify.py --require-node --output .local/evidence/baseline`: 98 Python tests, one error; daemon smoke failed | `.local/evidence/baseline/summary.json`, `python-unittest.txt`, `demo-process-smoke.txt` |
| PASS | Final `scripts/verify.py --require-node`, invoked by build: **101 Python tests**, compilation, daemon/CLI/MCP, UI/Worker syntax, **13 Worker tests** | `.local/verification/summary.json` and per-check logs |
| PASS | `node scripts/smoke_browser.mjs` | `.local/evidence/browser-final.txt`; `browser space 測試-5dG5Lw/summary.json` and screenshots |
| PASS | `node scripts/smoke_browser.mjs --packaged` on final build | `.local/evidence/packaged-browser-final.txt`; `browser space 測試-DXFoUU/summary.json` and screenshots |
| PASS | `.venv/Scripts/python.exe scripts/smoke_desktop.py` | `.local/evidence/desktop-final.txt` |
| PASS | `.venv/Scripts/python.exe scripts/smoke_packaged_windows.py` | `.local/evidence/packaged-native-final.txt`; `native package 測試 jb3xdu21/summary.json` |
| PASS | `.venv/Scripts/python.exe scripts/smoke_public.py` | `.local/evidence/public-final.txt`; `public-67hj32t3/summary.json`, schema/import/worker logs |
| PASS | `.venv/Scripts/python.exe scripts/smoke_backup.py` | `.local/evidence/backup-restore.txt` |
| PASS | `scripts/build-windows.ps1` | `.local/evidence/windows-build-final.txt` |
| PASS | All three Start CMD launchers with `--version` | Each printed `nfcraft 0.1.1` and exited successfully |
| PASS | `pip check`, package ZIP contents/hash check, `git diff --check` | No broken requirements; `.local/evidence/artifacts.json`; no whitespace errors |
| BLOCKED | `nfcraftctl.py --mode hardware doctor`; present Windows SmartCardReader enumeration | `PCSC_UNAVAILABLE`; no present reader, Smart Card service stopped/manual; no physical commands |

The browser runs used isolated Edge, not a signed-in browser. The built-in browser reported unavailable before this fallback. Test capabilities belonged only to each generated demo workspace and were never emitted in reports. Source screenshots were visually reviewed. The native source test verified connected DOM/WebView2 and fragment removal; packaged native tests verified window/tray launch, close, draft persistence and lock/runtime cleanup. Packaged browser tests verified the bundled UI separately.

Both browser runs exercised ten distinct cards, holding/inspection, duplicate refusal, foreign/locked/wrong-chip refusal, interruption and explicit original-URL recovery, an operator-selected attempt cap/15-second expiry, profile draft, CSV/public manifest/QR downloads, backup, crash/restart persistence and no automatic re-arm. Results are **simulated**. Hidden occupied-region and pause-between-page protection retain unit evidence; they are not physical acceptance.

Local public tests ran the actual installed Wrangler, workerd and D1 storage. They checked schema/import, idempotent retry, older-revision preservation, valid card, HEAD, vCard, suspended 410, unknown/root 404, POST 405, escaping and security headers. No remote auth/account selection occurred. Root 404 was expected. Equal-revision/unrelated-workspace conflict handling and publication receipts remain backlog; no automatic sync is claimed.

The backup drill restored a new synthetic copy, checked SQLite integrity/audit/identities/URLs/disarmed state, recovered the quarantined identity, and verified the archived source stayed unchanged.

A first native-package harness closed WebView2 before initialization and failed while printing a Unicode evidence path. It was corrected to allow native initialization, check diagnostic failures and print UTF-8; the final run passed. This was a harness correction, not suppressed runtime evidence.

## Artifacts and operation

Historical artifact note: the later 0.2.0 card-workshop session rebuilt `dist/nfcraft`. The hashes below describe the bootstrap build; its original 0.1.1 ZIP remains preserved. Use the newer session report for the current executable.

- `dist/nfcraft/nfcraft.exe` — unsigned portable app; keep its entire sibling `_internal` directory.
- `dist/nfcraft-0.1.1-local-windows-unsigned.zip` — 23,767,729 bytes. ZIP includes bundled web assets; no journal, runtime credential, virtual tags, `.local`, or MCP cache was included.
- EXE SHA-256: `ba2616098ca81e7d537e73f2f47d6479c5e611593bb00ec6ae2a8109b93ff2c7`.
- ZIP SHA-256: `a7680f8accc45885eea519efa9f479ffdb374e97f1615048d1772ef02f4a488d`.
- Authenticode: `NotSigned`. This is not a signed installer, clean-machine result or hardware qualification.

Source browser app: double-click `Start nfcraft.cmd`, or run `.venv\Scripts\python.exe run.py`. Stop with Ctrl+C in its terminal. Closing a browser tab does not stop the app.

Source desktop: double-click `Start Desktop.cmd`. Packaged desktop: run `dist\nfcraft\nfcraft.exe --desktop` (optionally `--tray`). Close the native window to stop. Browser package: double-click `dist\nfcraft\nfcraft.exe`; stop from its console with Ctrl+C.

Default is simulation. Data remains under the normal per-user nfcraft root, separated into demo/hardware; optional `--data-dir` selects another root. Launchers now accept that flag. Keep the operator URL private. Tests used ephemeral loopback ports and left their daemons stopped; no fixed port was newly allocated.

## Reproduction details

Run core checks with the venv. From `cloudflare/`, `npm ci` installs the pinned Worker tooling; then run `scripts/smoke_public.py` from the root with the venv. Browser smoke requires isolated test dependencies: `npm install --prefix .local/browser --save-exact playwright@1.58.2`; this Windows harness uses installed Edge. Desktop/QR/hardware/build extras are captured in `requirements-windows.lock`; use `scripts/build-windows.ps1 -InstallDependencies` to install that resolution and build. The Python snapshot pins versions, not hashes, and was validated only on this Python/Windows combination.

Wrangler flags/requirements were checked using the installed CLI help, npm package metadata, and official [installation documentation](https://developers.cloudflare.com/workers/wrangler/install-and-update/) and [D1 command reference](https://developers.cloudflare.com/d1/wrangler-commands/). This source check is separate from local runtime evidence.

## Remaining gates and continuation

| Gate | Status |
|---|---|
| G0 baseline | PASS locally; Git commits await author identity |
| G1 local workflow | PASS for recorded source/packaged mock workflows; individual unexercised UI paths retain unit-only evidence |
| G2 read-only reader | BLOCKED: no attached reader; PC/SC unavailable |
| G3 physical card/pilot | BLOCKED on G2, durable origin and explicit expendable-card approval |
| G4 public site | Local integration PASS; remote preview/production BLOCKED on approved account, hostname and public profile |
| G5 Windows package | This-host portable/browser/native lifecycle PASS; clean-machine/AV/tray-menu visual QA NOT_RUN; signing not implemented |
| G6 distribution | BLOCKED on physical/phone/printed-QR/publication/protection decision |

No actual Codex/Claude client configuration or hosted CI was run; CLI/MCP subprocess interoperability passed. No protection/locking/overwrite capability was added. No throughput measurement is claimed.

The owner was asked for Git author name/email and the intended Cloudflare account, long-lived hostname and public profile. No answer was assumed. Next agent: finish the initial source commit using the staged handoff once identity is provided, then review/stage explicit changed paths and commit this working slice. Prepare a concrete preview/production resource/content/backup plan after destination input; obtain scoped approval before cloud mutation. Do not select a default logged-in account. Connect a reader and complete read-only qualification before any physical write approval. Publication receipts/conflict prevention are the next independent product slice if those external inputs remain unavailable.

No data schema changed; legacy aliases, card identity and URL formats are retained. Roll back application code/package against a stopped, backed-up compatible workspace; do not delete or replace a journal. Owner data was not changed, so no owner-data rollback is necessary. Keep test evidence private and preserve the initial handoff checkpoint.

Lease state: `nfcraft` lease released with `uv run atlas lease release nfcraft --agent codex-nfcraft` after final repository checks. No delegated agents or test daemons are intentionally left running.
