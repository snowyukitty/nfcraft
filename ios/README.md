# nfcraft for iPhone — platform-neutral core

**Status: core implemented and checked off-device. No iOS app target, no Xcode
build, no iPhone and no card have touched this code.** The iPhone writer does
not exist yet; this is the part of it that can be built and proved without a
Mac.

`NfcraftKit` is a Swift package holding everything the iPhone writer decides:

| File | What it is |
| --- | --- |
| `Ndef.swift` | Port of `nfcraft/ndef.py` (via `android/.../Ndef.java`): validation, area encoder, strict decoder, staged/pruned write plan, write fence |
| `Tag215.swift` | Port of `Tag215.java`: GET_VERSION identity, protected-configuration checks, FAST_READ ladder, retried exchanges, ACK/NAK handling with read-back of swallowed acknowledgements |
| `Framing.swift` | CRC_A and a **read-only GET_VERSION probe** that establishes how this platform frames raw commands (see below) |
| `Presentation.swift` | The per-tap decision logic of `MainActivity.handle()` / `lostContact()`, lifted out of the UI and returning an `Outcome`; `Station` runs one presentation at a time |
| `RecentURLs.swift` | Port of `RecentUrls.java`: ten valid, distinct, most-recent-first destinations |

It imports nothing from Core NFC or UIKit. A screen renders an `Outcome`; it
never decides whether a card was written.

Deliberate differences from the Android writer, each pinned by a test:

- **Resuming a torn write needs a recovery record.** The staged header
  `03 00 D1 01` is identical for every destination, so on its own it proves
  nothing. An interrupted write returns `Outcome.recovery` (UID, the area
  before the first write, and the destination); the app keeps it on the device
  and passes it back. A card resumes without the override only when every page
  is attributable to that record, as `recovery_matches()` checks in the Python
  engine.
- **The command layer gates itself.** `Tag215` refuses to read the user area
  before an exact GET_VERSION, and to write before an inspection that passed.
- **A reconnect must find the same card.** A retry may re-establish the link,
  and whatever tag is then in the field answers. Each connection is a new
  generation: only identity reads are sent on it until GET_VERSION, UID, CC,
  locks and configuration have been proven equal to the first inspection on
  that same connection. A difference ends the presentation at the first
  differing byte; an unfinished check authorizes nothing. An inspection
  interrupted by a reconnect restarts from GET_VERSION, so its three reads
  always come from one tag. (Android reconnects without these checks.)
- **One presentation at a time.** A second request on a busy `Station` is
  answered `busy` before anything is sent.
- **Validation follows `ndef.py`, not Java, except where it is stricter.**
  Port range and empty port match Python. An empty fragment or empty
  credentials (`https://tgs.best#`, `https://@tgs.best`) are rejected here
  although Python accepts them; `parity-cases.json` lists these as `stricter`
  and the check fails if either side changes.

## Check it (Windows, Linux or macOS)

```sh
ios/tools/check.sh
```

Runs `swift test` and diffs the Swift encoder against `nfcraft/ndef.py` over
`ios/tools/parity-cases.json` (the Android cases plus boundary and
parser-disagreement probes). It uses a native `swift` if one is on `PATH`,
otherwise the official `swift:6.1-noble` Docker image with a `nfcraftkit-build`
cache volume. A pass is **simulation evidence only**.

## Why command framing is probed, not assumed

Apple's `NFCMiFareTag.sendMiFareCommand(commandPacket:)` reference (DocC JSON,
read 2026-10-04) says: *"For `ultralight` commands, you must calculate a 2-byte
CRC value and append it to the end of the `command` data."* Whether responses
then carry a CRC is not documented, and the statement itself is unverified on
hardware. Guessing wrong on a WRITE is exactly the kind of uncertainty this
app refuses to resolve with a card.

