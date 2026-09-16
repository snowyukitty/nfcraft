# 2026-09-16 — the phone writer stops giving up on a weak card

## Objective

The owner reported that writing a card fails often, and that a card that
eventually succeeds usually needs a long time of repositioning first. The
failing surface is the native Android writer, which at the start of this
session lived outside version control in an ignored working directory.

Two things were done: the reliability defect was found and fixed, and the
writer was moved into the repository it belongs to.

## Scope

- `android/` (was `work/card-writer-android/`), the whole tree.
- `README.md`, `CHANGELOG.md`, `.gitignore`, `.github/workflows/ci.yml`,
  `docs/PROJECT-STATE.md`.
- `reports/*.md`: internal process references removed ahead of publication.

No change to `nfcraft/`, the journal schema, the public manifest schema, card
identities, slugs or any URL.

## What was actually wrong

Not the encoder. `tools/parity.sh` has agreed with `nfcraft/ndef.py` byte for
byte since before this session, and still does.

One card presentation issues roughly thirty radio exchanges: `GET_VERSION`, two
head reads, a 496-byte area read, the write plan, a second 496-byte read, and a
second inspection. Every one of them was attempted exactly once. A wooden card
puts several millimetres between the tag antenna and the phone, so the link is
weak, and losing a single exchange — a CRC failure, a small hand movement, the
platform's own presence check landing between two commands — ended the whole
presentation.

At a two per cent chance of losing any one exchange, about half of all
presentations fail. That matches the report exactly, including the shape of it:
nothing wrong with the card, nothing wrong with the bytes, just repeat until one
pass happens to survive.

## The fix

In `android/app/src/main/java/best/tgs/cardwriter/Tag215.java` unless noted.

| Change | Why it is safe |
| --- | --- |
| Every exchange retried up to four times | Reads are idempotent by nature |
| Connection re-established between attempts | Android permits close-and-connect while the tag is in the field; this is what recovers a presence check landing mid-plan |
| First connect retried (`Tag215.open`) | Nothing has been read, decided or written yet |
| Wrong-length answer treated as a failed exchange | On this link a short answer is a corrupted one, not a card with something different to say |
| Page writes retried | A four-byte page write is idempotent: the same bytes at the same address land the same way |
| A lost write answer settled by reading the page back | Silence is never read as success; the existing no-ACK path was extended, not weakened |
| NAK `1h`/`5h` retried, `0h`/`4h` final | Parity/CRC and EEPROM-write errors are conditions a steadier moment clears; the other two are the card refusing |
| FAST_READ steps 16 → 8 → 4 pages before plain `READ` | A chunk this link will not carry is a reason to ask for less, not to abandon the fast path |
| Only pages that would change are written (`Ndef.writePlan(url, current)`) | The final area is identical; this only decides which pages travel |
| "Weak contact, hold still" shown while it is happening, and the link cost recorded on the receipt (`MainActivity.java`) | The one thing a person holding a card can do about weak coupling is stop moving |

**No safety check was loosened.** Every refusal still refuses, the full-area
readback plus preserved tail is still the only evidence a write is accepted, the
identity and configuration comparison still runs, and no command outside
`GET_VERSION`, `READ`, `FAST_READ` and `WRITE` to pages `0x04..0x7F` exists.

The staged-write invariant is preserved under pruning: the commit step is always
kept and always last, and the staged step is dropped only when the card already
advertises a zero-length message. `PlanTest` checks this on every state.

## Commands run, and what they said

| Result | Command | Evidence |
| --- | --- | --- |
| PASS | `gradle assembleDebug` (JDK 21, offline) | `android/app/build/outputs/apk/debug/app-debug.apk`, rebuilt after the move |
| PASS | `bash android/tools/parity.sh` | encoder parity with `nfcraft/ndef.py`; 1,087 pruned-plan states; 10 link behaviours |
| PASS | `.venv/Scripts/python.exe scripts/preflight.py` | Python 3.12.10, Node 24.18.0, no reader accessed |
| PASS | `.venv/Scripts/python.exe scripts/verify.py --require-node` | python-unittest, python-compile, demo-process-smoke, ui/library/guide/worker syntax, worker-tests |
| PASS | GitHub Actions run 35059120757 | 5/5 jobs: 4 × `verify` matrix plus the new `android-encoder` |
| **NOT_RUN** | Any of this against a physical card | No phone was attached to this machine during the session |

The two new suites were checked against a deliberate regression: setting
`ATTEMPTS` to 1 makes `LinkTest` fail at the first simulated dropped exchange,
so they test the change rather than agreeing with it.

## What is still not proved

- **The fix has not met a wooden card.** It is checked against a simulated link
  that misbehaves far more than a real one. The number to watch on the bench is
  how often the receipt reports retries at all — that is the coupling margin
  becoming visible instead of silent.
- **The recipient-facing check remains NOT_RUN.** Nothing yet confirms that
  tapping a written card on a *different* phone opens the destination.
- The refusal paths — locked, protected, foreign — have not met real hardware.
- The torn-write resume path has been exercised in checks, not by pulling a card
  away mid-write.
- PC/SC hardware writing is untouched by this session and remains unqualified.

## Publication

The repository was made public at the owner's explicit instruction, and `main`
was pushed to it. Before that: the working tree was scanned for local paths,
device serials, account identifiers, credentials and control-plane references,
and the internal process references in `reports/` were removed. Those lines
remain in four earlier commits, which the owner accepted; they name an internal
lease command and an agent, and contain no registry, port map or other
repository name.

Actions minutes for this repository are no longer metered.

## Next bounded task

Take one wooden NTAG215 and one phone, write a card, and record two things: the
`link` line on the receipt, and whether a *second* phone opens the destination
when it taps the finished card. That single pass closes the largest NOT_RUN
above and gives the first real number for the coupling margin.
