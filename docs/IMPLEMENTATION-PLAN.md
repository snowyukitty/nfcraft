# Implementation plan — ordered, independently testable work

These are **next-agent tasks**, not a list of completed features. Follow current evidence and the owner's priorities; update status only after a real check. Gates are defined in `QUALITY-GATES.md`.

| ID | Priority | Task / concrete exit criterion |
|---|---|---|
| L01 | P0 | Establish target Windows/shell/interpreter state; repo-local venv; run all checks; preserve existing workspaces; save a sanitized baseline report. |
| L02 | P0 | Exercise the actual browser app: normal batch, duplicate, held card, interrupt/recover, expiry, restart and exports. Test a directory containing spaces/non-ASCII text. Fix any failures. |
| H01 | P0 when reader available | Read-only reader qualification with exact model/interface/firmware/manual and sanitized transcripts. No experimental-write flag. |
| H02 | P0 after H01 | One owner-approved expendable card: identity reservation, bounded write, independent readback, recovery and no protected-page changes. Then ten-card pilot with phone/QR evidence. |
| P01 | P0 | Resolve/pin local Wrangler tooling, separate preview/prod configs/DBs, test Worker against real local D1—not only a mock. No external credentials needed for local preview. |
| P02 | P0 after destination approval | Deploy reviewed preview/production, verify exact encoded card URL and vCard, unknown/suspended routes, TLS and public-only data. Record rollback and separate state from local verification. |
| W01 | P1 | Run launchers and desktop/tray build on Windows. Verify dependencies, close/reopen, single instance, private operator URL handling, no admin requirement, and data outside install directory. |
| O01 | P1 | Add publication plan/diff/receipt: validate intended account/origin/workspace namespace/revision before import; persist result and independent URL probe. Retrying must be idempotent. |
| O02 | P1 | Track lifecycle dimensions independently: local write, publication, phone/print QA, issuance, suspension and protection. Show unknown states honestly and preserve evidence references. |
| O03 | P1 | Add inventory search/filter, readable physical labels and an actionable quarantine queue. Exports must match selected rows and never leak UID to public manifests. |
| D01 | P1 | Establish versioned migrations, a backup/restore drill and dependency lock strategy on each target platform; add CI evidence. Do not copy fabricated lockfiles. |
| U01 | P1 | Improve spacing, readability, keyboard control, accessibility and complete error-state copy; add Traditional Chinese UI only with consistent validation/error localization. |
| U02 | P2 | Multiple public profiles/personas, QR label/print sheets, profile preview and reviewed publishing. No private biography copied automatically. |
| A01 | P2 | Actual agent-client interoperability: negotiated MCP version/tools/stdio stderr separation; keep `nfc_*` compatibility or document migration. Review current MCP specification before claiming new-version support. |
| A02 | P2 | Android capability ADR: NDEF-only Web NFC vs native NfcA; authenticated pairing, short-lived jobs, independent verification, cancellation. Do not reuse operator token or unsafe LAN exposure. |
| M01 | P3 | Multi-station/fleet work only after durable per-station namespaces, conflicts/leases, card dedupe policy, deployment ownership and recovery semantics are specified/tested. |

## Portable links checkpoint — 2026-10-09

- Phone follow-up: clean install of 0.4.2 passed after an owner-authorized
  uninstall for a signing mismatch. Do not attempt migration from the removed
  owner installation. Build disposable old-version fixtures for that gate.

- Complete locally: explicit recent-link export/import with validation, preview,
  lossless merge, privacy disclosure and regression tests. No automatic backup.
- Pending: owner-selected application ID, coherent namespace/tooling rename,
  physical cross-installation transfer rehearsal and release signing.
- Use `android/store/TESTING.md` for real-device acceptance. The completed
  transfer implementation is not passed physical migration QA.

## Important risks to review while implementing

### Identity and polish milestone — 2026-10-09

- Complete locally: native tap/cancel/drag-out fix, lighter visual styling,
  brand header, conditional receipt visibility, and screen/font regression tests.
- Pending owner decision: product-centered Android ID; candidate `app.nfcraft`.
  Pause Play creation using the old test-site ID. See `ANDROID-IDENTITY.md`.
- Next bounded implementation after selection: coherent ID/namespace/tooling
  rename with an explicit ten-link transfer path, synthetic transfer tests,
  preserved legacy artifact and side-by-side phone acceptance.
- Still open: physical NFC matrix, release signing, real store screenshots,
  public privacy hosting and Play testing access. Do not equate local tests
  with hardware or publication approval.

### Owner-prioritized Play quality milestone — 2026-10-08

- MBL04 complete locally: consent-based browser sharing, modal/foreground scan
  gate, cross-Activity operation exclusion and session-only unknown overwrite.
