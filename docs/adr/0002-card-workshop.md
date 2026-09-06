# 0002 — A desktop card workshop with a separate recipient experience

Status: accepted for the 0.2.0 local increment, within the existing product direction. Date: 2026-09-06.

## Context

The owner asks whether nfcraft is an app and what kind of app it should become. It already is a local Python/SQLite application with a web UI, optional native Windows WebView2 window/tray, an unsigned portable package, and a separate public Worker. Its primary job is safely managing physical cards and durable identities, not requiring recipients to install software.

## Decision

Keep one native-OS writer with desktop-first operation. Both browser and native-window modes use that same engine and journal. Keep the public recipient experience a small responsive web page with a contact download. Preserve the current architecture rather than replacing it for cosmetic reasons.

Organize the operator experience around preparation, the current physical operation, card lookup/recovery, and explicit review of what will leave the workstation. Put mode, write permission and the next safe action first. Show identity evidence and exact export route entries on demand. Keep unknown public/phone stages visibly unknown.

For 0.2.0, deliver a searchable/paged card library, per-card lifecycle facts, live recipient preview, and reviewed public export. Use one public renderer in both preview and Worker to reduce design drift. Local preview receives only explicit form fields and uses escaped markup with disabled actions; the loopback CSP remains unchanged.

Use a content checksum to reject stale export reviews. This is an accidental-change check, not authentication or deployment acknowledgment. Display shared-profile impact because a filtered route manifest can still update other public cards sharing that profile. Keep CLI compatibility exports while the operator UI gets the more explicit review workflow.

## Evidence informing the design

- [Microsoft navigation basics](https://learn.microsoft.com/en-us/windows/apps/design/basics/navigation-basics): use a clear, consistent information hierarchy for desktop navigation.
- [NN/g visibility of system status](https://www.nngroup.com/articles/visibility-system-status/): actions should produce understandable feedback. Applied to draft, verification, export and unknown publication states.
- [NN/g progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/): defer secondary detail while preserving access. Applied to UID/hash evidence and exact route entries.
- [Chrome Web NFC documentation](https://developer.chrome.com/docs/capabilities/nfc): browser NFC is based on NDEF and does not provide the raw command surface this workstation's tag-safety inspection requires. This supports keeping the native PC/SC path central; it does not rule out a separately designed future phone adapter.
- [Cloudflare Workers best practices](https://developers.cloudflare.com/workers/best-practices/workers-best-practices/): preserve the existing request-local D1 binding/response path and avoid adding cloud/admin dependencies to public rendering.

These references inform design choices; local tests, not the references, establish implementation behavior.

## Boundaries and next increment

No schema migration, card identity changes, remote mutation, protection changes, public chat, new framework or mobile writer. UI paging bounds DOM rows; the legacy state snapshot still contains the full inventory, so large-fleet scalability is not claimed. Full publication receipts require an authoritative workspace namespace, equal-revision conflict handling and independently verified destination/URLs. Those remain the next operational design task after this useful local slice.
