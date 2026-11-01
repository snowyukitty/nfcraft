# Android link rewriting: supported tag profiles

Android 0.5.0 adds exact NTAG213 and NTAG216 profiles alongside NTAG215.
This is implemented and simulated, not physical qualification. The desktop
PC/SC writer and Python encoder remain NTAG215-only.

| Profile | Exact GET_VERSION | Factory CC | NDEF bytes | Writable NDEF pages | Dynamic locks |
|---|---|---|---:|---|---|
| NTAG213 | `0004040201000F03` | `E1101200` | 144 | `04..27` | `28` |
| NTAG215 | `0004040201001103` | `E1103E00` | 496 | `04..7F` | `82` |
| NTAG216 | `0004040201001303` | `E1106D00` | 872 | `04..DD` | `E2` |

The fence covers the CC-advertised area, not every physical user byte.
All writes are exactly four bytes. UID/BCC, CC, locks, configuration, password,
PACK and spare user pages are excluded. The profile must pass inspection
before either NDEF reading or writing. UID block-check bytes are validated;
this does not authenticate an NXP chip or reject every clone.

NTAG213 factory memory starts with the five-byte Lock Control TLV
`01 03 A0 0C 34`, followed by `03 00 FE`. The app recognises that blank layout,
preserves the control TLV and commits the NDEF length in page 05. Cards without
that prefix keep their existing page-04 layout. Layout is never moved during
a rewrite. Unsupported TLVs/content still require explicit overwrite permission.
For the factory NTAG213 layout, at most 139 ASCII URL bytes fit; a layout
without that prefix fits 144. NTAG215/216 retain the product's 200-byte URL cap.
Capacity refusal happens before any write, with a shorter-link explanation.

Every successful write requires the complete advertised area to equal the
target plus preserved original tail, followed by unchanged identity and
configuration. FAST_READ falls back to bounded four-page READ, including
NTAG216's final partial chunk. A WRITE response must be exactly one ACK/NAK
byte; unexplained framing fails closed. Missing ACK still requires page
readback, as before. No generic NDEF/formatting fallback is added.

MIFARE Classic, Ultralight variants, DESFire, NTAG424, NTAG21x variants with
different version bytes, protected/locked tags, payment cards and access badges
are not supported. Supporting another family requires its own reviewed profile
or adapter and physical evidence; a successful UID read is insufficient.

## Evidence and physical acceptance

Run `android/tools/parity.sh` for legacy Python/Java encoder parity, 1,087
legacy plan states, ten link fault behaviours, history checks and the new
multi-profile command simulator. Run Gradle unit tests/lint/builds as documented
in `android/README.md`. Pure JVM tests additionally pin exact vectors, capacity,
layout-preserving rewrites and write fences.

For each physical model, use Inspect only first. Then the owner explicitly
selects an expendable card and public test link, disables Inspect only, and
presents/removes that card. Check rewrite to another link, already-done,
protection refusal and interrupted-write behaviour. Verify the final URL on a
different phone. Never infer physical success from simulated memory or APK
installation. No device serial, UID, private URL or app preference dump belongs
in a shared report.

Protocol reference: [NXP NTAG213/215/216 datasheet, Rev. 3.2](https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf?pspll=1),
sections 8.5.3, 8.5.5, 8.5.6, 8.5.7 and 10.1 (checked 2026-10-31).
Tables 4–7 define CC sizes and factory data; Table 28 defines exact version
responses. Physical chip capacities differ from the advertised NDEF sizes.
