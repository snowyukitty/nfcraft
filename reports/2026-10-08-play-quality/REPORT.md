# Android 0.4.0: free-release quality and Play preparation

Date: 2026-10-08, Asia/Tokyo. Branch: `work/mobile-history-brand-release`.
Starting tree was clean at `425cb50`; previous mobile work was already committed.
Scope: `android/`, related state/release documentation, this sanitized report.
No desktop journal, NFC card, remote account or published site was mutated.

## Owner decisions and milestone

- nfcraft is free to download; voluntary income methods are desired.
- Owner reports Google Personal developer account verification complete and
  Create app available. App-record creation, merchant setup and upload are not
  verified by the agent.
- Public support address explicitly approved: **dokoii@proton.me**. The Google
  login address is not reused in public materials.
- Public developer identity, merchant country, distribution/audience selections,
  phone model, upload signing and public policy URL remain unresolved.

This milestone is a locally validated Android preparation build and concrete
store/revenue design. It is not a signed, hardware-qualified or submitted release.

## Product and safety changes

Android version is 0.4.0 / code 4, retaining `best.tgs.cardwriter`, minSdk 21,
target API 36 and `card-writer` preferences.

- Browser text sharing accepts one bounded valid HTTPS URL. Cancel preserves
  input; confirmation saves it and enables Inspect only. Paragraphs, multiple
  links, credentials, fragments, HTTP and overlong input are rejected. Pending
  consent survives recreation, accepted imports do not replay.
- `ScanGate` serializes foreground/modal admission and excludes concurrent
  operations across Activity instances. Dialogs never start on top of an
  admitted NFC operation. Backgrounding does not interrupt a page write already
  in progress; it prevents new operations. Destroyed screens ignore posted UI
  results. NFC byte/page safety and readback logic are unchanged.
- Unknown-content overwrite now requires explanation/confirmation and resets
  on background/restart. The old persisted permission is deliberately removed.
- Quick guide explains choosing, inspecting, writing, independent recipient
  checks and uncertainty. NFC-off state offers Settings. Email support opens an
  unsent composer and automatically attaches no URLs, tag data or screenshots.
- Switch accessibility state, keyboard focus, stronger text/dialog contrast,
  larger captions and stacked mode controls improve small/large-text layouts.
- `Locale.ROOT` fixes rejection of uppercase ASCII hostnames in Turkish locales
  without changing payload bytes. Android 12+ extraction rules exclude all
  application data domains from cloud backup and device transfer; older full
  backup is disabled too. OEM transfer behavior still requires physical QA.

## Store and income preparation

- `android/store/feature-graphic.png`: 1024 x 500 opaque RGB; existing reviewed
  icon plus bundled OFL fonts. Rebuilt by `android/tools/build_store_assets.py`;
  this is editorial artwork, not a changed launcher icon or fabricated phone UI.
- `android/store/play-console-guide.md`: Create app values, current-binary
  declarations, Data safety rationale, reviewer instructions and test sequence.
- Store description, privacy draft and physical acceptance checklist updated.
  Policy remains a draft until developer identity, support handling and hosting
  are finalized; approving an email address did not publish anything.
- `docs/MONETIZATION.md`: policy-backed recommendation for an optional one-time
  Workshop finishes pack, then demand-tested label tools/physical craft kits.
  Concrete copy, entitlement states, compatibility decisions and transaction
  acceptance are specified. Billing/checkout/donation links are **not implemented**.
  Core work remains free and offline; no ad/billing/analytics SDK was added.
- `check_release.py` validates artifacts, metadata/permissions, image dimensions,
  test/lint reports and optional expected-certificate verification. It never
  uploads or treats local tests as physical acceptance. Existing reports alone
  cannot prove source freshness; run it immediately after a rebuild.

## Actual evidence

Environment: native Windows 11 / PowerShell, repository Python 3.12.10,
Node 24.18.0, existing JDK 21 and project-local Android SDK. Pillow 12.3.0 was
already available for editorial rendering. No new paid service/toolchain was installed.

