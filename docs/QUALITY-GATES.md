# Quality gates — evidence before claims

Use exactly `PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED` with a reason and evidence reference. A prerequisite being absent is not PASS. A gate can be partially complete. Report hardware, app, public-site and packaging readiness separately.

## G0 — Provenance and baseline

Confirm project root/identity/version, current diff, interpreter/OS, data locations and legacy detection. Preserve existing files. Run `scripts/preflight.py` and `scripts/verify.py --require-node`; record tool versions and logs. Build a package/wheel if distributing Python artifacts and verify bundled web assets.

## G1 — Local app and deterministic workflow

In the actual target browser: create a draft (zero writes), approve a bounded mock run, initialize ten distinct virtual cards, hold a card (no second allocation), re-present a duplicate (no mutation), reject foreign/locked/wrong-chip/hidden-write-region content, exercise interruption and original-ID recovery, pause between pages, expire a lease, restart and verify no automatic approval. Test persistence, backups, optional QR and exports. Include process-level CLI/MCP behavior and agent denial of operator operations.

An automated demo test must use disposable synthetic state. It cannot obtain the real operator token or approve real hardware. The handoff's Python tests and process smoke are evidence for this subset, not complete Windows browser acceptance.

## G2 — Read-only hardware

Capture exact reader/interface/firmware/OS/driver/manual revision, UID/GET_VERSION/CC/configuration observations, supported APDU/session/ACK shape, clean insertion/removal/reconnect and exclusive ownership. Never issue write/protection commands at this gate. No unexplained framing mismatch may be waved through.

## G3 — One real card, then pilot

Owner-approved expendable card; agreed real durable origin; explicit experimental flag plus independent human batch approval; durable reservation before first write; byte-for-byte target/preserved-tail readback; unchanged identity/configuration; observed failure/recovery semantics. Proceed to ten cards only after one succeeds. Record physical labels and results privately. Measure speed only on actual cards.

## G4 — Public site

Real local Worker+D1 integration, isolated preview/prod database, reviewed profile and public manifest, explicitly scoped destination, backup/rollback. After approved deployment verify an exact card URL, vCard response, unknown/suspended behavior, escaping and public-only fields from outside the workstation. Preserve existing issued URLs and newer revisions. A handler unit test with mocked D1 does not pass this gate.

## G5 — Packaging and operating system

Run the app and optional packaged desktop/tray on the target Windows environment. Verify startup without admin, shutdown/restart, paths with spaces/Unicode, single instance, web assets, optional dependency failures, log/credential handling and persistent data location. State unsigned/signed accurately. CI passing on Windows is useful but not a physical-reader or clean-machine installer result.

## G6 — Ready to distribute

Final wooden card after printing/engraving/coating, NFC opened on actual test phones, QR scanned from actual print, same intended route, contact import checked, human-readable fallback/contact detail reviewed, publication confirmed, backup/restore and protection decision recorded. Unprotected cards remain rewritable; acknowledge that distribution choice. Never enable irreversible locking as an automatic final step.

## Evidence format

Record timestamp/timezone, source version/commit, hardware/tool versions, actual command/test procedure, expected and actual outcome, result, private evidence location and sanitized summary. For failures include whether mutation could have occurred and safe recovery. Do not share operator tokens, raw production UIDs, private profiles or full local environment dumps.

## Completion wording

"Local demo validated" is appropriate after local checks. "Physical pilot passed" needs G2/G3 and actual logs. "Public URL deployed and verified" needs G4. "Ready to hand out" needs the relevant gates including G6. This release is a **source handoff**, not a fully qualified production deployment.
