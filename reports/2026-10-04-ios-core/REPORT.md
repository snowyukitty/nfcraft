# 2026-10-04 — iPhone writer core (NfcraftKit)

## Objective

Resolve the highest-value iOS uncertainty that can be resolved without a Mac,
iPhone or card, and leave the iPhone writer one adapter away from a device
spike. Requested from the apple-app-store-research workspace; branch
`work/ios-core`, built in an isolated worktree so the owner's checkout on
`work/mobile-history-brand-release` (clean at 425cb50) was not touched.

## Starting point

- Desktop 0.2.2 / Android 0.3.0; no iOS code. `docs/STORE-RELEASE.md` already
  chose native Swift/Core NFC with the same encoder vectors and
  safety/readback contract, and warned that a generic NDEF writer is no
  substitute.
- Windows 11, Python 3.12.10, JDK 21.0.11, Docker 29.6.2. No native Swift, no
  Mac, no iPhone, no tag.

## What changed

New `ios/` tree; nothing else in the app changed apart from `.gitignore`.

- `ios/NfcraftKit` — Swift package with no Core NFC/UIKit imports: ports of
  `Ndef.java`, `Tag215.java`, `RecentUrls.java`, and the per-tap decision logic
  of `MainActivity.handle()`/`lostContact()` as `Presentation.run`, returning
  an `Outcome` the UI renders.
- `Framing.swift` — CRC_A plus a read-only GET_VERSION probe that establishes
  whether the platform or the app appends the command CRC (see below).
- `ios/tools/check.sh`, `ref.py`, `parity-cases.json` — `swift test` plus a
  byte diff against `nfcraft/ndef.py`, using the Android cases plus 24
  boundary/parser-disagreement cases.
- `ios/README.md` — the Core NFC adapter contract and the ordered device spike.

## Findings

1. **Command CRC is not settled by documentation.** Apple's current
   `sendMiFareCommand(commandPacket:)` reference (DocC JSON, read 2026-10-04)
   says the app must append the 2-byte CRC for `ultralight` commands. Whether
   responses carry a CRC is undocumented. The core therefore probes framing
   with GET_VERSION before anything else and never discovers it by a WRITE.
2. **The obvious probe order was unsafe; tests caught it.** Trying the
   documented framing (app CRC) first is ambiguous: if the platform also adds
   a CRC and the tag ignores trailing bytes, GET_VERSION still answers, and
   every later WRITE would carry two stray bytes. The probe now sends the bare
   frame first — a tag never answers a frame without a valid CRC — and a
   lenient-tag regression test pins it.
3. **Android validation diverges from `ndef.py`** (confirmed by running both):
   Java accepts `https://a.co:65536` and `:99999`, which Python rejects, and
   rejects `https://a.co:`, which Python accepts. The Swift port follows
   Python. Low severity (unusual URLs), but Android could write a card the
   Python tooling decodes as foreign. Not changed here; Android is outside
   this slice.
4. **FAST_READ ladder start.** With an unknown response limit the Java formula
   starts at 15 pages and halves to 7 and 3. Core NFC exposes no limit, so the
   Swift port starts at 16 (16, 8, 4, then READ).
5. **A refused WRITE is not a card that moved.** Android reports a final NAK
   mid-plan as "The card left the field". Swift says "Write refused".
6. **Lost answer to the commit write.** As on Android, a commit whose answer
   is lost is reported as an interrupted write, not "committed"; a test now
   states that explicitly.

## Independent review and fixes

A separately invoked Codex session (ATD route `codex:mphi`, model
`gpt-6.1-sol`, effort high; owner label "codex:mphi 6.1 sol high") reviewed
e0ea86c as explicit files and returned REQUEST_CHANGES with seven findings.
The git-diff packet was refused by ATD's privacy guard because of the
deliberately fake credential URLs in the test fixtures; those two files were
omitted rather than overriding the guard. All seven were reproduced and fixed,
each with a regression test that fails when its fix is removed:

| Finding | Fix |
| --- | --- |
| F1 high: a CRC-frame answer is ambiguous, so the probe could still choose app CRC | Probe tries every bare attempt first; a CRC-only answer allows inspection but returns `framingUnconfirmed` instead of writing |
| F2 high: the staged header alone let foreign data be overwritten without the override (inherited from Java) | Resume requires a `RecoveryRecord` for this UID and destination whose pages pass a `recovery_matches()` port |
| F3 high: `Tag215.readArea`/`writePage` could run before GET_VERSION or inspection | Internal gates; nothing is sent otherwise |
| F4 medium: Swift rejects an empty fragment/credentials that Python accepts | Kept stricter, recorded as `stricter` cases checked on both sides |
| F5 medium: overlapping presentations could interleave plans | `Station` admits one presentation at a time |
| F6 medium: a GET_VERSION change after writing was reported as `notNtag215` | Reported as `identityChanged` once a page was sent |
| F7 low: the terminator test changed a URL byte | Now changes the terminator itself |

A focused re-review of the fixes confirmed F1 and F3–F7 and raised two more,
both fixed with regression tests:

| Finding | Fix |
| --- | --- |
| R1 medium: a GET_VERSION change after writing still returned a recovery record | Cleared; the card is set aside |
| R2 high: a reconnect could reach a different card and inherit the first card's inspection — an A→B→A sequence could combine B's readback with A's identity (also true of the Android design) | Every reconnect re-checks the full identity against the first inspection; a mismatch ends the presentation, is never swallowed by the FAST_READ ladder, and nothing more is sent |

## Checks (actual)

| Command | Result |
| --- | --- |
| `ios/tools/check.sh` at e0ea86c (Docker `swift:6.1-noble`, Swift 6.1.3, Linux x86_64) | PASS: 47 XCTest cases, 0 failures; parity PASS over 110 lines |
| `ios/tools/check.sh` after all review fixes | PASS: 60 XCTest cases, 0 failures; parity PASS over 114 lines incl. 4 pinned stricter cases |
| One mutation per review fix (F2, F3 ×2, F5, F6, F7, F1, R1, R2) | Each killed by its intended regression test; R2's two safeguards are redundant, so removing either alone passes and removing both fails |
| Same, with the port limit mutated to 99 999 | FAIL as intended on EDGE[2], EDGE[3]; source restored |
| `.venv` `python -m unittest discover -s tests` | PASS, 118 tests |
| `android/tools/parity.sh`, Gradle tests | NOT_RUN (Android unchanged) |
| Xcode build of an iOS target | NOT_RUN — no Mac; no app target exists |
| Core NFC on a device, any card read or write | NOT_RUN — no iPhone, no tag, no authorization |

Simulation only. None of this is iPhone NFC evidence.

## Data, migration, rollback

No journal, preference, manifest or URL format changes. Delete `ios/` and the
`.gitignore` lines to roll back. The Docker build cache lives in the
`nfcraftkit-build` volume (`docker volume rm nfcraftkit-build`).

## Next bounded task

On a Mac with Xcode: create the iOS app target, add `NfcraftKit` as a local
package, write the ~60-line Core NFC `Type2Link` adapter described in
`ios/README.md`, and run spike steps 1–3 (read-only) on an NFC iPhone. Step 4
(one write) needs separate owner authorization for a named disposable card.
