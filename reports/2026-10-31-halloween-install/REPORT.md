# Halloween IconFlow identity and authorized Android reinstall

Date: 2026-10-31, Asia/Tokyo. Android **0.5.1 / code 8**; desktop 0.2.2.
Branch: `work/android-multi-tag`. The preceding multi-model changes were already
present and are preserved. This report supersedes their phone-install blocker;
it does not overwrite the earlier evidence.

## Owner decision and delivered result

The owner explicitly instructed removal of the old phone app, creation of a
high-quality Halloween icon using IconFlow, and installation of the new app.
The tested replacement was prepared before removal. Uninstall of 0.2.0 and
installation of 0.5.1 both returned `Success`. Package manager reports
`versionName=0.5.1`, `versionCode=8`, `minSdk=21`, `targetSdk=36`.
The installed base APK was pulled read-only into ignored local evidence; its
SHA-256 exactly equals the tested build:

`23e9d10eff2600318408aecd89dde5bc135b3b6e25f72976f027ff4383b70eb2`.

This is a **clean install with explicitly authorized old-data removal**.
The former app's destinations/settings were removed, not migrated or restored.
No NFC card was changed. Keep this new installation for subsequent matching-key
updates; do not repeat the uninstall merely because the request mentioned it twice.

## Design and generated assets

Essence: **keep**. The functional object is the reusable-card sleeve: pumpkin
orange, broad carved eyes, a bat-wing thumb cut, and a tilted cream card where
a lantern's stem would be. The established forest background and paper tone
keep it connected to the pocket NFC workshop. The face belongs to the sleeve,
rather than being an unrelated pumpkin placed on a generic NFC badge.

Four concept directions were explored. Three vector finalists were compared
with a device-free sleeve and the inherited icon. The ghost-card looked like
chat; the bat-cut document lost the sleeve/reuse story. Widening the winning
draft's 96-unit eye cuts to 128-unit height and 160-unit minimum width kept
two deliberate cuts at native 16px. The smaller grin remains subordinate.
NFC wave fans, initials, generic pumpkin emoji and tiny holiday props were
deliberately avoided.

IconFlow 0.10.1 doctor, audit, source-bound review, neighbourhood check and
ship all passed. The final six scores are **4 / 4 / 4 / 5 / 4 / 5**:
legibility, distinctiveness, balance, color, scalability and craft. The
contact sheet, foreground bake-off, neighbourhood proofs and exact Android
circle/squircle/themed/legacy target sheet were actually inspected. The generated
native Android adaptive/themed test renders and rebuilt feature graphic were
also inspected. This is a headless evidence review; no interactive Lab or
independent review is claimed.

Current source: `android/master.svg`, alpha-only `android/monochrome.svg`,
`android/iconflow.toml`, `android/master-review.json`. The superseded
master/receipt/configuration/native vector are preserved under
`android/history/2026-09-29-pocket-card/`. The new design case is
`android/casebook/2026-10-31-nfcraft-halloween-pocket.md`.

`android/tools/build-icons.ps1` now copies the exact reviewed IconFlow Android
target resources, including API-33 overrides. This replaces the old manually
duplicated VectorDrawable. Generated resources include five densities of
legacy square/round icons, adaptive foreground, monochrome layer and adaptive
XML/background. Web previews and opaque 512/1024 store icons are updated;
the existing feature-graphic generator was rerun with all three NTAG model
names. Google Play icon alpha was checked: every pixel is fully opaque.
The output tree is **32 IconFlow files**, plus the local store artwork.

Preview: [icon-preview.png](icon-preview.png).
Reviewed platform contexts: [icon-targets.png](icon-targets.png).
The user owns the icon and outputs, with no attribution or commercial-use
restriction. No artwork was uploaded or published.

## Verification actually run

All commands were run from the repository root except IconFlow and Gradle
commands, which used `android/`. `iconflow` below means the installed toolkit
venv interpreter with `-m iconflow`; the shared toolkit was not edited.

