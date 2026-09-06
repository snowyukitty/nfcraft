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

## Important risks to review while implementing

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
