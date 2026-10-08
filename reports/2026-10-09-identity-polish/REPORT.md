# Android identity review and prelaunch polish

Date: 2026-10-09 (Asia/Tokyo). Android 0.4.1 / code 5; desktop 0.2.2.
Scope: local repository changes and synthetic verification only.

## Outcome

The legacy `best.tgs.cardwriter` identity originated in prototype commit
`d9634d1`, alongside the `https://tgs.best` default destination. It is not an
NFC requirement. The owner's broader product positioning warrants a separate
identity decision. `app.nfcraft` is proposed, not selected or checked available.
Play app creation is on hold. This build keeps the legacy ID for testing only.

Native View handling now decides whether a gesture clicks. Previously the
decorative listener called performClick on every pointer-up, including after
dragging outside a control. Tests cover valid tap, drag-out, cancellation,
orphan pointer-up, disabled controls, accessibility clicks and the real
Inspect only control.

Visual changes add the nfcraft workshop header, forest-green primary action,
lighter borders/shadows, neutral unavailable-NFC styling and conditional
receipt/session details. The existing logo is unchanged. Destination and
large-text-scrolled engineering renders were visually inspected. The attached
preview is a synthetic engineering render, not a store or phone screenshot.

## Verification

Commands run from the repository root unless specified:

| Command | Result |
|---|---|
| `.venv/Scripts/python.exe scripts/preflight.py` | PASS |
| `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-10-09-polish` | PASS: 118 Python tests, 16 Worker tests, compilation/syntax and isolated demo/CLI/MCP smoke |
| `./gradlew.bat testDebugUnitTest --tests '*PressInteractionTest*' --console=plain` (android directory) | PASS after correcting queued-click test synchronization |
| `./gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` (android directory) | PASS: 29 Android tests; lint 0 errors / 17 warnings; APK and AAB built |
| `bash android/tools/parity.sh` (Git Bash) | PASS: encoder parity, 1,087 plan states, 10 link behaviors, history |
| `.venv/Scripts/python.exe android/tools/check_release.py --output .local/release-check-2026-10-09.json` | PASS local artifacts; upload signature not verified |

The initial gesture test run failed because native View posts the click to the
main looper. The fixture now drains that looper after dispatch; production code
retains native handling. The final full suite passed. Layout tests exercise
four screen geometries, three font scales (up to 200%) and two APIs (28/36):
24 scenarios with control height, text-fit and horizontal-overflow assertions.
These are Robolectric checks, not physical-device acceptance.

The verification runner starts `python run.py --mode demo --data-dir <temp>
--port 0 --no-browser` in an isolated child and shuts it down. No owner workspace
or physical tag was used. Logs remain under `.local/`; sanitized artifact
metadata is in `artifacts.json` beside this report.

**NOT_RUN:** physical NFC, same-key phone update, new-ID link transfer,
real store screenshots, purchase transactions and store upload.
**BLOCKED prerequisites:** final ID/Console availability, upload signing,
privacy hosting and Play testing access. The release AAB is unsigned.

## Operation, data and next task

Android test APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
Release bundle: `android/app/build/outputs/bundle/release/app-release.aab`.
Do not upload this legacy-ID test build. After choosing a test device, launch
nfcraft normally and leave Inspect only enabled for read-only checks; close
the Activity or force-stop to stop. No physical write is authorized by this
report. Local desktop demo remains `.venv/Scripts/python.exe run.py
--no-browser --mode demo`; stop with Ctrl+C. Use disposable demo data for QA.

No migration occurred: application ID and existing preference storage remain
unchanged; card destinations and deterministic NFC write planning are untouched.
A new ID would create separate app storage. Preserve the old installation and
provide an explicit, tested recent-link transfer before switching IDs.

Next bounded task: confirm the ID and existing Console record state; implement
coherent namespace/tooling changes and synthetic transfer tests, then perform
side-by-side installation and real NFC acceptance on the chosen phone. Public
support remains `dokoii@proton.me`. Monetization remains a design proposal.

Work was performed on `work/mobile-history-brand-release` under the nfcraft
Atlas lease for codex-root. No push, publication, account change or paid service
was performed.