- MBL05 complete locally: guide, settings shortcut, switch semantics, small and
  large-text layouts, Turkish-hostname fix and Android 12+ extraction rules.
- MBL03 preparation advances: feature graphic, Console worksheet, free-download
  decision and owner-reported Google verification; artifact/signature checks
  added. Real phone QA, upload key, public support/privacy, screenshots and
  internal/closed testing remain gates, not engineering simulation results.
- MBL06 designed, not implemented: optional one-time Workshop finishes product.
  Resolve merchant country, minSdk compatibility, verification/restore design,
  product/price and Play transaction QA before activation. Future label tools
  and physical craft services remain demand-validation proposals.

### Owner-prioritized mobile release work — 2026-09-29

- MBL01 complete locally: ten recent destinations, deduplication, reuse,
  confirmed clearing, one-time preference migration and restart regressions.
- MBL02 complete locally: nfcraft Android identity, reviewed IconFlow source,
  native adaptive/themed layers and opaque store icons.
- MBL03 prepared: API 36 build, unsigned AAB, optional upload signing,
  listing/privacy drafts and individual-account enrollment guide. Still needs
  account verification, final public contacts/privacy URLs, owner-managed key,
  real device media, physical NFC acceptance and Google closed testing.
- MBL04 next iOS slice: acquire access to a compatible Mac and NFC iPhone,
  prototype exact NTAG215/Core NFC commands read-only, then port encoder and
  safety/readback semantics with shared vectors. No iOS build exists yet.

See `STORE-RELEASE.md`. These are standalone mobile tasks; A02's paired station
architecture remains separate. Do not deploy the local desktop API for phones.

The current hardware loop holds the engine lock while issuing driver I/O; UI state updates may wait. Measure before restructuring. If I/O becomes interruptible/asynchronous, do not weaken single-writer semantics or pretend a timed-out call did not mutate a tag.

The handoff importer copies a stopped schema-1 workspace. It is not a synchronization engine. Once a copied workspace becomes authoritative, do not keep using both copies for further provisioning/publication. Hardware reader exclusivity is not a cross-station identity/namespace protocol.

Current public SQL uses revision-guarded upserts for one authoritative workspace. Equal revision with different content and unrelated workspaces with `main` profiles need explicit conflict handling before automated or shared publishing. Manifest checksums detect accidental corruption, not malicious authorship or physical truth.

Optional desktop dependencies are constrained ranges. Actual platform resolution, packaging and clean-machine testing are outstanding. Do not call an unsigned `dist/` folder a signed installer.

The repository's `.github/workflows/ci.yml` is supplied configuration. Its execution must be verified on the chosen remote; file presence is not a successful CI run.

## Session discipline

### 0.2.0 card workshop progress

O03 search, combined filters, bounded UI pages, matching CSV and actionable quarantine shortcut are implemented; advanced print/physical labels remain backlog. U01 gains stable row focus, clear empty states and progressive card detail. U02 live recipient preview is implemented using the public Worker renderer. O01 gains local export review/stale-content refusal and shared-profile scope warnings, but **no publication receipt, cloud sync, workspace namespace or equal-revision conflict handling**. O02 displays existing facts and explicitly unknown stages; it does not persist new phone/issuance attestations. No schema migration was needed.

### 2026-09-06 progress

L01 complete locally (Git author identity still required for commits). L02 source and packaged browser acceptance passed; hidden-region refusal and pause-between-pages remain unit evidence, not additional browser/physical claims. P01 real local D1/Worker checks and pinned tooling complete; P02 blocked on approved account/hostname/profile. W01 unsigned package and native lifecycle passed on this host; clean-machine and tray-menu visual checks remain. D01 synthetic backup/restore and Windows dependency snapshot complete; future schema migrations remain separate work. U01 approval cap/expiry controls added and browser tested. H01/H02 blocked: no connected reader, PC/SC unavailable. O01/O02 and multi-workspace publication conflict protection remain backlog; do not automate publication yet.

Choose one or a few bounded tasks. For each: state the user outcome; inspect related code; design a failure/recovery test; implement; run; record evidence. Create ADRs only for decisions with enduring consequences. Keep a useful working app after each increment. End with updated project state and one actionable continuation, not a long speculative feature list.

## 0.2.1 checkpoint

W01/U01: reviewed app/tray/favicon identity and English / Traditional Chinese offline guide delivered, with desktop shortcuts and repeatable guide checks. Full operator UI localization remains separate. Source-history/GitHub checkpoint is authorized; see latest session report. H01/H02/P02 remain dependent on real equipment and destination approval.

## 0.2.2 W01 follow-up

Dedicated windowed executable and direct normal-window shortcut replace hidden-script startup. Real ShellExecute and non-minimized dimensions are now required evidence. The prior shortcut-property-only check did not cover actual usability.
