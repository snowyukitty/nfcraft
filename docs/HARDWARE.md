# Hardware qualification runbook

**Status: zero physical-reader tests for this release.** The ACR1552U adapter is experimental code, not a compatibility certification. Do not distribute cards based only on the test suite.

## Selecting the station

A desktop needs NFC hardware. The target path is a native OS PC/SC service → USB ACS ACR1552U PICC interface → one NTAG215. A laptop with built-in NFC could work only if its reader exposes the required command path; generic NFC or smart-card branding is insufficient. A 125 kHz reader, contact-only card reader, SAM slot or UID keyboard reader is not interchangeable.

ACS documents ACR1552U reader/writer mode, CCID and PC/SC support. That makes it a candidate for qualification, not a tested match to this adapter. ACR122U is now labeled end-of-life by its manufacturer; it is not the preferred new-deployment target. Existing other readers can be supported by a separately verified adapter, not by altering a model-name check.

For Windows, run the daemon with native Windows Python and the Windows PC/SC stack. Running an agent in WSL does not require moving the USB reader into WSL. A Windows stdio CLI process is the straightforward bridge when the client can launch one. USB passthrough and cross-OS networking are separate setup tasks, not assumed to work transparently. Linux/macOS PC/SC availability is platform-dependent and has not been tested with physical hardware here.

## Gate A: record the exact environment

Record OS/version, CPU architecture, Python/pyscard versions, reader model and serial/firmware, vendor driver package, exact PICC reader name, wooden-card supplier/batch, and whether other NFC tools are installed/running. Do not mix SAM and PICC entries. Keep only one card within the antenna work area and remove other readers/card stacks while qualifying.

```sh
python -m pip install -e ".[hardware]"
python nfcraftctl.py --mode hardware doctor
python run.py --mode hardware --reader "EXACT READER NAME"
```

Inspect with an expendable sample tag. Save the read-only output locally. The application checks canonical NTAG215 GET_VERSION `00 04 04 02 01 00 11 03`, CC `E1 10 3E 00`, UID/BCC consistency and relevant locks/configuration. These checks reject unexpected behavior but do not verify cryptographic originality. A clone can copy such evidence.

## Gate B: qualify the reader protocol without EEPROM writes

The implementation uses ACS PC/SC transparent exchange to send native Type 2 commands. It starts a transparent session, selects ISO14443-A layer 3, parses response objects, then performs GET_VERSION and READ. Native responses and ACKs must be interpreted using the **exact vendor manual/firmware**, not by stripping a fixed number of bytes from every response.

Review these implementation assumptions before enabling writes:

- Start/end session and protocol-switch APDU formatting are accepted by the selected firmware.
- Response C0 status object structure, optional 0x96 reception information and 0x97 payload semantics match the parser.
- GET_VERSION yields exactly eight expected bytes; READ yields sixteen memory bytes; no reader wrapper bytes are treated as tag memory.
- READ of page 0 validates both UID block checks; READ of 0x82 is attempted only after an exact NTAG215 geometry match.
- A WRITE acknowledgment may have a four-bit representation. The prototype expects a one-byte 0x0A result and conservatively rejects nonzero reception info. **Validate this interpretation; it can be too strict for a firmware that encodes valid-bit information in 0x96. Do not enable writes by guessing.**
- Card-present polling, clean removal, reader unplug/replug, exclusive-access contention and reader resets are tested independently. Only specific PC/SC absence statuses are treated as an empty reader. An unexplained RF/reader error stops the run rather than silently acting like removal.

A complete ACR1552U manual was not retrievable as parsed text in the build environment. The official manual download, product page, NXP datasheet and source references are listed in SOURCES.md. Obtain the vendor PDF for the actual unit and review the experimental APDU sequence before physical use. Add sanitized real response fixtures and associated tests when available. A synthetic parser test is not this gate.

## Gate C: one expendable card

Use only a card you own and can sacrifice. Confirm the intended hostname, public profile and NDEF payload. No lock/password setting is part of this pilot. Start with the explicit launch flag:

```sh
python run.py --mode hardware --reader "EXACT READER NAME" --allow-experimental-hardware-writes
```

Create a **one-card** batch with a real public hostname you control. An accepted hostname is not proof of ownership or availability; verify those yourself. Remove the card, approve the run in the UI, then present it flat at the tested antenna position. Compare the full readback with an independent NFC inspection tool. Check that UID, CC, locks and configuration are unchanged.

Do not continue after an unexpected response. Read the journal, keep the reserved identity, and investigate. Do not select a new empty workspace to bypass duplicate protection.

## Gate D: ten-card pilot

Use ten final-form wooden cards, not merely bare inlays. Keep separate physical piles for **blank**, **written / pending public QA**, and **quarantined**. Mark each card with its batch/ordinal or a temporary label so it cannot be confused with its neighbors. A simple nonmetal positioning guide can help.

Test ordinary insertion/removal, holding the same card in place, re-presenting a known card, a prewritten card, a locked card, and an unsupported chip. On an expendable card, test interruption during body writing and after the final length commit. Verify that an uncertain card retains the original URL and cannot silently allocate a second identity.

Publish verified routes and test each on at least an NFC-capable Android phone and a compatible iPhone. Confirm URL opening, correct profile, vCard import and printed/engraved QR fallback. Test after final engraving/printing/coating. Keep tag antenna placement and nearby metal in mind. Do not leave a stack of tags in the reader field and assume anticollision provides a safe bulk-production selection rule.

## Gate E: measure, then scale

No cards-per-minute promise is made. Measure real elapsed time from presentation to verification, time spent feeding/removing cards, p50/p95 cycle time, retries, quarantines, and successful public phone QA. Report OS/firmware/materials with the result. The app's **SIMULATED ms** field is not a throughput benchmark.

Before unattended or multi-station use, add a persisted qualification profile, reader-specific removal evidence, operating-system integration tests, signed packaging, monitoring and a complete publishing/issuance state model. A human-assisted single-reader workshop is the scope of this prototype.

## Acceptance record

Use `examples/PILOT-ACCEPTANCE.md`. Until it contains actual evidence, keep `hardware_qualified: false`. The current app intentionally never turns that field green.
