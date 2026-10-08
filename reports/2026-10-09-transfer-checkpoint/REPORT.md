# Portable links and GitHub checkpoint

Date: 2026-10-09 (Asia/Tokyo). Android 0.4.2 / code 6; desktop 0.2.2.
Objective: make the prelaunch application more ready without guessing its
final identity or treating local tests as physical acceptance.

## Changes and data contract

Recent → Transfer links provides a portable list of up to ten saved HTTPS
destinations. Export displays plain text for manual selection/copy and excludes
unsaved current input and NFC identifiers. Import accepts bounded text, validates
every line, deduplicates exact strings and previews the full result. Existing
order is retained and new links append. Capacity overflow is refused rather
than silently evicting saved data. Confirmation saves the list, keeps the current
destination, enables Inspect only and disables unknown-content overwrite.

No package rename, schema migration, automatic clipboard access, network,
third-party SDK, new permission or NFC engine change. Cancelling or recreating
an unconfirmed dialog cannot import. The source of truth stays in existing
private preferences. Android's system text selection handles explicit copying;
the privacy text explains clipboard/keyboard retention and that Clear history
cannot remove external copies. See the platform's
[clipboard privacy guidance](https://developer.android.com/privacy-and-security/risks/secure-clipboard-handling).

Code scope: LinkTransfer, MainActivity, version/resources and two new test
classes. Documentation scope: Android README, privacy draft, physical testing,
root entry points, identity decision, project state, backlog, changelog and
continuation prompt. Existing logo and NFC write planning are unchanged.

## Verification evidence

| Command | Result |
|---|---|
| `.venv/Scripts/python.exe scripts/preflight.py` | PASS |
| `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-10-09-transfer` | PASS: 118 Python / 16 Worker tests, compilation/syntax and isolated demo/CLI/MCP smoke |
| `./gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` from android | PASS: 39 tests, lint 0 errors / 17 warnings, APK/AAB builds |
| Git Bash `bash android/tools/parity.sh` | PASS: encoder parity, 1,087 plan states, 10 link behaviors and history |
| `.venv/Scripts/python.exe -m unittest discover -s android/tools -p test_check_release.py` | PASS: 5 tests |
| `.venv/Scripts/python.exe android/tools/check_release.py --output .local/transfer-artifacts-final.json` | PASS local artifact checks; upload signature not verified |
| `git diff --check` | PASS before checkpoint commit |

New tests exercise hostile/oversized input, exact round-trip, no-loss merge,
preview cancellation, restart, recreation without consent, modal NFC exclusion,
read-only import and export without automatic clipboard changes, on APIs 28/36.
The transfer preview was rendered with Robolectric native graphics and visually
reviewed. `transfer-preview.png` is an engineering render, not a store screenshot.

Initial run: three failures. One exposed trim removing a trailing control
character; production parsing now rejects disallowed controls before trimming.
Two were JSON serialization assertions that incorrectly assumed unescaped
slashes; tests now parse the JSON and compare exact URL values. The final full
run passed. A Gradle version probe from the root directory failed because the
wrapper is under android; all actual Gradle verification used that directory.

Logs remain in `.local/preflight-transfer.log`, `.local/verify-transfer.log`
and `.local/android-transfer-final.log`. `artifacts.json` records final hashes,
permissions, version, test totals and signature limitations without local paths.

## Remaining gates and operation

**NOT_RUN:** real Android/NFC acceptance, physical cross-installation transfer,
same-key phone update, real store screenshots, payments and store upload.
**BLOCKED prerequisites:** final application ID and Console availability,
qualified phone, upload signing, public privacy details/hosting and Play testing.
`app.nfcraft` remains a candidate; the build still uses `best.tgs.cardwriter` as
a legacy test identity. Do not create the public Play record using the old ID.
The APK is a debug build; the AAB is unsigned. Monetization is designed only.

Local APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
Bundle: `android/app/build/outputs/bundle/release/app-release.aab`.
Install only as an explicit test-device action with matching identity/signing;
do not uninstall the old app to bypass a signing mismatch. Open nfcraft and use
Recent → Transfer links for the synthetic rehearsal; close/force-stop to stop.
No permanent tag write is authorized by this report.

Desktop demo: `.venv/Scripts/python.exe run.py --no-browser --mode demo`; use
disposable data and Ctrl+C to stop. The verification command already exercised
an isolated demo child on a dynamic loopback port and stopped it cleanly.

Next bounded task: owner selects the public ID; align namespace/source/tooling,
then use `android/store/TESTING.md` to rehearse old/new installations and exact
link transfer on a chosen phone. Preserve the original installation until that
passes. This implementation alone does not prove physical migration.

## Checkpoint and publication scope

The owner explicitly requested a GitHub push. The existing origin is the owner's
nfcraft repository. Work stays on `work/mobile-history-brand-release`; no merge,
release, visibility change, app upload or public hosting deployment is included.
The only workflow triggers pushes on main, pull requests and manual dispatch;
this branch checkpoint does not request hosted CI. Local evidence is recorded
above. The outgoing diff was checked for credentials and private data.

Repository mutation used the nfcraft lease, released after the push checkpoint.
See the final user-facing handoff for the pushed commit and remote verification.