So `Presentation.run(_:_:framing: .probe)` first sends GET_VERSION — which
changes nothing on any Type 2 tag — as a bare command, then with an app CRC, and
accepts only the exact NTAG215 version (optionally followed by a valid response
CRC). Bare first is deliberate: a tag never answers a frame without a valid
CRC, so a bare answer proves the platform added it, whereas a CRC-first answer
can come from a tag that ignores two stray trailing bytes.
No answer under any framing means "not an NTAG215", and nothing is read or
written beyond that probe.

Only a bare answer authorizes writing. If only the CRC-carrying frame is
answered, that is still ambiguous — a tag that ignores trailing bytes on a
platform that adds its own CRC looks the same — so the presentation inspects
normally but answers `framingUnconfirmed` instead of writing. Writing then
needs `.fixed(framing)`, set by the adapter from the recorded device spike.
A `Station` reuses a bare probe result for later taps. Every page write still requires the full readback and
unchanged identity before the result can be `written`/`finished`.

## Core NFC adapter — the next step, on a Mac

Not in this tree: the repository rule is that no uncompiled iOS scaffold is
presented as a deliverable. The adapter is small and must be written where it
can compile. Its contract is `Type2Link`:

| `Type2Link` | Core NFC |
| --- | --- |
| `connect()` | `session.connect(to: .miFare(tag))` (idempotent while connected) |
| `transceive(_:)` | `tag.sendMiFareCommand(commandPacket: Data(command))` |
| `disconnect()` | no-op; the session owns the link |
| `maxResponseBytes` | `nil` (not exposed; the FAST_READ ladder discovers it) |

Create one `Station` per reader session and call `present(_:)` from a `Task`.
Persist `Outcome.recovery` per UID on the device (never in logs or analytics)
and pass it back in the next `Request`.

Points to verify in the installed SDK while writing it (from the 2026-10-04
DocC read; see `apple-app-store-research` source notes):

- `NFCTagReaderSession.init(pollingOption:delegate:queue:)` is marked
  deprecated in iOS 26.4 in favour of `init(configuration:delegate:queue:)`.
  Choose per deployment target with `#available`.
- Entitlement `com.apple.developer.nfc.readersession.formats` currently lists
  only `TAG`. Info.plist needs a non-empty `NFCReaderUsageDescription`.
- Whether an NTAG215 reports `mifareFamily == .ultralight` is undocumented;
  accept `.ultralight` and `.unknown` and let GET_VERSION decide.
- More than one tag in the field: show a message and `restartPolling()`; never
  pick one.
- Call `Station.present` in a `Task`, not on the session's delegate queue.
  Use `alertMessage` for "hold still", `invalidate(errorMessage:)` for any
  non-verified verdict, `invalidate()` only after `isVerifiedWrite`.
- A session timeout exists (`readerSessionInvalidationErrorSessionTimeout`);
  its length is not stated in the current reference. Measure one full
  presentation on the device.
- Never log URLs, UIDs or receipts.

## Device spike, in order (all NOT_RUN)

Prerequisites: a Mac with current Xcode, a physically operated NFC iPhone, a
signing team that can carry the NFC entitlement, and owner-approved disposable
NTAG215 cards. **Steps 1–3 never write. Step 4 needs separate owner
authorization for the named disposable card.**

1. Build and install a development build; confirm `readingAvailable`.
2. Inspect only: framing probe result, `mifareFamily`, inspection result,
   read path (`FAST_READ 16p`/`8p`/`4p`/`READ 4p`). If only the CRC frame is
   answered, establish the framing from this evidence and fix it in the
   adapter before step 4.
3. Inspect a card that already carries an nfcraft URL written by Android or
   PC/SC: the decoded URL must match.
4. Write one disposable card; record verdict, framing, effort and read path.
   Then read it with a *different* phone (recipient check).
5. Torn write: lift the card mid-plan; expect `writeInterrupted`, then
   `finished` on the next tap without the override.

Simulator, unit tests and this package's checks are not iPhone NFC evidence.
