# Physical pilot acceptance — UNEXECUTED TEMPLATE

Date / operator:
OS / architecture / Python / pyscard:
Reader exact model / PICC name / firmware / driver:
Card supplier / batch / final material / print or engraving:
Public hostname / profile revision:

| Gate | Evidence | Result |
|---|---|---|
| Reader enumeration and exact interface | | NOT RUN |
| Read-only UID/BCC / GET_VERSION / CC / locks / config | | NOT RUN |
| Transparent wrapper and RF/ACK interpretation | | NOT RUN |
| Clean insertion, removal, reconnect, exclusive contention | | NOT RUN |
| One expendable card readback and independent verification | | NOT RUN |
| Ten cards, unique identity mapping | | NOT RUN |
| Duplicate / foreign / locked / wrong-chip refusal | | NOT RUN |
| Interrupted write retains identity and explicit recovery | | NOT RUN |
| No UID, CC, lock, config, password or PACK writes | | NOT RUN |
| Exact public URL resolves with intended HTTPS/profile | | NOT RUN |
| Android NFC scan / vCard / QR | | NOT RUN |
| iPhone NFC scan / vCard / QR | | NOT RUN |
| Final engraving/printing/coating re-test | | NOT RUN |
| Measured p50 / p95 cycle and retry/quarantine rates | | NOT RUN |

Record sensitive UIDs/traces privately. A redacted report should retain relevant command lengths, status objects and expected/actual data but not expose operational tokens. No permanent-lock gate exists in this release.