| Status | Exact command or check | Result / evidence |
| --- | --- | --- |
| PASS | `.venv/Scripts/python.exe scripts/preflight.py` | `.local/preflight-2026-10-08.log`; no reader accessed |
| PASS | `.venv/Scripts/python.exe scripts/verify.py --require-node --output .local/verification/2026-10-08-play` | 118 Python / 16 Worker tests; compilation, JS checks, isolated daemon/CLI/MCP smoke |
| PASS | `python run.py --mode demo --data-dir <temporary fixture> --port 0 --no-browser` | Child launch/check/stop exercised by the above demo smoke; no owner data |
| PASS | Git Bash `bash android/tools/parity.sh` | Encoder parity; 1,087 plan states; 10 link behaviors; recent-history suite |
| PASS | From `android/`: `.\gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease --console=plain` | `.local/android-2026-10-08-final.log`; 23 tests, APK/AAB built; 0 lint errors / 17 warnings |
| PASS | `.venv/Scripts/python.exe -m unittest discover -s android/tools -p test_check_release.py -v` | 5 tooling regressions: unsigned zero-exit, wrong fingerprint, hash shape, truncated PNG, empty bundle |
| PASS | `.venv/Scripts/python.exe android/tools/build_store_assets.py` | RGB banner generated; dimensions and visual review pass |
| PASS | `.venv/Scripts/python.exe android/tools/check_release.py --output reports/2026-10-08-play-quality/artifacts.json` | Bound artifact hashes, compiled metadata, NFC/VIBRATE-only permission scope, images and unit/lint results |
| PASS | `check_release.py --require-signed --upload-certificate-sha256 <synthetic 64-hex fingerprint>` | Expected refusal, exit 1, because AAB is unsigned; `.local/release-unsigned-refusal-2026-10-08.json` |
| PASS | `apksigner verify --print-certs android/app/build/outputs/apk/debug/app-debug.apk` | Debug certificate verified; not an upload certificate |
| PASS | `jarsigner -verify android/app/build/outputs/bundle/release/app-release.aab` | Output explicitly `jar is unsigned.`; not upload-ready |
| PASS | Synthetic Android visual review | `android/app/build/reports/visual/`: destination, history, share, guide and 320dp/160%-text scrolled layout; engineering evidence only |
| PASS | `git diff --check` and final source review | No whitespace errors, secrets or unintended external-action changes found in session diff |
| NOT_RUN | Physical Android, same-key upgrade, NFC writes, recipient phones, real screenshots | Read-only `adb devices -l` found no attached device; no phone/card operation attempted |
| NOT_RUN | Play Billing transactions | No payment integration or configured product; revenue design only |
| BLOCKED | Signed upload, policy publication, Play testing/production access | Owner/account/hosting/signing and hardware gates above |
| NOT_RUN | Store upload, cloud deployment, Apple build, hosted CI, desktop repackaging | No such actions performed |

Remaining lint warnings are mainly existing icon shape/duplicate/versioned
monochrome suggestions, the intentional NFC hardware requirement, button style,
layout weighting and tool-version advice. No lint baseline or suppression was
added. There are no native `.so` files in either package.

Failures found and fixed: initial visual QA showed an overwrite label clipped
at 160% text despite tests passing; the layout now stacks and its regression
checks the complete label. A new artifact guard initially expected `sdkVersion`
instead of aapt2's `minSdkVersion`, producing a real checker FAIL. The compiled
manifest was inspected, the parser was corrected and the check rerun to PASS.

## Artifacts and operation

Exact SHA-256/size evidence is in [artifacts.json](artifacts.json).

- `android/app/build/outputs/apk/debug/app-debug.apk`: local debug build.
- `android/app/build/outputs/bundle/release/app-release.aab`: unsigned preparation.
- `android/store/google-play-icon.png`, `feature-graphic.png`: prepared artwork.
- No private signing material, production UID or private destination is in the
  report, artwork or store copy.

On an explicitly selected test phone with compatible signing, install using
`adb -s <selected-device> install -r android/app/build/outputs/apk/debug/app-debug.apk`.
This command was **not run**. Do not uninstall an existing app to bypass a key
mismatch. Open nfcraft; use Quick guide and Inspect only before a separately
approved expendable-card test. Home/Back disables new scan admission; force-stop
closes the app. No local/public server is needed.

The unchanged desktop demo can be reproduced with
`.venv/Scripts/python.exe run.py --no-browser --mode demo --port 0 --data-dir <new temporary path>`;
Ctrl+C stops it. No fixed port was allocated.

## Migration and continuation

Destination, recent history and Inspect only preferences survive same-key
updates. Persisted unknown-overwrite permission is intentionally removed and
never restored. No journal schema or public URL changes. Backup/device-copy
exclusion means users should not expect history restoration on a replacement
phone. Rollback cannot safely be simulated by uninstalling or resetting data;
use disposable devices/fixtures and respect Android version/signature rules.

Next bounded milestone: owner creates the free Play app record, supplies public
developer identity and merchant country, and selects an NFC test phone. Finalize
the privacy/support page for an approved hosting target, prepare the backed-up
upload key privately, run physical acceptance, then review the concrete signed
bundle and listing before internal upload. Closed-test recruitment can begin
once that build is usable; monetary features follow their separate activation
gates. Apple still requires an actual iOS implementation and Mac/iPhone access.

Coordination: Atlas `nfcraft` lease held by `codex-root` for this session, to be
released at completion. No subagent or independent review was claimed. Local
checkpoint only; no push, release tag, purchase, account mutation or publication.
