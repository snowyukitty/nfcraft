# Architecture: a workshop, not a fleet of services

## Product decision

The first usable product is a local operator app with one durable engine. It must be useful before a reader arrives and must not claim the reader works before a real pilot. A tiny source app is preferable here to simultaneously maintaining Rust, React, Tauri, Android, an MCP service and several cloud workers before any physical evidence exists.

Python was selected for the initial implementation because its standard library covers the UI server, SQLite, JSON, threading and CLI, while pyscard exposes native PC/SC. The front end is plain HTML/CSS/JavaScript with no build step. This is a delivery/iteration choice, not a measured throughput claim. The adapter can later be replaced with a Rust or other native implementation without changing the operation model.

```text
Operator browser / optional desktop window
                 │ operator capability: approve, edit, recover
Agent CLI / MCP  │ agent capability: prepare, inspect, pause, export
          └──────┴────── authenticated loopback API
                              │
                     Single deterministic Engine
                       │                 │
                  SQLite journal       Reader interface
                                         ├─ Persistent Mock (implemented)
                                         ├─ ACR1552 PC/SC (experimental)
                                         ├─ Android NfcA (planned)
                                         └─ Web NFC NDEF-only (separate future capability)

verified routes → reviewed export → Cloudflare Worker / D1 → public page + vCard
```

The engine has no AI API dependency. Agents help with planning, content drafts, diagnosis and reports; they are not on the timing-critical per-card path. Human feeding remains one physical card at a time. A robot/feeder, multi-reader line and multi-station coordinator are outside v0.1.

## Data and authority

`profiles` contains editable local public-content drafts. `batches` bind a target count, route origin and profile ID. `cards` binds each UID to one random 128-bit slug, immutable URL, ordinal, saved original memory and intended target. `attempts` records each write/recovery. `audit` records operational events. All live writes are serialized through one engine lock. An OS-held workspace lock prevents a second daemon from opening the same operational workspace.

The SQLite state is:

```text
reserved → writing → verifying → verified
    └────────┴──────────┴───────→ quarantined
```

A startup recovery pass quarantines pending reservations/writes/verifications. No persisted approval reactivates hardware. Quarantined cards keep their identity, consume a reserved place in the batch, and are not included in public route exports. Replacement cards should use a deliberately created new batch rather than silently inheriting uncertain IDs.

Separate concepts must not be collapsed:

| Concept | v0.1 evidence |
|---|---|
| Locally encoded and verified | Engine's complete readback and configuration comparison; simulated in demo |
| Desired public route enabled/suspended | Local setting included in the next export |
| Public URL actually available | Not automatically tracked; manual deployment and remote check |
| Card issued / final physical QA passed | Not tracked in app; pilot acceptance sheet |

Profiles are separate from immutable tag URLs. Updating a profile then republishing the Worker database updates what existing cards show. The first UI supports one profile; multiple personas/campaign profiles are a later UX task, not an implemented feature hidden behind a schema field.

## Write boundary

NTAG215 has 504 physical user bytes, but its factory capability container `E1 10 3E 00` advertises a 496-byte NDEF memory area. The writer intentionally uses only pages 0x04..0x7F and caps ASCII HTTPS URLs at 200 bytes. The last eight physical user bytes are not used by this implementation. NDEF/TLV overhead still consumes space.

Before any reservation, the engine requires the exact NTAG215 GET_VERSION bytes, a seven-byte UID, expected CC, clear relevant lock bits, disabled authentication, disabled mirroring and expected access settings. It never modifies the capability container to make a mismatched card “fit.” UID/version inspection does not constitute cryptographic authenticity verification.

A single short-form NDEF URI record uses the HTTPS prefix code 0x04. The URL is the only record. A write first exposes a zero-length NDEF TLV, writes subsequent four-byte pages, and finally commits the first page with the intended length. It then reads the entire advertised area and verifies both the target and the preserved tail, plus identity/configuration consistency. The zero-length convention reduces partial advertised messages; it does not make EEPROM writes atomic.

The adapter rejects writes outside the permitted user pages. There is no general memory-write API or model-controlled APDU. Unknown responses fail closed rather than trying a different write command. Reader USB presence, UID retrieval and raw Type 2 memory support are different capabilities.

## Bounded automation

A human approves an exact batch name, count limit and ten-minute maximum expiry. The worker latches a UID until removal is observed. A repeated card is not given a new slug. A fault stops the run. An in-flight pause is observed between page operations; it can leave an uncertain card, so pause is not undo. Recovery is one-card, explicit, UID-bound and compares the observed partial state to recorded evidence before writing.

The current driver checks UID at page boundaries but cannot defeat a malicious emulator that copies UID and memory. One card physically present in the work area is an operational requirement, not something this release proves through RF field inventory. The GUI may not animate every internal stage because hardware work is serialized under the engine lock; final state and errors are authoritative.

## Offline and publication

Creation, simulation and local provisioning do not require an online backend. Offline provisioning still cannot make an unregistered URL live. The recommended pilot deploys a public site before final handoff and explicitly publishes verified identities afterward. There is no cross-database atomic transaction or automatic two-phase commit with the cloud.

v0.1 uses a public manifest and reviewed SQL import rather than an unreliable “sync succeeded” badge. This avoids embedding cloud credentials in the writer and keeps the public Worker read-only. A later sync worker should use an outbox, idempotent revisioned operations, acknowledgements, DNS/TLS checks and independent URL probes. Never start by adding those checks to every NFC page write.

## Future Android split

Web NFC is useful for low-cost NDEF-only writing in supported Android Chrome. It does not expose the raw NTAG215 configuration inspected above. Native Android NfcA can offer a closer raw-reader adapter, but needs an app, lifecycle handling and authenticated task delivery. These should advertise different capabilities rather than implementing a dishonest universal `inspect()`.

A phone bridge must pair via short-lived one-time credentials, accept a bounded job lease, locally enforce approved destination/size, report completion independently, and handle network/session loss. NDEF write completion alone is not independent verification; require a new read/retap. An empty or unreliable Web NFC serial number cannot satisfy this engine's UID-bound recovery contract. Do not reuse the current localhost operator token on a phone.

## Facts and evidence

Protocol facts and platform constraints are sourced in SOURCES.md. The exact physical ACR1552 firmware has not been exercised. TEST-REPORT.md is the acceptance evidence for this archive, not a roadmap disguised as completed work.
