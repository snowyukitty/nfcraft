# nfcraft 0.2.1 — identity, bilingual guide and GitHub checkpoint

Date: 2026-09-06 (Asia/Tokyo). Scope: this repository, the requested Windows desktop shortcuts, and the owner-authorized private GitHub checkpoint. No hardware operation or cloud deployment is part of this checkpoint.

## Outcome

The existing app now has a source-bound IconFlow identity across native window, executable, tray, sidebar and browser favicon. A responsive English / Traditional Chinese guide explains the product, first demo, separate acceptance stages, privacy and recovery. It opens offline and from the app's Guide link. No external fonts, analytics, account or daemon is required to read it.

The Windows desktop has `nfcraft` and `nfcraft Guide 使用說明` shortcuts. The app shortcut uses `scripts/start-desktop.ps1`, prefers the packaged native app with tray, and hides its console. Closing the native window stops the workstation. Browser mode still stops with Ctrl+C. The guide shortcut opens the bundled local HTML. IconFlow read back both shortcut targets and their content-addressed ICO paths; no Explorer/cache reset was used. The helper uses a process-scoped PowerShell execution-policy argument, not a persistent machine policy change.

## Design and implementation

- `master.svg`, `master-review.json`, `iconflow.toml`, `casebook/2026-09-06-nfcraft-tap-card.md`, `docs/ICON-DESIGN.md`: essence **connect**, clipped contact card with one 128-unit curved tap aperture. Four concept directions, two object finalists plus a device-free control; the painted arc lost its silhouette cue, so the final arc is a transparent cut.
- `nfcraft/web/icons/`: 15 IconFlow outputs, including multi-frame ICO, favicon, native PNG/ICNS and color/alpha tray assets. Electron is an output format target only; the app remains Python/WebView2.
- All six review axes **4/5**: legibility, distinctiveness, balance, color, scalability, craft. Clean automated check, inspected bake/neighbour/static sheets and actual Review Lab in isolated Edge, exported scored receipt, gated ship PASS. Case lint PASS. The casebook flags distinctiveness/scalability as first-pass evolution targets; no shared toolkit was modified.
- `nfcraft/web/guide.*`: offline bilingual page, keyboard language controls, starter anchors, expandable FAQs, mobile layout and reduced-motion support. Without JavaScript both languages remain readable.
- `nfcraft/server.py`: exact static allowlist for guide and favicon, with existing Host/Origin/CSP boundaries retained; no generic file serving.
- `nfcraft/desktop.py`, `nfcraft/__main__.py`, packaging and `scripts/start-desktop.ps1`: same reviewed identity everywhere and repository-owned shortcut entrypoint.
- `scripts/smoke_guide.mjs`, `tests/test_library.py`, `scripts/verify.py`: offline interaction/layout checks, static allowlist/traversal checks and guide syntax gate.

## Verification

Baseline: **113 Python / 16 Worker** PASS before implementation (`.local/evidence/icon-baseline.txt`). New static-asset/security regression: **13 library tests** PASS (`icon-library-tests.txt`).

Source guide: PASS at 1440px and 375px in both languages, including all image assets, language state, FAQ and anchor interaction, no horizontal overflow and no page exceptions (`.local/evidence/guide/summary.json`). English desktop and Traditional Chinese mobile screenshots were visually inspected. First guide run occurred before icon shipping and correctly failed its missing-image assertion; shipping the required assets resolved it.

Final build: `scripts/build-windows.ps1` PASS, including **114 Python / 16 Worker** tests, compilation, daemon/CLI/MCP and app/library/guide/Worker syntax. `scripts/preflight.py` PASS; no reader was accessed. Final checks:

| Result | Check | Local evidence |
|---|---|---|
| PASS | `node scripts/smoke_guide.mjs --packaged` | `.local/evidence/guide/packaged-summary.json` and four language/viewport screenshots |
| PASS | `node scripts/smoke_library.mjs --packaged` | `.local/evidence/icon-packaged-library.txt`, `library-pyqWSZ/summary.json` |
| PASS | `python scripts/smoke_desktop.py` | `.local/evidence/icon-native.txt` |
| PASS | `python scripts/smoke_packaged_windows.py` | `.local/evidence/icon-packaged-native.txt`, `native package 測試 kwt9to29/summary.json` |
| PASS | Embedded EXE icon extracted with Windows `ExtractAssociatedIcon`, then visually inspected | `.local/evidence/icon-extracted.png` |
| PASS | ZIP includes guide, desktop and tray assets; excludes runtime/journal files | `.local/evidence/icon-artifacts.json` |
| PASS | `git diff --cached --check`; staged baseline and final secret/artifact scans | No whitespace errors or credential-pattern findings; local caches/data excluded |

Current ZIP: `dist/nfcraft-0.2.1-windows-unsigned.zip`, **23,338,600 bytes**, SHA-256 `3f514386e8f5afa870c58533d52f2093465affdbb6da295d209b0d42d87d56d4`.
EXE SHA-256: `f81299c4508d6282a27b1ad8dfe188e6122823991a1502a7e2ae114730fdb3a2`. Authenticode: `NotSigned`.

Shortcut target/icon properties and the native application were checked separately. Clicking the installed shortcut into the owner's normal data workspace, tray-menu visual QA and clean-machine/AV acceptance are NOT_RUN. No normal workspace was opened to manufacture evidence.

## Data, publication and source history

No journal schema, card identity, URL or database migration. No owner workspace was opened by automation. Native/browser workflow checks use fresh synthetic demo workspaces. The old 0.1.1 and 0.2.0 unsigned ZIPs are retained.

The handoff originally had no Git history. Its exact staged source was preserved as root commit `b61881e`, before staging any session improvements. For the explicit push request, the authenticated GitHub account was verified as `snowyukitty` (ID 270071858); repository-local Git identity uses that name and its standard ID-based GitHub noreply address. No private email was inferred. `snowyukitty/nfcraft` was absent and has now been created **private**, with no visibility change to any existing repository. The existing workflow only tests code (no credentials, deployment or release). Checkpoint destination: `origin/main`, with the complete source history. A main push triggers the existing Windows/Linux Python 3.11/3.13 matrix; hosted results must be read from GitHub and are not implied by the local pass. No release/tag or Pages deployment is included.

Tracked evidence copies normalize Windows line endings; original local logs remain untouched. A preliminary raw SVG digest comparison was inappropriate because IconFlow hashes its normalized renderer input; the toolkit's `svg_sha256` verifies the final source-bound receipt. SVG line endings are now explicit in `.gitattributes` for durable checkouts.

Physical reader qualification, a separately approved single-card write, real phone/printed-QR acceptance, code signing, clean-machine acceptance and public deployment remain unfulfilled. Cloud destination/profile approval is still required. Next bounded engineering task: publication plan/receipt with workspace namespace and equal-revision conflict protection, independently of hardware qualification.

## Hosted Windows follow-up

Initial checkpoint `217c0fb` reached private `origin/main`, with a matching remote SHA and clean worktree. GitHub run `34005519265` passed both Linux jobs but failed both Windows jobs. This was a real test failure, not a billing refusal. The verifier initially hid failure details in runner-local files, so `5774466` exposes failed command output with UTF-8 diagnostics. A bounded branch dispatch (`34005673040`) identified the exact failure: an existing handoff test compared the Windows TEMP 8.3 alias `RUNNER~1` with its resolved long path even though both identify the same existing directory.

The test now uses `Path.samefile` to prove the original directory is reused. No runtime path behavior, database operation, safety check or package byte changed. A clean local clone without site packages also passed all 114 tests, explaining why the hosted alias was needed to expose this assumption. Verifier evidence files now normalize CRLF once to prevent duplicated carriage returns. Final hosted results remain attached to the corresponding GitHub commit/run; previous failures are preserved in history.

Lease: released after final checks with `uv run atlas lease release nfcraft --agent codex-nfcraft`; Atlas confirmed release. No subagents.
