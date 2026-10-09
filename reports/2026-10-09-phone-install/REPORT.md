# Phone installation and final session checkpoint

Date: 2026-10-09. Scope: authorized phone installation, sanitized evidence and
documentation/GitHub checkpoint. Application source and built artifacts unchanged.

## Result and authorization

The owner requested installation of the available Android 0.4.2 test APK.
The connected phone initially had 0.2.0 / code 2 under `best.tgs.cardwriter`.
An in-place install was refused by Android for mismatching signatures. The
old version was confirmed still installed; no uninstall was attempted until
the owner explicitly requested clearing the old version and installing the new
one. After that authorization, uninstall and fresh install both succeeded.

Package manager confirmed `versionName=0.4.2`, `versionCode=6`, `minSdk=21`,
`targetSdk=36`. The version and local APK hash were rechecked during this final
checkpoint. Device serial and unrelated device information are omitted.

## Exact operation evidence (device selector redacted)

Commands used the repository's `.local/android-sdk/platform-tools/adb.exe`.
`<device>` below stands for the one selected, authorized test phone.

| Command | Result |
|---|---|
| `adb -s <device> shell dumpsys package best.tgs.cardwriter` (version fields only) | Initially 0.2.0 / code 2 |
| `adb -s <device> install -r android/app/build/outputs/apk/debug/app-debug.apk` | FAIL: INSTALL_FAILED_UPDATE_INCOMPATIBLE; signatures do not match |
| Same package inspection after refusal | Original 0.2.0 / code 2 remained |
| `adb -s <device> uninstall best.tgs.cardwriter` after explicit owner approval | PASS: Success |
| `adb -s <device> install android/app/build/outputs/apk/debug/app-debug.apk` | PASS: Success |
| Same package inspection after installation and at checkpoint | PASS: 0.4.2 / code 6 |
| `Get-FileHash -LiteralPath android/app/build/outputs/apk/debug/app-debug.apk -Algorithm SHA256` | Matches the prior tested artifact below |

APK SHA-256:
`8e3acb52a3b0602111dd8d6545da132803a161bff126bfbf3227306fcd5b026b`.
This is the debug APK from the [transfer checkpoint](../2026-10-09-transfer-checkpoint/REPORT.md).
Its 39 Android, 118 Python, 16 Worker and 5 release-tool test results remain
historical evidence for the unchanged source/artifact. Those suites were not
rerun for this documentation-only checkpoint. `git diff --check` passed.

## Data effects and limits

The authorized uninstall removed the old app's local destination/settings/history.
No backup, restore or preserved-data migration is claimed. There is no rollback
for those removed settings documented here. No NFC card was changed by these
installation commands. The newly installed app remains the legacy-ID test build.

**NOT_RUN:** opening/interacting with the installed UI, real NFC read/write,
recipient-phone scan, cross-installation link transfer, same-key preserved-data
update, production signing, store upload or purchase flow.
**Pending:** final public application ID, Play availability, release signing,
public privacy details and physical acceptance. Installation success alone does
not close any NFC or store-readiness gate.

## Resume and stop

The owner can open nfcraft from the phone launcher, add disposable HTTPS links
and check Recent → Transfer links. Use Inspect only for read-only NFC checks;
permanent card writes still require a separate explicit operator decision.
Close or force-stop the app to stop. No app launch or background helper was
started by this checkpoint.

Next bounded task: run UI/history/transfer acceptance on the installed 0.4.2,
then plan owner-approved NFC tests. Preserve this installation for future
same-key updates. For 0.2.0 migration tests, use disposable fixtures instead of
assuming the removed owner installation still exists. Decide the public ID
before creating a Play record.

## Git handoff

Updated project state, changelog, test report, backlog, physical testing checklist
and continuation prompt. Work remains on `work/mobile-history-brand-release`.
The owner explicitly requested pushing this checkpoint. Outgoing changes contain
no device serial, credentials or private app content. No main merge, release,
store upload or visibility change is included; branch push does not trigger the
current main-only push workflow. The nfcraft coordination lease is released at
completion. Final response records the remotely verified commit.
