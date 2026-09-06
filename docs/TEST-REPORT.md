# nfcraft 0.1.1 — handoff verification report

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
