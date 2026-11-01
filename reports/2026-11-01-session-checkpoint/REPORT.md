# Android 0.5.1 session checkpoint

Date: 2026-11-01, Asia/Tokyo. Desktop 0.2.2; Android 0.5.1 / code 8.
Scope: finish the existing multi-tag/Halloween work, reconcile documentation,
verify the final artifacts and publish the owner-requested GitHub checkpoint.
Branch: `work/android-multi-tag`.

## Delivered state

Android supports exact NTAG213/215/216 profiles with matching CC, UID BCC,
protection checks, model-specific NDEF capacity/page fences and full
target/preserved-tail readback plus unchanged identity/configuration. Factory
NTAG213 Lock Control TLV and existing NDEF placement are preserved. Unknown
models and unexplained ACK framing fail closed. The desktop writer remains
NTAG215-only. No new runtime change was needed during this final checkpoint.

The reviewed IconFlow Halloween card sleeve is present in the editable master,
monochrome source, source-bound receipt, Android adaptive/themed/legacy assets,
local store artwork and design case. Original pocket-card sources are retained
as historical design evidence. Exact generated resources replace the former
manually duplicated VectorDrawable. Scores remain 4/4/4/5/4/5; review is
headless, with the actual contact, target and neighbourhood sheets inspected.
The user owns the icon and outputs, with unrestricted commercial use.

Root README/start page, current state, changelog, test report, backlog,
continuation prompt and store/identity preparation documents now describe
0.5.1, model support and remaining gates consistently. Historical reports are
preserved. Store drafts remain drafts, with public app identity selection held.

## Verification actually run

Environment: native Windows PowerShell, repository Python 3.12.10 venv,
Node 24.18.0, JDK 21, existing Android SDK/Gradle wrapper, IconFlow 0.10.1.

| Exact command / procedure | Result |
|---|---|
| `.venv/Scripts/python.exe scripts/preflight.py` | PASS: expected native toolchain; no reader accessed |
| `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-11-01-checkpoint` | PASS: 118 Python / 16 Worker tests, compilation, JS syntax and isolated demo/CLI/MCP smoke with startup/shutdown |
| From `android`: `gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` | PASS: build successful; 44 existing Android test results, lint 0 errors / 5 warnings; unchanged tasks appropriately cached |
| Git Bash `cd android && tools/parity.sh` | PASS: Python/Java parity, 1,087 plans, ten link fault behaviours, history and 621 model safety assertions |
| `.venv/Scripts/python.exe -m unittest discover -s android/tools -p test_check_release.py` | PASS: five artifact-checker tests |
| `.venv/Scripts/python.exe android/tools/check_release.py --output reports/2026-11-01-session-checkpoint/artifacts.json` | PASS: 0.5.1 / code 8 metadata, archives, permissions, images, test/lint reports; upload signature not verified |
| `iconflow check --config android/iconflow.toml` | PASS: no automated warnings |
| `iconflow ship --config android/iconflow.toml --review android/master-review.json --plan android/work/halloween/evidence/plan` | PASS: approved render plan matched byte for byte; 32 outputs |
| APK SHA-256 vs October 31 installed-artifact record | PASS: unchanged `23e9d10eff2600318408aecd89dde5bc135b3b6e25f72976f027ff4383b70eb2` |
| `adb get-state` | BLOCKED: `no devices/emulators found`; no current phone mutation or UI claim |
| `git diff --check` | PASS |

The IconFlow runner above is the existing toolkit venv interpreter with
`-m iconflow`. No shared toolkit source was modified. The plan command
publishes only reviewed local icon files, not a remote deployment.
Local logs remain under `.local/verification/2026-11-01-checkpoint/` and
`.local/android-2026-11-01-checkpoint.log`. Sanitized artifact metadata is in
[artifacts.json](artifacts.json).

## Phone and data truth