| Command / check | Result |
|---|---|
| `iconflow --version`, `doctor`, `case stats`, exported/read design references | PASS: 0.10.1, renderer ready |
| `iconflow compare <three-finalists> <plain-control> <inherited> --out work/halloween/bake.png` plus foreground/refinement sheets | PASS: inspected; refined eyes after first bake |
| `iconflow neighbours <each-finalist> --config iconflow.toml --sheet <proof>` | PASS: no avoid-set collision; proofs inspected |
| `iconflow check --config iconflow.toml` | PASS: no automated warnings |
| `iconflow review --config iconflow.toml --evidence work/halloween/evidence` | PASS: contact, neighbourhood and exact-target sheets inspected |
| `iconflow score --config iconflow.toml --evidence work/halloween/evidence --scores 'legibility=4 distinctiveness=4 balance=4 color=5 scalability=4 craft=5'` with six sheet-specific rationales | PASS: source-bound ready receipt |
| `iconflow ship --config iconflow.toml --review master-review.json` | PASS: 32 reviewed outputs; plan matched byte for byte |
| `iconflow case new ...`, `case lint`, `case stats` | PASS: case recorded; clean casebook |
| `android/tools/build-icons.ps1 -IconFlowPython <toolkit-venv-python>` | PASS: generated Android resources copied into app |
| `.venv/Scripts/python.exe android/tools/build_store_assets.py` | PASS: rebuilt local feature graphic |
| `.venv/Scripts/python.exe scripts/preflight.py` | PASS: native Windows/Python/Node |
| `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-10-31-halloween` | PASS: 118 Python / 16 Worker tests, compile, syntax, disposable demo/CLI/MCP startup and shutdown |
| Git Bash `cd android && tools/parity.sh` | PASS: encoder parity, 1,087 plans, ten faulty-link behaviours, history, 621 model safety assertions |
| `gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` | PASS: 44 Android tests; lint 0 errors / 5 warnings; APK/AAB |
| `.venv/Scripts/python.exe -m unittest discover -s android/tools -p test_check_release.py` | PASS: five checker tests |
| `.venv/Scripts/python.exe android/tools/check_release.py --output reports/2026-10-31-halloween-install/artifacts.json` | PASS: version, permissions, archives, dimensions, tests/lint; upload signature not verified |
| `adb uninstall best.tgs.cardwriter`, then `adb install android/app/build/outputs/apk/debug/app-debug.apk` | PASS: Success / Success, after this turn's explicit owner authorization |
| `adb shell dumpsys package best.tgs.cardwriter` (version fields only) | PASS: 0.5.1 / code 8 |
| Read-only pull of installed base APK and SHA-256 comparison | PASS: exact tested APK, including new icon resources |
| `adb shell am start -W -n best.tgs.cardwriter/.MainActivity` | BLOCKED: process created, but Activity stays stopped behind keyguard; waiting launch probe was cancelled |
| App-only PID / `logcat -d --pid=<app-pid> -s AndroidRuntime:E` | PASS for process presence and no crash output; not foreground acceptance |
| `adb shell dumpsys window policy`, `dumpsys power` (lock/wake fields only) | Phone awake, keyguard still showing; owner unlock requested |
| `git diff --check` | PASS |

Case stats reports scalability as the weakest first-pass axis and a distillation
signal. This is recorded for the toolkit owner; shared-toolkit edits are outside
this task. No gate was weakened to accommodate that signal.

Logs remain local in `.local/android-2026-10-31-halloween.log` and
`.local/verification/2026-10-31-halloween/`. [artifacts.json](artifacts.json)
records hashes and exact local artifact/check totals without device identifiers.
No new hardware engine behavior was introduced after the preceding verified
multi-model increment.

## Phone UI boundary and remaining evidence

NFC is enabled, but the phone is keyguard-locked. The app process exists and
the Activity is stopped, so UI acceptance and setting Inspect only are
**BLOCKED pending the owner unlocking the phone and opening nfcraft**. The
owner was prompted. Only a wake event was sent; no unlock bypass, PIN,
credential, operator capability or card-write permission was obtained.
The waiting ADB launch probe was stopped; it will not later dump an unrelated
screen. No phone screenshot or private preference dump was captured.

**NOT_RUN:** actual launcher appearance/foreground controls on this phone,
physical NTAG213/215/216 rewrite, interruption/recovery, independent recipient
scan, preserved-data upgrade, release signing, Play upload or cloud deployment.
The APK is debug-signed and the release AAB remains unsigned. The local
application ID remains the existing test identity; no public ID was selected.

## Run, stop, migration and continuation

Open **nfcraft** from the phone launcher after unlocking. Enable **Inspect only**
before presenting a card; the destination starts empty after the clean install.
Then the owner selects the expendable card/link and enables writing explicitly
in the app when ready. Close or force-stop `best.tgs.cardwriter` to stop NFC
activity. ADB remains available; no desktop nfcraft daemon is running.

Rebuild assets with the script above, then Gradle and the artifact checker.
APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
AAB: `android/app/build/outputs/bundle/release/app-release.aab` (unsigned).
Future same-signer updates should use `adb install -r` and preserve app data.
No SQLite schema, package identity or desktop data migration was performed.
Source rollback cannot restore the old preferences already removed by the
explicitly authorized uninstall. No tag write needs rollback because none ran.

Next bounded task: owner unlocks/opens the installed app; verify its UI, new
launcher icon and Inspect only, then perform owner-operated one-card physical
qualification per model and recipient-phone QA.

Scope includes the Android icon sources/resources/build integration, version,
local store graphic and project status/changelog/backlog/continuation docs.
Prior multi-model work remains in the same branch. No commit, push, release,
store publication or cross-project source edit was performed. The nfcraft lease
was held by `codex-root` for mutation and is released at handoff.
