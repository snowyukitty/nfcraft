# nfcraft

[English / 繁體中文 app guide](nfcraft/web/guide.html) · [Desktop repair report](reports/2026-09-06-desktop-launch/REPORT.md) · [Phone writer reliability report](reports/2026-09-16-phone-writer-reliability/REPORT.md)

Open the guide locally, or choose **Guide / 使用說明** inside the app. The **nfcraft** desktop shortcut directly opens `nfcraft-desktop.exe` as a normal Windows GUI app; PowerShell is not used at launch. The second shortcut opens the offline guide. GitHub displays HTML source; this is not a hosted public site.

![nfcraft identity](nfcraft/web/icons/icon-192.png)

**A small, local-first workshop for your NTAG215 business cards.**

Two programs share one encoder. The desktop workshop drives a USB PC/SC reader and keeps the journal; [Card Writer](android/README.md) puts one card's destination on a phone with no PC at all. What they write is byte-for-byte identical, and a check proves it on every commit.

Prepare a batch with an AI agent. Approve it in the app. Present one card at a time. Keep every assignment and uncertain outcome in a durable journal.

**Version 0.2.2 — Card workshop. A working Windows app, still awaiting physical-reader qualification.**

**Owner: start with [START-HERE.zh-TW.md](START-HERE.zh-TW.md).** Agents: read [AGENTS.md](AGENTS.md) and the full [bootstrap execution prompt](prompts/BOOTSTRAP-LOCAL-AGENT.md). This archive is complete; the old NFC Card Ops download is not required.

**New in 0.2.0:** searchable card library with filters and pagination, card detail/evidence views, live recipient preview using the public site's renderer, and public export review that refuses stale content. Review explicitly warns about shared-profile updates beyond selected routes. **118 Python tests and 16 Worker tests pass.** The unsigned Windows app is in `dist/nfcraft`; see the [current milestone report](reports/2026-09-06-library/REPORT.md) and [Windows bootstrap history](reports/2026-09-06-bootstrap/REPORT.md). Hardware, phone QA and cloud deployment remain separate gates.

This release adds safer legacy-data handling, stricter public exports, an occupied-write-region guard, repeatable local checks and a deployment/iteration handoff. [Current state](docs/PROJECT-STATE.md) · [Changelog](CHANGELOG.md) · [Deployment](docs/DEPLOYMENT.md) · [Continue next version](prompts/CONTINUE-ITERATION.md)

[繁體中文快速開始](docs/QUICKSTART.zh-TW.md) · [Architecture](docs/ARCHITECTURE.md) · [Hardware qualification](docs/HARDWARE.md) · [Agent handoff](AGENTS.md) · [Test evidence](docs/TEST-REPORT.md)

## What you are receiving

| Component | Status in this archive |
|---|---|
| Local browser app: workbench, inventory, public profile, audit, device information | Implemented and exercised against the mock engine |
| Persistent virtual NTAG215 cards and interruption/recovery scenarios | Implemented; no NFC hardware required |
| NDEF encoder, guarded write plan, reservation journal, byte-for-byte readback | Implemented and tested with simulated cards |
| Agent-safe CLI and stdio MCP facade | Implemented; no AI API key or model subscription required by this app |
| ACS ACR1552U PC/SC adapter | Experimental source; **no physical tests**; read-only by default |
| Desktop window / tray integration | Unsigned Windows portable build; browser/native lifecycle tested on this host; clean-machine and tray-menu visual QA outstanding |
| Public card page and contact.vcf | Shared recipient renderer; real local Worker/D1 and narrow-browser tests pass; **not remotely deployed** |
| Android phone writer (`android/`) | Implemented as a separate single-card tool; one physical card written and verified, no batch station |
| Permanent locking, password changes, arbitrary rewrites | Deliberately absent |
| Signed installer, automatic cloud synchronization, multilingual UI, public AI chat | Not included in v0.1 |

The main app is English. Chinese setup documentation is included. This source repository also produces an ignored local Windows portable build; keep the complete `dist/nfcraft` folder with its executable. Windows 11 has been validated locally. NFC reader, firmware and hostname still need qualification/approval. The repository does not assume ownership of any personal domain.

## Try it now, with no NFC reader