The owner explicitly authorized the October 31 uninstall of differently signed
0.2.0 and fresh installation of 0.5.1. Both succeeded; package manager and exact
installed-APK hash were checked. Old settings were removed, not migrated.
See the [installation report](../2026-10-31-halloween-install/REPORT.md).
At that time the phone was locked; foreground UI was not verified. The phone
is now disconnected. These are distinct observations, not proof of regressions
or a reason to uninstall again. Preserve the installed app/data on reconnect.

No NFC card, database, profile, workspace identity, Windows service, firewall,
cloud resource, key or spending limit was changed. No same-signer data-preserving
upgrade or physical NFC qualification is claimed. APK is debug-signed; AAB is
unsigned. No store upload or public recipient service deployment occurred.

## GitHub checkpoint

The owner explicitly requested documentation/GitHub push at this checkpoint.
The configured repository is owner-controlled and public, and the current
account has ADMIN permission. The outgoing scope is application code/assets,
sanitized evidence and project documentation. Device serials, private UIDs,
phone screenshots/preferences, APKs/AABs, raw logs, local paths and credentials
are excluded. Prior branch history is already present on the existing remote
mobile-history branch. No visibility change or source handoff to a client is
part of this operation.

The existing workflow runs on main pushes, pull requests and explicit dispatch;
checkpoint-branch push alone does not start CI. No main merge, release, tag or
workflow relaxation was performed.

- **PASS — implementation push:** commit
  `7818c6646afbd3c2656d0272a3a908ae629139a3` was pushed to
  `origin/work/android-multi-tag`. `git ls-remote --heads` matched the local
  commit exactly. The commit contains 103 changed paths after rename detection.
- **PASS — hosted checks:** one explicit `gh workflow run ci.yml --ref
  work/android-multi-tag` ran the unchanged existing workflow on that exact code
  revision. [Run 41270588873](https://github.com/snowyukitty/nfcraft/actions/runs/41270588873)
  completed successfully: all four Windows/Linux Python 3.11/3.13 jobs and the
  Android encoder/model job passed. Sanitized results are in
  [github-ci.json](github-ci.json). These are hardware-free hosted checks, not
  physical Android/reader qualification.
- **PASS — publication review:** 105 explicit candidate paths were inspected
  before staging (103 after rename detection); scans found no credential,
  private host path, device identifier or forbidden binary package. Eighty
  local Markdown links resolved before publication. GitHub is public; this
  push is authorized by the owner's explicit request, not inferred from visibility.

The final handoff is a documentation-only follow-up recording these results.
Its remote head is checked after push and reported in the session handoff;
it adds no runtime change beyond the tested code revision above. Main remains
unchanged and no pull request or release is created.

## Start, stop and next bounded task

On the existing phone, reconnect USB debugging, unlock it and open **nfcraft**.
Start with **Inspect only** and check the launcher icon/foreground controls.
Then the owner selects one expendable card and a public test link per model,
explicitly enables writing, and checks rewrite, interruption, preserved memory
and the final URL on a separate recipient phone. No agent-controlled arming
or keyguard bypass is authorized. Close/force-stop the app to stop phone scans.

Desktop demo: `.venv/Scripts/python.exe run.py --no-browser --mode demo`;
for verification use disposable `--data-dir` and `--port 0`. Ctrl+C stops an
interactive run. The process smoke used a temporary workspace and stopped its
child tree. No nfcraft daemon or pending phone UI probe is left running.
ADB's standard server remains available.

APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
AAB: `android/app/build/outputs/bundle/release/app-release.aab`.
Use matching-signature `adb install -r` for future updates. No schema migration
is needed; source rollback does not restore already removed phone settings.

Next work is **physical phone/tag acceptance**, followed by the separately
held public app identity, release signing and store gates. These prerequisites
do not prevent this source checkpoint from being complete and resumable.

Coordination: `codex-root` claimed the nfcraft lease for checkpoint mutation;
no other live nfcraft session was exposed. Release the lease after remote
verification. All pre-existing work in this session is included deliberately;
unrelated workspace resources remain untouched.
