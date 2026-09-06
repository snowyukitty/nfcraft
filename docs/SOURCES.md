# Research references

Research checked on 2026-09-05. Links are primary product/platform documentation unless explicitly labeled otherwise. Vendor capability statements are not tests of this source repository.

## NFC tag and memory

- NXP NTAG213/215/216 product: https://www.nxp.com/products/NTAG213_215_216
- NXP data sheet: https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf
  - Memory organization, NTAG215 capability container and delivery contents, GET_VERSION, READ/WRITE, dynamic/static locks and configuration. Page images were inspected for the memory/configuration/READ tables. NTAG215 physical user memory is 504 bytes; factory CC advertises 496 bytes to the NDEF mapping.
- NXP TagInfo: https://www.nxp.com/design/design-center/software/rfid-developer-resources/the-nfc-taginfo-app-by-nxp%3ANFC-TAGINFO

## Reader

- ACS ACR1552U product/specifications: https://www.acs.com.hk/en/products/575/acr1552u-usb-nfc-reader-iv/
- ACS ACR122U end-of-life notice: https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/
- ACS ACR1552U API manual download, revision 1.07: https://www.acs.com.hk/download-manual/13474/REF-ACR1552U-Series-1.07.pdf
  - The download endpoint was surfaced but full PDF retrieval/parsing did not succeed in this build environment. Fetch and review the correct revision locally before qualifying the driver; do not regard this reference list as proof the entire API manual was validated.
- NXP Community discussion of ACR1552U transparent-mode READ_SIG behavior: https://community.nxp.com/t5/NFC/NFC-NTAG213-READ-SIG-Originality-Signature-Verification-Using/m-p/1890732
  - This is a user report hosted by NXP, not a normative ACS protocol specification. It motivates checking transparent session/layer selection and response wrapping; the app does not implement originality-signature authentication.

## Computer and phone platforms

- pyscard user guide: https://pyscard.sourceforge.io/user-guide.html
- pyscard exception API: https://pyscard.sourceforge.io/apidocs/smartcard.Exceptions.CardConnectionException.html
- Chrome Web NFC capabilities and limitations: https://developer.chrome.com/docs/capabilities/nfc
  - Android Chrome, NDEF-only access, secure context/permission constraints; no raw NFC-A commands for protection-page inspection.
- Android advanced NFC: https://developer.android.com/develop/connectivity/nfc/advanced-nfc
- Android NfcAdapter: https://developer.android.com/reference/android/nfc/NfcAdapter
- Windows/WSL USB attachment: https://learn.microsoft.com/en-us/windows/wsl/connect-usb
- Apple background NFC reading: https://developer.apple.com/documentation/corenfc/adding-support-for-background-tag-reading
  - Phone compatibility still needs testing on the user's actual devices. An operating-system capability is not proof the wooden card's antenna performs well.

## App and public service

- MCP stdio transport specification: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- pywebview usage: https://pywebview.flowrl.com/guide/usage.html
- pystray usage: https://pystray.readthedocs.io/en/latest/usage.html
- Cloudflare D1 getting started: https://developers.cloudflare.com/d1/get-started/
- Cloudflare D1 local development: https://developers.cloudflare.com/d1/best-practices/local-development/
- Cloudflare D1 CLI commands: https://developers.cloudflare.com/d1/wrangler-commands/

No vendor PDF, proprietary SDK, font file or driver binary is bundled. The physical adapter is unqualified; see HARDWARE.md for the evidence still required.


## 0.1.1 handoff references (checked 2026-09-05)

- Python SQLite backup: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup
- Cloudflare D1 getting started: https://developers.cloudflare.com/d1/get-started/
- D1 migrations: https://developers.cloudflare.com/d1/reference/migrations/
- Wrangler environments: https://developers.cloudflare.com/workers/wrangler/environments/
- Chrome Web NFC (NDEF scope): https://developer.chrome.com/docs/capabilities/nfc
- MCP implemented older transport contract: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- Newer MCP material to assess during client integration: https://modelcontextprotocol.io/specification/2026-07-28
- Supplied CI action documentation: https://github.com/actions/checkout/tree/v4 ; https://github.com/actions/setup-python/tree/v5 ; https://github.com/actions/setup-node/tree/v4

This handoff retains its existing negotiated MCP version set; it does not claim support for every newer specification. Major action refs are not immutable dependency pins. Platform docs must be rechecked at execution time. None of these sources substitutes for real-reader, target-Windows or deployed-service tests.
