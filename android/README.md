# Card Writer — native Android rewrite tool

Writes one HTTPS URL to one NTAG215 card, verifies it by reading the whole
advertised area back, and does it with no PC, no cable, no network and no
hosted page.

**Status: physically proved on one NTAG215, on one phone.** The encoder is
checked byte-for-byte against the Python reference in
[`nfcraft/ndef.py`](../nfcraft/ndef.py), an independent review has been applied,
and the command layer now rides out a link that stutters. The recipient-facing
check is still outstanding — see "What is proved, and what is not".

## Why this exists

The desktop app in this repository drives a USB PC/SC reader, and an earlier
station drove Web NFC in Chrome over `adb reverse` — which needs the PC for the
secure context, the progress state, the audible status channel and the journal.
This app removes all of that, and the foreground trap with it: in reader mode a
foreground activity owns the NFC field, so the system tag viewer never sees a
card and cannot steal the scan the way it does from a browser tab.

It is deliberately **not** a batch station. There is no resume, no serial set,
no reconciliation. One card, one tap, one verified result.

## What it does per tap

1. `GET_VERSION` must return the exact NTAG215 bytes, or nothing else is read.
2. Reads pages 0–3 and 0x82–0x85 for UID, capability container, static and
   dynamic lock bytes, CFG0 and CFG1.
3. Refuses a card whose CC is not `E1103E00`, whose lock bits are set, whose
   `AUTH0` is not the factory `0xFF`, or which has mirroring, counters, access
   limits or config locking enabled.
4. Reads the whole CC-advertised area, pages 0x04–0x7F, 496 bytes.
5. Decides what the card holds: our canonical URL record, blank, an interrupted
   write by this app, or content it does not recognise. Unrecognised content is
   refused unless you switch overwriting on. An empty TLV hiding data inside the
   planned write region is refused the same way.
6. Writes the plan from `nfcraft/ndef.py`: an empty-length TLV first, then the
   body pages, then the first page again with the real length — skipping any
   page the card already holds.
7. Reads the whole area back and requires it to equal the intended write
   **plus the untouched tail** beyond it.
8. Re-inspects and requires identity and protected configuration to be
   unchanged.

A write that completes is not the evidence. Step 7 and step 8 are.

## What it can never do

There is no command in this app that changes lock bits, the capability
container, `PWD`, `PACK`, `AUTH0`, mirroring or any page outside 0x04–0x7F.
Those are absent, not disabled. `makeReadOnly` has no equivalent here: the app
cannot lock a card even if asked.

## Holding a card that will not hold still

This is the part that decides whether the app is usable on a bench, and it is
where the first build fell down.

One card presentation is not one radio exchange. It is a `GET_VERSION`, two head
reads, a 496-byte read, the write plan, a second 496-byte read and a second
inspection — around thirty exchanges over a link that a wooden card, with its
thickness between the antenna and the phone, holds weakly. The first build
attempted each of those exactly once. One CRC failure anywhere, one small
movement of the operator's hand, or the platform's own presence check landing
between two commands, and the whole presentation failed. At even a two per cent
chance per exchange, roughly half of all taps fail — which matches what the
bench actually saw: cards that took several minutes of nudging before one pass
happened to survive.

Nothing was wrong with the bytes. What was missing was a second attempt.

- **Every exchange is retried**, up to four times, first plainly and then after
  re-establishing the connection, which Android permits while the tag is still
  in the field.
- **A wrong-length answer counts as a failed exchange**, not as a card with
  something different to say. On this link a short answer is a corrupted one.
- **Writes are retried too, and they are safe to retry**: the same four bytes at
  the same address land the same way. A write whose answer went missing is
  settled by reading the page back, never by assuming either outcome.
- **A NAK is read for what it is.** `1h` (parity/CRC) and `5h` (EEPROM write
  error) are conditions a steadier moment can clear, so they are retried. `0h`
  and `4h` are the card refusing, and are not: asking again would be pretending
  not to have heard.
