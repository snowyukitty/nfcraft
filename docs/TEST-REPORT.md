# nfcraft — verification evidence

## 0.2.2 desktop repair

118 Python / 16 Worker checks pass. Real shortcut acceptance now checks GUI subsystem, visible/non-minimized window, normal dimensions and clean close. The actual owner desktop shortcut was opened and its window metadata verified; no owner UI operation was automated. See [repair report](../reports/2026-09-06-desktop-launch/REPORT.md).


## 0.2.1 checkpoint

Baseline 113 Python / 16 Worker PASS; final 114 Python / 16 Worker PASS. Guide/static security and native/icon packaging checks are indexed in [the checkpoint report](../reports/2026-09-06-checkpoint/REPORT.md). Historic evidence below remains unchanged.


## Card workshop 0.2.0 — 2026-09-06

**PASS:** 113 Python tests (12 new library/export regressions), 16 Worker tests (3 shared-renderer regressions), syntax/compilation and CLI/MCP smoke. Dedicated browser acceptance used 56 freshly simulated cards to check 25-row pagination, filters/CSV, quarantine/empty views, detail facts, safe recipient preview, cross-window stale export rejection and shared-profile scope. The existing write/recovery browser workflow also passes. Real local Worker/D1 and 375px recipient rendering/vCard download pass. Source/packaged native and browser evidence is recorded in [the current session report](../reports/2026-09-06-library/REPORT.md).

These are local/synthetic checks. Hardware, actual phone/printed QR, remote deployment, clean-machine/AV and tray-menu visual qualification remain blocked or NOT_RUN as described below. The Python journal and public manifest remain schema 1. Fresh logs are separate from the baseline and original delivery evidence.

## Windows bootstrap — 2026-09-06

**PASS:** 101 Python tests, 13 Worker handler tests, compilation, JS syntax, disposable daemon/CLI/MCP; source and unsigned packaged Edge workflow; native desktop, packaged desktop/tray lifecycle; local Wrangler/D1 integration; synthetic backup/restore and original-identity recovery. Windows 11, Python 3.12.10, Node 24.18.0, Wrangler 4.129.0. Approval cap and expiry are exercised through the real UI.

**Initial FAIL, resolved:** 98-test baseline had one Windows lock error; process smoke failed on Windows JSON encoding and cleanup. A later Unicode-workspace startup run exposed console encoding failure, also fixed. Native-package harness initially closed WebView2 before initialization and failed to print its Unicode evidence path; corrected harness passed. These failed logs remain locally preserved.

**BLOCKED:** physical NFC (no attached reader/PCSC service unavailable), phone/printed-card QA, remote cloud preview/production (no approved destination/profile). **NOT_RUN:** clean-machine installer/antivirus acceptance, tray-menu visual inspection, hosted CI, real external agent-client configuration. Signing is not implemented; Authenticode reports `NotSigned`.

Fresh evidence is under ignored `.local/evidence/` and `.local/verification/`. The full command/evidence map is in [the session report](../reports/2026-09-06-bootstrap/REPORT.md). Original delivery logs below and `docs/test-evidence/` are preserved unchanged.

## Original 0.1.1 handoff verification report

Date: 2026-09-05. Environment: **Linux container, Python 3.13.5, Node v22.16.0**. These checks were run while creating this handoff, not on the owner's Windows computer.

## Executed for the renamed source

| Check | Actual outcome / scope |
|---|---|
| Python unittest suite | **98 tests passed**; local synthetic data only |
| Public Worker handler suite | **13 tests passed** with mocked D1 |
| Python compilation | PASS for package, scripts and tests |
| UI and Worker JS syntax | PASS using Node `--check` |
| Child-process demo daemon | PASS in a new disposable temporary workspace |
| Live CLI draft/state against that daemon | PASS; draft creation did not arm hardware or initialize cards |
| Agent token cannot arm | PASS; loopback API returns the expected denial |
| MCP stdio initialize/notification/status | PASS against the child demo daemon; server name is nfcraft |
| CLI proxy/redirect restrictions | PASS; ambient HTTP proxy bypassed and redirect refused without contacting external target |
| Version/import/package consistency | PASS; nfcraft 0.1.1 and canonical/compatibility CLI names |
| Legacy import tests | PASS for opt-in/schema/mode/source lock/destination refusal/audit/identity preservation/no token copy |
| Planned-region data safety regression | PASS; empty NDEF with occupied planned bytes is not overwritten |
| Public manifest validation regressions | PASS; checksums, simulation marker, fields, duplicate slugs, revisions, URL mapping and UID exclusion |
| Python wheel build | PASS using `pip wheel . --no-deps --no-build-isolation` |
| Wheel contents | PASS: package modules, web assets and three CLI entrypoints included |
| TOML/JSON configuration parse | PASS for shipped config/templates |

The 98 Python tests include the original 76 plus 22 new handoff/transport regressions. The original 0.1.0 baseline was separately re-run before editing: 76 Python and 13 Worker handler tests passed. Historical prototype UI screenshots/results are under `history/v0.1.0/`; they are not evidence of a newly rendered nfcraft interface or real card operation.

## Evidence files

`test-evidence/summary.json` records the unified runner's actual outcomes. Corresponding raw logs are `python-unittest.txt`, `python-compile.txt`, `demo-process-smoke.txt`, `ui-syntax.txt`, `worker-syntax.txt`, `worker-tests.txt` and `wheel-build.txt`. Compilation/syntax success may produce an empty log; the summary records the exit code.

The process smoke creates and terminates its own **demo-only** daemon. It does not read the owner's data, approve a real batch, connect a reader, or make a remote request. Unit tests exercise mock writing and recovery. SQL validation/generation remains reviewable file creation, not a deployment.

## Not performed for this handoff

**NOT_RUN:** physical NFC reads/writes; real ACR1552U/firmware protocol qualification; target Windows/PCSC driver integration; a normal browser UI navigation/rendering acceptance run for the newly renamed version; pywebview/pystray execution; Windows packaging or signing; actual Codex/Claude client integration; Android/iPhone/printed-wood QR/vCard QA; local Wrangler+D1 execution; remote Cloudflare/D1/DNS/TLS changes; CI execution on a remote GitHub repository.

No cloud account was selected and no public resources were created. `hardware_qualified` remains false, hardware writes remain opt-in experimental, and all permanent protection/lock operations remain absent. A wheel build is not a Windows installer and does not qualify optional hardware dependencies.

## Reproduce locally

```sh
python scripts/preflight.py
python scripts/verify.py --require-node
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir .local/wheels
```

Use the project's virtual-environment interpreter. Wheel creation requires a compatible installed build backend; resolve it in the local environment rather than changing global tools. The unified runner requires no optional NFC/QR/desktop dependencies. Without Node, checks are explicitly NOT_RUN; `--require-node` makes that incomplete run non-successful.

Record new local runs separately and do not overwrite this delivery evidence. Complete `QUALITY-GATES.md` on the actual equipment before broader readiness claims.
