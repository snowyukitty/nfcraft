# 2026-09-29 — mobile history, identity and store preparation

## Objective and decisions

Implement ten reusable web destinations, redesign the mobile app icon and
prepare Apple/Google store distribution. Owner chose **nfcraft** and
**individual developer accounts**. Neither account, Mac nor iPhone is ready;
the owner requested enrollment guidance. No enrollment, payment, identity
submission, key creation, upload, public hosting or physical tag operation ran.

Work is on `work/mobile-history-brand-release`. The initial tree was clean.
Scope: `android/`, changelog, project state, implementation backlog, store
runbook, test report and this report. No sibling project source was edited.
Atlas coordination lease: `nfcraft/mobile-history-brand-release`, released at
handoff. No other team agents were active and no delegated agent work ran.

## Changes and data effects

- Android 0.3.0 remembers ten distinct valid HTTPS URLs. Save link/Done and a
  validated write-mode card operation remember a destination. Picking a saved
  URL fills the input and moves it to the front. Invalid/unfinished input is
  excluded. History is local convenience state, not successful-write evidence.
- A confirmed clear persists an empty list and preserves current input. The
  previous valid destination migrates once when the history key is absent;
  an explicitly cleared list never reimports it at startup. No desktop journal
  or public schema, card UID assignment, encoded URL or slug was changed.
- Capture URL/switches at discovery. Later edits apply to the next card.
  History callbacks from before a clear or after Activity destruction are
  ignored. Existing NFC memory fences, readback and refusal rules are retained.
- Keep `best.tgs.cardwriter` and `card-writer` preferences while changing the
  launcher name to nfcraft. New installs start blank instead of using an
  unrelated preselected domain. Same-key upgrades retain existing input.
- Target/compile API 36, AGP 8.10.1, Gradle wrapper 8.11.1. Optional upload
  signing takes four environment variables; absent credentials yield unsigned
  preparation output. Partial signing configuration is rejected.
- Add scrolling, a local Privacy explanation and matching Save/Recent controls.
  Fix older Android pressed-state fill access and version-qualified bar themes.
- Replace the press logo with a cream sleeve, tilted brass card and forest
  field. Essence: **keep**. Avoided wave fans, bare letters and pen overlays.
  Reviewed 16px through large sizes, adaptive crops, isolated Chromium Review
  Lab, and real Android drawable rendering through Robolectric native graphics.
  Scores: legibility 4, distinctiveness 4, balance 4, color 5, scalability 4,
  craft 4. Native paths match the SVG; legacy density icons, themed/adaptive
  layers and opaque 512/1024 store assets are included. The owner owns the
  artwork with no attribution requirement or commercial restriction.
- Store copy, privacy draft, reviewer/physical acceptance checklist and
  personal-account enrollment guidance are local artifacts. Toolkit evolution
  statistics flagged first-pass axes; no shared-toolkit changes were made.

## Actual checks

Native Windows/PowerShell, repository Python 3.12.10, Node 24.18.0, JDK 21.
SDK platform 36/build-tools 35.0.0 were installed into ignored project-local
`.local/android-sdk` using existing accepted SDK licenses. The global SDK and
JDK were not replaced. Runtime Android dependencies remain platform-only;
JUnit 4.13.2 and Robolectric 4.16.1 are test-only.