- **The first connect is retried**, because a card resting slightly off the
  antenna used to be turned away before anything had even been read.
- **FAST_READ walks down instead of giving up.** A chunk this link will not
  carry halves — 16 pages, 8, 4 — before plain four-page `READ` takes over, and
  the receipt names the path that answered.
- **Only the pages that would change are written.** A card that tore part-way
  through keeps everything that already took, so the second tap is short — which
  matters, because it is the same weak link being asked again.
- **The operator is told while it still helps.** The moment the link starts
  repeating itself the screen says so, because the one thing a person holding a
  card can do about weak coupling is stop moving. The receipt then carries what
  the link cost — `link 3 retries, 1 reconnect · FAST_READ 16p` — so a marginal
  jig shows up as a warning about the next hundred cards rather than as a
  mysterious failure on this one.

None of this loosens a safety check. Every refusal in the list above still
refuses, the readback is still the evidence, and a write is still never reported
as done on an assumption.

## Build

```sh
JAVA_HOME=/path/to/jdk-21 ./gradlew assembleDebug
# app/build/outputs/apk/debug/app-debug.apk
```

The Gradle wrapper is committed, so a JDK 21 and an Android SDK are the only
things a machine needs. Create `local.properties` with `sdk.dir=` pointing at
that SDK; it is machine-specific and deliberately not committed. The project
has no third-party dependencies, so once the wrapper distribution, the Android
Gradle plugin and SDK platform 35 are cached, the build works offline.

## Install