Install Python 3.11 or later, extract the archive, and open a terminal in this directory:

```sh
python run.py
```

On Windows, `Start nfcraft.cmd` invokes the same command and prefers a repo-local `.venv`. `Start Demo.cmd` remains an alias. No third-party Python package, Node, cloud account or AI key is needed for the core demo. The launcher starts a loopback-only server and opens a private operator URL in your browser. Keep the terminal running; Ctrl+C stops it.

1. In **Public profile**, replace the demo name and introduction. This saves a local draft, not a public page.
2. In **Workbench**, create a batch of 10. The default `https://tap.example.com` is deliberately a **simulation-only** destination.
3. Click **Arm this batch**, set the maximum attempts and expiry (15–600 seconds), and type `ARM <exact batch name>`. Approval ends at the first limit reached. Recovery always targets one original identity.
4. Click **Place virtual card**, wait for the verified result, then **Remove**. Repeat.
5. Try **Interrupted write**. The assignment is quarantined. In **Card inventory**, use **Review & recover**, approve again, and observe that it retains its original identity and URL.

A successful simulation does not read or write any of your wooden cards. The virtual cards persist in your local workspace, so you can re-present a card or restart the app without losing its assignment.

### Optional extras

Use a virtual environment for optional dependencies:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[qr]"
```

The `qr` extra enables **QR SVG** downloads. `hardware` installs pyscard. `desktop` installs pywebview, pystray and Pillow. Optional dependency installation requires package access; versions are constrained ranges, not a reproducible lockfile.

```sh
python -m pip install -e ".[desktop,qr]"
python run.py --desktop
# Optional Windows-oriented tray controls:
python run.py --tray
```

Desktop/tray packaging still needs local validation. `Start Desktop.cmd` falls back to the browser when the desktop extra is absent. Closing a browser tab does not stop the daemon. Do not leave a workstation armed unattended.

## Real USB hardware — read this before enabling writes

Recommended qualification target: **ACS ACR1552U, PICC reader/writer interface**. A PC/SC reader that can report a UID is not automatically a compatible Type 2 memory writer. Do not choose a SAM interface, 125 kHz reader, contact-only reader or keyboard-only UID device.

```sh
python -m pip install -e ".[hardware]"
python nfcraftctl.py --mode hardware doctor
python run.py --mode hardware --reader "EXACT PICC NAME FROM DOCTOR"
```

Stop the demo first, or give the hardware app a different `--port` (for example 47822).

This starts in **read-only mode**. Use **Inspect card**. Unknown geometry, changed capability container, locks, password restrictions, mirroring and unexpected reader responses are refused. The adapter's native transparent-command path is **not hardware-qualified** and may require changes for your reader/firmware. A manufacturer's compatibility claim is not evidence that this implementation has been tested.

After inspecting the source and completing the read-only checks in [HARDWARE.md](docs/HARDWARE.md), an explicitly experimental, sacrificial-card write can be enabled:

```sh
python run.py --mode hardware --reader "EXACT PICC NAME FROM DOCTOR" --allow-experimental-hardware-writes
```

This flag does not arm the reader. A human must still approve a bounded batch in the app. Use your own real public HTTPS hostname, not the sample domain. Expect failure to stop the run rather than trigger a speculative fallback command. Do not hand cards to others until their URL is published and independently checked on phones.

## Give an agent useful tools, not raw hardware commands

The app must be running in the same workspace. Open a second terminal:

```sh
python nfcraftctl.py status
python nfcraftctl.py batch-create --name "Pilot 01" --count 10 --base https://tap.example.com
python nfcraftctl.py inspect
python nfcraftctl.py pause
python nfcraftctl.py manifest
python nfcraftctl.py audit
python nfcraftctl.py mcp
```

Commands default to the **demo** workspace. For hardware, put `--mode hardware` before the subcommand. With a custom workspace root, also pass `--data-dir` before the subcommand.

MCP tools: `nfc_status`, `nfc_batch_create`, `nfc_inspect`, `nfc_pause`, `nfc_export_manifest`, `nfc_audit_verify`. Example client configuration is in `examples/mcp-config.json`. The facade implements a small stdio tool subset; it has not been exercised inside every Codex/Claude client.

Agents cannot arm a run, change the public profile, send raw APDUs, overwrite unknown cards, modify protection or permanently lock a card through these tools. They can prepare a batch and report results. The deterministic worker then processes the human-approved batch without a model call per card.

This is an API capability boundary, **not isolation from an unrestricted local agent running as your OS user**. Such an agent could edit the code, read browser state or drive the UI. See [SECURITY.md](SECURITY.md).

## Publish a usable business card

In **Card inventory**, search by batch, label, URL or private UID; combine batch/write-result/route-intent filters. Results show 25 rows per page. CSV and **Review public export** use all matching rows across pages. Public export excludes unverified cards. Click a card label for identity and separate write/export/public-availability/phone-QA facts.

In **Public profile**, preview edits before saving; the preview stays local and its actions are disabled. **Review public export** shows saved public fields, destinations, enabled/suspended routes and omitted unverified matches. Download validates that the reviewed content is still current. If it changed, review again. Profiles are shared: importing a changed profile can affect public cards outside the filtered route selection. No automatic cloud sync or publication receipt is implemented.

The tag contains one canonical HTTPS NDEF URI with a random 128-bit route identifier. The public Worker serves the contact page and a downloadable vCard. Updating the public profile does not require physically rewriting the tag.

Publication is intentionally separate:

```text
Local reservation → tag written → readback verified
                                      ↓
                              Export public manifest
                                      ↓
                        Review → deploy Worker / D1
                                      ↓
                        Phone-test URL + vCard + QR
                                      ↓
                                  Hand out card
