# Android multi-model link rewriting and phone installation diagnosis

Date: 2026-10-31, Asia/Tokyo. Android 0.5.0 / code 7; desktop 0.2.2.
Branch: `work/android-multi-tag`. Initial worktree was clean.

## Outcome and scope

Implemented Android NTAG213/215/216 link rewriting with exact GET_VERSION
profiles, factory CC checks, per-model lock/configuration reads and write
fences, capacity refusal and unchanged full-area readback requirements.
UID BCC bytes are checked; uninspected or unsafe cards cannot reach NDEF
read/write. Unexplained ACK framing is refused instead of masking off bits.

NTAG213's five-byte factory Lock Control TLV is recognised and preserved.
The NDEF length lives in page 05 for this layout. Existing page-04 layouts
stay in place, so rewriting never changes the position of an advertised
message while its body is being updated. Length is hidden before body writes
and committed last. Tail bytes and protected memory are compared/preserved.
NTAG216's final partial READ chunk remains inside its advertised area.

Profile/page/capacity contract and datasheet references:
[ANDROID-TAGS.md](../../docs/ANDROID-TAGS.md). The Python/PCSC writer remains
NTAG215-only. No database, package identity, permission, SDK or cloud change.

Files: Android `Tag215.java` becomes `Tag21x.java`; new `TagProfile.java`,
`TagProfileTest.java` and desktop-JVM `ProfileTest.java`; encoder, Activity,
guide/resources, Gradle version and parity/link harness updated. Project state,
agent write contract, backlog, changelog, Android guide/testing and continuation
instructions are updated. Historical reports and delivery evidence are intact.

## Verification actually run

Environment: Windows PowerShell, Python 3.12.10 in the existing repository
venv, JDK 21, Node 24.18.0, existing Android SDK and Gradle wrapper.

| Exact command / procedure | Result |
|---|---|
| `.venv/Scripts/python.exe scripts/preflight.py` | PASS; native Windows, Python/Node present, no reader accessed |
| `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-10-31` | PASS: 118 Python / 16 Worker tests, compilation, JS syntax and disposable demo/CLI/MCP smoke |
| Git Bash, from repository root: `cd android && tools/parity.sh` | PASS: legacy encoder parity, 1,087 plan states, ten faulty-link behaviours, history and 621 multi-model assertions |
| From `android`: `gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` | PASS: 44 JVM/Robolectric tests; lint 0 errors / 17 warnings; APK/AAB |
| `.venv/Scripts/python.exe -m unittest discover -s android/tools -p test_check_release.py` | PASS: five release-checker tests |
| `.venv/Scripts/python.exe android/tools/check_release.py --output reports/2026-10-31-android-multi-tag/artifacts.json` | PASS; 0.5.0 / code 7; only NFC/VIBRATE permissions; debug APK and unsigned AAB |
| `.venv/Scripts/python.exe run.py --no-browser --mode demo --data-dir <disposable-temp> --port 0` | PASS: child starts with runtime file; process tree stopped and temporary data removed; no operator token printed or used |
| `git diff --check` | PASS |
| Robolectric `destination.png` visual inspection | PASS for changed model footnote; synthetic UI, not a phone screenshot |

Simulator covers all three model fences, exact CC, BCC and protection refusals,
unknown-version refusal before memory reads, bounded plain-READ fallback,
full target/tail comparison, unchanged protected memory, capacity boundaries,
every interrupted prefix and malformed ACK refusal. JVM tests additionally
cover exact model vectors, known/unknown layouts, hiding the correct length
before body changes and preserving legacy NTAG215 bytes/plans.

Early test corrections: boundary fixture initially added one excess URL byte;
the protection fixture initially toggled an unused configuration bit rather
than mirroring. Both were corrected. One inserted Java middle-dot character
used the Windows default encoding; it was replaced with a Java Unicode escape
and source files were UTF-8 checked. The final complete Gradle run has no
compilation error. Local logs: `.local/android-2026-10-31-final.log` and
`.local/verification/2026-10-31/`; earlier runs are retained separately.

## Phone diagnosis and installation gate

ADB sees one authorized NFC-capable Android 11 / API 30 phone. NFC reports on.
Package-manager inspection of `best.tgs.cardwriter` reports **0.2.0 / code 2**,
which differs from the historical October 9 clean-install checkpoint. The
installed APK was pulled read-only to ignored local storage and public signing
certificate fingerprints were compared with `apksigner verify --print-certs`.
The signers differ. No preferences, private URL history, UID or unrelated
device files were inspected.

`adb install -r android/app/build/outputs/apk/debug/app-debug.apk` returned:

```text
INSTALL_FAILED_UPDATE_INCOMPATIBLE:
Package best.tgs.cardwriter signatures do not match previously installed version
```

**FAIL:** in-place installation, correctly blocked by Android signing policy.
Package manager was rechecked: original 0.2.0 / code 2 remains.
**BLOCKED:** fresh installation pending explicit owner authorization to remove
this device's old app and its destination/settings. The existing Android README
prohibits uninstalling to bypass a signing mismatch without that authorization.
The owner was asked after the verified APK was ready. No uninstall, app-data
clear, signer change or signing-key access was attempted. Earlier permission
for a historical device/checkpoint is not assumed to cover this removal.

**NOT_RUN:** new app launch/UI on this phone, physical NTAG213/215/216 writes,
physical interruption/recovery, recipient-phone scan, preserved-data upgrade,
release signing, store upload or remote deployment. Installation alone would
not pass any physical NFC gate.

## Artifacts, data and operation

Artifact hashes/metadata are in [artifacts.json](artifacts.json).
APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
AAB: `android/app/build/outputs/bundle/release/app-release.aab` (unsigned).
The existing installed APK is retained in ignored local evidence for diagnosis;
it contains app code, not a backup of settings. No source was disclosed or
artifact uploaded outside the workspace/device installation attempt.

No SQLite/schema migration or card mutation occurred. App ID/preferences stay
compatible with a same-signer update; removing an existing differently signed
app would delete its private data. Do not run uninstall or clear commands until
the owner explicitly authorizes that exact data loss. Repository rollback can
restore code but cannot undo future physical card writes or app-data deletion.

After authorized installation, open nfcraft from the launcher and turn on
Inspect only before presenting any card. Start with one owned expendable card
per profile and record sanitized results. Writing remains an explicit owner
action in the app. Close/force-stop `best.tgs.cardwriter` to stop NFC activity.
Desktop demo starts with the command above; use Ctrl+C to stop an interactive
run. No nfcraft daemon or phone app was left running by this session. The standard
ADB server was started for device access and remains available.

Next bounded task: resolve the installation/data decision, install the tested
APK, verify startup/settings and Inspect only, then perform owner-operated
read/write/recipient-phone acceptance per model. Keep unsupported card families
and desktop geometry outside this increment.

Coordination: nfcraft lease held by `codex-root` during repository mutation;
release at handoff. No other live project agent was exposed by the session tools.
No commit, push, release or cloud mutation was performed.