| Status | Exact command / action | Evidence |
| --- | --- | --- |
| PASS | `.venv/Scripts/python.exe scripts/preflight.py` | `.local/preflight-2026-09-29.txt`; no reader accessed |
| PASS | `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-09-29-mobile` | 118 Python tests, 16 Worker tests, compilation, JS syntax and daemon/CLI/MCP smoke |
| PASS | `python run.py --mode demo --data-dir <temporary fixture> --port 0 --no-browser` | Executed by the above `scripts/smoke_demo.py`; child launch/status/exit validated; no owner workspace used |
| PASS | `bash android/tools/parity.sh` via Git Bash | Python/Java encoder equality, 1,087 plan states, 10 link behaviors, history policy suite |
| PASS | `android/gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` from `android/` (invoked as `.\gradlew.bat`) | `.local/android-final-checks.log`; 5 Robolectric tests; APK/AAB generated |
| PASS | `.\gradlew.bat testDebugUnitTest --console=plain` | Final visual-proof adjustment: `.local/android-visual-final.log`; 5 tests, zero failures |
| PASS with warnings | `lintDebug` in combined build | 0 errors, 42 warnings; mainly existing resource/localization/layout/tool-version advice. This is not a warning-free app |
| PASS | `iconflow compare`, each finalist `iconflow neighbours`, `iconflow check master.svg --config iconflow.toml`, `iconflow review --config iconflow.toml --out work/identity/review.png --html work/identity/review.html --receipt-template master-review.json` | Ignored `android/work/identity/`; final check has zero warnings |
| PASS | `iconflow ship --config iconflow.toml --review master-review.json`; `android/tools/build-icons.ps1`; `iconflow case lint`; `iconflow case stats` | Source-bound receipt and casebook; 11 toolkit outputs plus platform assets |
| PASS | `.venv/Scripts/python.exe .local/check-mobile-artifacts.py` | Native vector/master geometry; PNG dimensions/opacity; archive integrity; no native `.so`; unsigned AAB |
| PASS | `aapt2 dump badging android/app/build/outputs/apk/debug/app-debug.apk` | Package retained, version 0.3.0/3, target 36, label nfcraft; only NFC/VIBRATE permissions |
| PASS, debug only | `apksigner verify --print-certs android/app/build/outputs/apk/debug/app-debug.apk` | Android Debug signer verified, not release signing |
| PASS, unsigned confirmed | `jarsigner -verify android/app/build/outputs/bundle/release/app-release.aab` | `jar is unsigned.` Expected preparation state, cannot upload as-is |
| PASS | `git diff --check` | No whitespace errors |
| NOT_RUN | Physical phone installation/upgrade, NFC writes and recipient-phone checks | No owner phone/card touched; follow `android/store/TESTING.md` |
| BLOCKED | Store submission / signed release / iOS build | Accounts, owner signing key, public privacy/support details, hardware QA; no iOS source/Mac/iPhone |
| NOT_RUN | Hosted CI, cloud deployment, desktop packaging | No push or external mutations requested/performed |

Initial failures were resolved, not hidden: lint found an existing API-24-only
color getter used on API 21, unqualified system-bar attributes, and SDK path
escaping. Unit-test dependency resolution needed AndroidX enabled for test-only
dependencies. Clear-dialog tests initially asserted before the main-looper
button callbacks ran; the harness now drains that queue. The first full-square
icon failed corner QA; the final source has a rounded field and store exports
are explicitly flattened. No baseline suppression or weakened checks were used.

## Artifacts and operation

- `android/app/build/outputs/apk/debug/app-debug.apk` — 442,052 bytes;
  SHA-256 `e4c9c69ad2dcaa3eae5e76d25473e8a4c2576ed3766bb14e398059987bba37c4`.
- `android/app/build/outputs/bundle/release/app-release.aab` — 409,027 bytes;
  SHA-256 `cace380e9e37cb09a662adc287d96fa7f756e06aec27b3f98a7c1376daf3f801`.
- `android/store/google-play-icon.png`, `app-store-icon.png`; SVG/receipt and
  native Android resources are the editable/rebuildable identity chain.
- `android/app/build/reports/visual/`: actual layout/dialog/adaptive/themed
  raster output from the synthetic Android environment, visually inspected.
  These are not phone screenshots for store submission.
- `docs/STORE-RELEASE.md`; `android/store/listing-draft.md`,
  `privacy-policy-draft.md`, `TESTING.md`.

To install on a selected test phone after confirming its current signing key:
`adb -s <chosen-device> install -r android/app/build/outputs/apk/debug/app-debug.apk`.
This command was **not run**. Do not uninstall to bypass a signature mismatch.
Open **nfcraft** from the launcher. Save link → Recent reuses destinations;
Recent → Clear history deletes the list. Leaving the Activity disables reader
mode; Android force-stop terminates the app if required. No server is needed.

The desktop demo is unchanged. For isolated reproduction, run
`.venv/Scripts/python.exe run.py --no-browser --mode demo --port 0 --data-dir <new temporary path>`;
Ctrl+C stops it. No new fixed port was allocated.

Rollback is source-level before release: the legacy destination and switches
remain, and older builds ignore the added history key. Android versionCode and
signing rules may prevent an in-place downgrade; do not erase app data to make
one succeed. Clearing history is intentionally local and cannot erase a tag.

## Next bounded work

Owner: begin Google Personal account enrollment using the linked official guide,
complete identity/payment privately and report the resulting status. Prepare
real Android testers. Engineering: physical 0.3.0 acceptance, signing setup and
reviewed public support/privacy pages, then internal/closed testing. Apple work
starts with Mac/iPhone access and a read-only Core NFC qualification prototype;
membership payment alone does not produce an iOS app.