```

The app never calls local verification “publicly live.” Cloud publication/phone QA/issuance are not tracked automatically in this prototype. Suspending a route in the app changes local publication intent; **export and deploy again** to change the public response. An offline write cannot make an undeployed URL work.

Follow [PUBLISHING.md](docs/PUBLISHING.md). Public manifests exclude raw UIDs; inventory CSV and journal backups contain them and should remain private. Export is not deployment. No DNS record or remote database was created for you.

## Repository map

```text
nfcraft/
  engine.py          single-writer orchestration and bounded approvals
  store.py           SQLite journal, durable reservations, audit, export
  ndef.py            strict HTTPS URI codec and restricted page plan
  adapters/          persistent mock and experimental ACR1552U adapter
  server.py          authenticated loopback UI/API
  cli.py, mcp.py      agent-safe control of the same running daemon
  web/               no-build HTML/CSS/JavaScript app
  desktop.py         optional window/tray support
cloudflare/          public Worker, D1 schema and handler tests
scripts/             preflight, verification, demo smoke, legacy import, SQL export, Windows build
examples/            MCP client config and suggested agent prompt
tests/               hardware-independent Python tests
docs/                architecture, runbooks, limitations, research, test evidence
android/             Card Writer, the phone-only single-card rewrite tool
```

## Test and extend

```sh
python -m unittest discover -s tests -v
node --check nfcraft/web/app.js
node --test cloudflare/worker.test.mjs
# Or run all supplied checks and save evidence:
python scripts/verify.py --require-node
```

Node is only needed for public Worker tests, not for the local app. The supplied test report distinguishes simulation, local HTTP, browser rendering, real NFC and deployment. To continue development, start with `AGENTS.md` and `docs/ROADMAP.md` rather than replacing the safety gates.

Legacy `NfcCardOps` journals are detected before silently creating an empty default workspace. Follow [MIGRATION.md](docs/MIGRATION.md); do not delete old state to get past a warning.

Default data location: `%LOCALAPPDATA%\nfcraft\demo` on Windows; `~/nfcraft/demo` elsewhere. Hardware uses a separate `hardware` folder. `--data-dir PATH` changes the root but retains that separation. SQLite is **not encrypted**; protect your OS account and backups. Never delete a physical workspace simply to make an already-assigned card look new.

MIT license for this repository's original code. Optional dependencies have their own licenses. No third-party font files or vendor PDFs are bundled.

## Agent and data compatibility

Use `nfcraftctl.py` / installed `nfcraftctl` for new integrations. `nfcctl.py`, installed `nfcctl` and existing `nfc_*` MCP tools remain deliberate compatibility aliases. MCP server identity is `nfcraft`. Neither the local journal nor the public manifest schema changes for this rename.