```sh
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Debug-signed for sideloading. A phone that already carries a build signed with
the same debug keystore accepts an update without being uninstalled first;
one signed elsewhere does not. Settings are per-device: the destination, both
toggles and the written count live in each phone's own storage.

## Checks

```sh
tools/parity.sh
```

Three suites, none of which needs a phone. `Ndef.java` and `Tag215.java` have no
Android imports beyond `NfcA`, which is stubbed for the desktop JVM, so all of
this runs on an ordinary JDK.

| Suite | What it pins |
| --- | --- |
| Encoder parity | Area bytes, the page-by-page write plan, the strict decode round trip, emptiness and the occupied-region guard, diffed against `nfcraft/ndef.py` for the same inputs |
| `PlanTest` | Every torn and partial state ends at the intended area once the pruned plan is applied, and no length is ever advertised while the body is in flight |
| `LinkTest` | What the command layer does to a link that drops exchanges, truncates answers, swallows acknowledgements, answers NAK or dies outright |

A card written by this phone therefore carries the same bytes as one written by
the PC/SC path, and still decodes under the Python tooling. Re-run after any
change to either encoder.

## What is proved, and what is not

One NTAG215 has been written and verified on a real phone. The app only reaches
the green "Written" state after the whole chain succeeds, so that single tap
cleared a good deal at once:

* `GET_VERSION` returned the exact NTAG215 vector on a real tag.
* The identity and configuration checks passed against a real card — CC
  `E1103E00`, clear static and dynamic lock bytes, factory `AUTH0`, no
  mirroring or access limits.
* A full 496-byte read of pages 0x04–0x7F completed over a real NFC stack.
* Every page write in the plan was accepted, so the WRITE acknowledgement
  handling works on that HAL.
* The verifying readback equalled the intended area **plus the untouched
  tail**, and the re-inspection matched the pre-write one byte for byte.

Still **NOT_RUN**, and worth keeping honest:

* **The reliability work above has not met a wooden card.** It is checked
  against a simulated link that misbehaves far more than a real one, and that
  is not the same as a bench result. The number to watch is how often the
  receipt reports retries at all.
* **The recipient-facing check.** Nothing yet confirms that tapping a written
  card on a *different* phone opens the destination. A rig that drifts produces
  cards that read back perfectly at the station and still fail in someone's
  hand. Do this before any card is handed over.
* The refusal paths — a locked, protected or foreign card — have not met real
  hardware.
* The torn-write resume path, which is the fix for the review's highest-severity
  finding, has been exercised in checks but not by pulling a card away
  mid-write.
* This phone's HAL mapping of the 4-bit Type 2 ACK/NAK, and the wooden-card
  coupling margin. Both need a physical card.

## Independent review

The NFC engine was reviewed by an independent model with the NTAG215 datasheet
and the Android documentation in scope. It confirmed the command framing, the
page map and the write fence against NXP Rev 3.2, and confirmed no path to a
lock, a password or an OTP brick. It found seven real problems. All are fixed:

| Finding | Fix |
| --- | --- |
| **A torn write refused its own card.** `writePlan` stages page 0x04 as `03 00 D1 01`, which is neither a decodable record nor the factory empty TLV. A card that left the field mid-plan was refused as unfamiliar content — while the error copy told the operator to tap it again. | `Ndef.isOurStagedWrite` classifies that pattern and the write resumes without the override switch. This is the single-destination equivalent of the Python engine's `recovery_matches`. |
| **250 ms presence checks would tear the first wooden-card write.** The platform keeps polling a discovered tag at that interval while the whole plan runs. | `PRESENCE_CHECK_MS` raised to 2000. |
| **Every `IOException` claimed the card was unchanged.** | The failure copy now depends on how far the plan got: before any write, mid-write, or committed-but-unverified. The stage advances *before* each attempt, so a write that threw is never reported as untouched. |
| **An empty WRITE response was assumed to be an ACK.** Some Android HALs surface a NAK the same way. | On an empty response the page is read straight back and compared, instead of waiting for the final full-area readback. A present non-ACK byte still fails. |
| **`hidesDataUnderEmptyTlv` could not see this app's own staged page.** | Left as-is for foreign `FE`-form empty TLVs, with the staged pattern handled by the new classifier. |
| **View state read from the binder thread.** `getText()` and `isChecked()` were called from `onTagDiscovered`. | The URL and both switches are snapshotted into volatiles on the UI thread; the NFC path reads only those. |
| **`busy` was a check-then-set.** A rediscovery could call `connect()` on a tag that still had a live technology. | `AtomicBoolean.compareAndSet`. |
| *(note)* FAST_READ chunking was derived from the **send** limit, and a 240-byte response is the first thing to CRC-fail on weakly-coupled wood. | Capped at 16 pages, and now halved further by the ladder above when the link will not carry it. |

## UI

| Control | Effect |
| --- | --- |
| Destination | The HTTPS URL, validated live with the same rules as the Python encoder, remembered between launches |
| Inspect only — never write | Reports what a card holds and writes nothing |
| Allow overwriting unrecognised content | Required before replacing content this app cannot decode |

| Colour | Meaning |
| --- | --- |
| warm near-black | idle or ready |
| rust-brown | working, or a weak link that is still being retried |
| green | written and verified |
| teal | inspected, or already carries the destination |
| red | refused or failed |

Sound and vibration accompany every result, so the phone can lie face down on a
jig. The screen is held on while the app is open, so `svc power stayon` is not
needed.

## Identity

The launcher mark was designed with IconFlow and lives in `master.svg`, with the
scored receipt in `master-review.json`, the shipped raster set in `icons/`, and
the design record in `casebook/`.

Essence **restamp**; a cream hand press on a rust ground with the amber imprint
it has just struck held clear beneath it. The cliché avoided was the NFC wave
fan, and equally a second contact card with a tap cue — nfcraft already owns
that object, and a sibling surface needs a different one rather than a restyled
copy. Six rubric axes all scored 4/5. The Android adaptive layers in
`app/src/main/res/mipmap-*` are derived from the shipped `icon-512*.png`, with
the mark at 72/108 of the foreground canvas so it sits inside the guaranteed
safe circle.

The icon is yours: no attribution required, commercial use unrestricted,
nothing viral attached.
