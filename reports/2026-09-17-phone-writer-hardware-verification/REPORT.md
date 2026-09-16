# 2026-09-17 — the phone writer meets real hardware

## Objective

`reports/2026-09-16-phone-writer-reliability/REPORT.md` shipped a reliability
fix for the Android card writer but could not run it against a phone: the
machine it was written on had none attached. This session's only job was to
close that gap — build the fixed commit, install it on real devices, and
collect the two pieces of evidence that report left `NOT_RUN`: the `link`
line on a real write, and whether a finished card opens its destination when
tapped outside the app.

No source change was made this session. This is a verification report, not a
development one.

## Starting environment

The build machine had none of the Android toolchain: no JDK, no Android SDK,
no `adb`, and `git`/`xcodebuild` were blocked on an unaccepted Xcode license.
All of that was provisioned before any device work:

- Xcode license accepted (owner-run, requires a real TTY — the harness's own
  shell has none, so this cannot be scripted from here again if it regresses).
- `openjdk@21` and `android-commandlinetools` installed via Homebrew.
- `platform-tools`, `platforms;android-35`, `build-tools;35.0.0` installed via
  `sdkmanager`, licenses accepted.
- `android/local.properties` created locally (gitignored, not committed).
- GitHub auth for `snowyukitty` was already configured (`gh auth status`); no
  action needed there.

## Commit built

```
51f5c18 Mark the check script executable so the documented invocation works
```
`main`, confirmed via `git log --oneline -1`, tree clean.

## Devices

Two phones were updated in turn, one at a time on a single USB port. Serials
and raw card UIDs are omitted here per the reports convention; they are
recoverable from shell history on the build machine if ever needed.

| Device | Model | Prior version | Prior settings (captured before install) |
| --- | --- | --- | --- |
| Phone 1 | P710 | 0.1.0 | url `https://tgs.best`, Inspect Only **on**, Overwrite Unknown **on** |
| Phone 2 | P780 (Rakuten Hand5G) | 0.1.0 | url `https://tgs.best/3d`, Inspect Only **off**, Overwrite Unknown **off** |

Both were on old, pre-fix installs signed with a different key than this
machine's debug keystore, so both hit the documented
`INSTALL_FAILED_UPDATE_INCOMPATIBLE` on the first install attempt, resolved by
uninstalling and reinstalling as the runbook describes.

## Commands run, and what they said

| Result | Command | Evidence |
| --- | --- | --- |
| PASS | `bash android/tools/parity.sh` (`PYTHON=python3`) | encoder parity with `nfcraft/ndef.py`; 1,087 pruned-plan states; 10 link behaviours |
| PASS | `./gradlew assembleDebug` (JDK 21) | `app/build/outputs/apk/debug/app-debug.apk` |
| PASS ×2 | `adb install` after `adb uninstall best.tgs.cardwriter` | both devices report `versionCode=2`, `versionName=0.2.0` after |
| PASS | Settings restored on both devices from the captured values above | confirmed by reading `shared_prefs/card-writer.xml` back after |

The default script calls `python`; this machine only has `python3` on `PATH`.
Not a code defect — noted so the next run doesn't lose time on it.

## What real hardware showed

**The `link` line, live.** On Phone 1, an early inspect-mode tap produced:

```
link   2 retries, 1 reconnect · FAST_READ 16p
```

matching `logcat`'s `NativeNfcTag: Tag lost, restarting polling loop` at the
same timestamp. This is the exact signal the 09-16 fix was built to survive,
observed for the first time against a real wooden card.

**Sustained writes, both devices.** With Inspect Only off:

- Phone 1: 17 consecutive `Written` outcomes, each verified by full readback.
  `logcat` shows 8 `Tag lost` events inside that batch's ~36-second window —
  real coupling loss, mid-session, with every one of the 17 writes still
  landing as `Written`, not `Card moved` or `Write interrupted`.
- Phone 2: the session ran to 50 `CARDS WRITTEN` on the in-app counter, with
  41 `Tag lost` events in the `logcat` buffer overall (including the failures
  below). `Already done` fired correctly on a re-tap of a card whose stored
  destination already matched — the idempotence check working outside a
  simulation for the first time.

**A real, device-specific coupling problem — not a software bug.** Phone 2
repeatedly returned `Card moved` (contact lost before any page write began)
against a card the owner reported was not moving. Nothing in `Tag215.java` or
`MainActivity.java` distinguishes phones; the likely cause is this phone's NFC
antenna sitting in a different spot on the back panel than Phone 1's, so a
card position calibrated on Phone 1 wasn't over Phone 2's coil. Once the
owner found the live spot on Phone 2, writes succeeded repeatedly. This is
exactly the "coupling margin becoming visible instead of silent" the prior
report asked this session to watch for — recorded here as a finding, not
patched, per the constraint against weakening or working around refusals.

**Two false alarms, not software bugs, worth recording so they aren't
re-investigated as regressions:**
- Phone 2 appeared to be "stuck" on `Inspected` for a period. Cause: Inspect
  Only had been toggled back on during testing (by hand, in the UI) — the app
  was doing exactly what that switch says. Not a defect; fixed by toggling it
  back off and confirmed via the prefs file.
- Phone 2 also appeared unresponsive at one point. Cause: the screen was
  locked and the device had never finished its own first-run setup
  (`Finish setting up your Rakuten Hand5G`). Unlocking it was the owner's,
  not something this session could or should do on their behalf.

**Evidence 2 — tapping a finished card outside the app: PASS.** With
`best.tgs.cardwriter` backgrounded (confirmed via
`dumpsys window | grep mCurrentFocus`, not just assumed), tapping the card
brought `com.android.chrome` to the foreground loading
`tgs.best/?lang=ja` — the real destination site, not a placeholder. This was
the largest outstanding gap named in the 09-16 report and it is now closed.

## Open item

Phone 2's destination URL drifted from the captured `https://tgs.best/3d` to
the bare `https://tgs.best` partway through this session (visible on a
write's own receipt: `before https://tgs.best/3d` → `now https://tgs.best`),
most likely from manual editing during testing rather than any app behaviour.
The owner was asked whether to restore `/3d` and has not yet answered; the
field was left as found rather than guessed at. Whoever next has hands on
Phone 2 should confirm which URL that device is supposed to carry before more
cards are cut on it.

## Unresolved prerequisites for next time

- The Xcode license and Homebrew-provisioned toolchain live only on this
  machine, in a user-level, non-scripted state (the license step needs a real
  terminal). A different machine starts from zero again.
- The refusal paths (locked card, protected, foreign content) still have not
  met real hardware — both sessions here wrote to blank or already-owned
  cards only.
- The torn-write resume path is still checks-only; no one has pulled a card
  away mid-write on real hardware yet.
- PC/SC desktop hardware writing remains untouched and unqualified.

## Next bounded task

Confirm Phone 2's intended destination URL with the owner and restore it if
`/3d` was the correct value. Then, on Phone 2 specifically (the device that
showed antenna-position sensitivity), mark and measure its NFC sweet spot
once, so future sessions don't rediscover it by trial and error — a one-line
note in this repo's device notes would do. Separately: deliberately pull a
card away mid-write on real hardware to give `Write interrupted` /
`Not confirmed` their first real-world exercise; both are checks-only today.
