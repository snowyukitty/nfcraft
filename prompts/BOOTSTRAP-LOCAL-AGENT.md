# nfcraft — initial local-agent execution prompt

You are taking over **nfcraft**, my real, long-lived NFC card project. Act as a hands-on product engineer, implementation lead, test engineer and deployment operator. Work directly in this repository. Review and improve this brief where the actual code or evidence warrants it, then **implement, run, verify and improve the product**. Do not merely rewrite this prompt, return a plan, or build an unrelated replacement scaffold.

## My intent and what is already decided

I own many NTAG215 wooden cards and want to turn them into useful, attractive business/contact cards and other long-lived NFC experiences. I want an app for batch initialization, settings, verification, recovery, inventory and future updates, with useful CLI/MCP access for my local AI agents.

The permanent name is **nfcraft**, lowercase, one word. The folder I opened is the project root; do not create `nfcraft/nfcraft/` as a second repo. A Python package subdirectory named `nfcraft/` already exists inside the root and is intentional. Preserve the downloaded implementation and develop it further.

My primary computer is Windows 11, with WSL available. Detect the OS/shell/interpreter in this session. Prefer a Windows-native process for a USB reader owned by Windows. Reader model, firmware, available NFC phone, long-lived public hostname and cloud destination remain unconfirmed. Do not treat any domain suggested in a past conversation as mine or as an approved publishing target.

The production path is intended to be:

```text
Human operator or agent -> nfcraft -> native PC/SC reader -> one NTAG215
                                   -> local SQLite journal
verified public export -> separate public card site -> contact page/vCard
```

A phone is not a required middleman. A phone writing station is an optional later adapter, not a reason to postpone a working desktop product. AI prepares batches, helps diagnose issues and improves content; deterministic code writes each card. No model call belongs in the per-card loop.

## Start by establishing reality

Read `AGENTS.md`, `START-HERE.zh-TW.md`, `docs/PROJECT-STATE.md`, `README.md`, the architecture, security, hardware, deployment, migration and quality-gate documents. Review the source and Git status; preserve unrelated work and any existing credentials/configuration without revealing their values. If there is no Git repository, initialize a local repository for this project only; do not create a remote repo or push publicly without an approved destination.

Run `scripts/preflight.py`. Create/use a repository-local `.venv`; do not replace my global Python/Node setup or install drivers as a side effect. Core demo startup needs no third-party packages. Run `scripts/verify.py --require-node`, saving fresh logs under an ignored local evidence directory or a sanitized session report. If Node is missing, continue Python work and mark Node checks NOT_RUN until you resolve that toolchain.

Inspect the app with a real local browser. Read the actual errors instead of masking them. Check new-batch creation, bounded approval, mock card placement/removal, distinct IDs, duplicate refusal, interrupted write, explicit same-identity recovery, restart behavior, inventory, profile draft, CSV/manifest export and optional QR export. Do not use automation to approve a physical operation; any automated operator interaction is restricted to a temporary mock-only test workspace.

Create `reports/<local-date>-bootstrap/REPORT.md` recording the initial environment and findings. No credentials, raw production UIDs, private contact content or personal file listings in reports.

## Deliver working slices, not a framework migration

### Slice A — Reliable local nfcraft app

Make the existing app start cleanly on my machine with a clear launch/stop/restart path. Fix demonstrable defects first. Prefer the current Python/SQLite/plain-web architecture unless an observed constraint justifies a documented change. Do not introduce Rust/Tauri/React/Android/queues simply because they were mentioned earlier.

Validate the rename across UI, version output, Python imports, package data, launchers, docs, build metadata and MCP server name. Preserve `nfcctl.py` and the `nfc_*` MCP tool names as documented compatibility aliases unless a tested migration is provided. Detect any legacy `NfcCardOps` workspace and follow the non-destructive migration runbook; never silently start an empty inventory over existing card assignments.

Improve the workbench carefully: clear mode and write-permission indicators, readable status, useful empty/error states, large current-card feedback, keyboard-friendly operation, progress and recovery. Keep the calm, restrained workshop aesthetic. No fabricated scan charts, decorative AI dashboard, unnecessary glass effects, particles or animations. Explain to me in Traditional Chinese; code identifiers and technical docs may remain English. Any localization must include validation/errors and not just the sidebar.

### Slice B — Prove one physical card, then ten

First detect installed PC/SC support and enumerate devices. ACR1552U PICC is a qualification target, **not proven supported hardware**. A reader that reports a UID is not automatically a compatible writer. Read the exact vendor manual for the connected device/firmware; no command transplant from another model without evidence.

Start read-only. Verify UID and chip geometry, memory/protection state, transparent-session behavior, RF/ACK framing, removal/reconnection and exclusive reader ownership. Save sanitized traces with firmware and manual revision. Add regressions for every change to command parsing or protection logic. Never broaden acceptable response patterns just to accept a failing device.

If no usable reader is attached, record `BLOCKED: hardware unavailable` and continue local product/packaging/public-preview work. Do not repeatedly ask me to buy hardware or claim that simulation tests are hardware tests.

Only after a read-only review and my explicit approval, use **one expendable NTAG215** with the experimental write flag and a separately approved bounded batch. Validate URL, byte-for-byte readback, preserved memory, identity and restart/recovery semantics. Then run a ten-card pilot, including real phone reading and QR/vCard verification. I physically place and remove cards. Do not promise a cards-per-minute figure before measurement.

Do not expose permanent locking, password writes, raw APDU, arbitrary erase or unknown-card overwrite as convenience features. Distribution protection is a separate unresolved product decision, not something to enable automatically.

### Slice C — Public card site and real deployment

The local hardware-control app remains local. Deploy **only the separate public Worker**, never the operator API. Prepare/review the existing Cloudflare Worker/D1 source and establish separate preview and production configurations and databases. Run handler tests and actual local Wrangler integration before calling cloud work complete.

Inspect existing project-local configuration and safely identify the intended account. I may have multiple cloud accounts: a successful login or default CLI account is not permission to choose one arbitrarily. Do not print tokens or copy them into this repo. Resolve and pin the Wrangler version against its current official requirements; generate a real lockfile rather than inventing one. Recheck CLI syntax against official documentation.

Use disposable demo data only in local/preview environments. `--allow-demo` must never be a shortcut for production publication. Validate the manifest, show the target account/Worker/database/environment and review the public profile before a remote mutation. Reuse a scoped prior approval if it exists; otherwise ask once for the unresolved destination/approval while continuing unblocked work. Do not perform unrelated DNS changes, replace existing projects, disable authentication or incur unapproved paid services.

For an approved production destination, make a backup/rollback plan, apply reviewed schema/data changes, deploy the intended Worker, configure only the approved long-lived hostname, and verify the **exact URL encoded in a card**, not merely a preview URL or root homepage. Root `/` returning 404 is not a failed card route test. Check a valid route, an unknown route, a suspended route, escaped content, vCard response and methods/security headers from outside the local workstation. Record the account/environment/resource IDs and deployment version privately; include only safe summary data in repo reports.

No automatic sync is implemented in this handoff. A local suspension/profile update is not applied publicly until publication. Add a reliable publication status/diff/acknowledgment feature as a separate tested increment; never claim it already exists. Ensure old revision imports cannot silently overwrite newer public state or merge unrelated workspaces.

### Slice D — Package and operate it sustainably

After the local app works, validate optional Windows desktop/tray packaging. Produce an unsigned local build first if useful and clearly label it; do not claim signing. Test launch, shutdown, files with spaces, non-ASCII paths, restart and workspace persistence on Windows. Use the real `.venv` interpreter in launchers. Keep failure logs accessible without leaking the operator URL. Do not change execution policy or run as administrator to hide a packaging problem.

Maintain the supplied CI/check scripts and a reproducible dependency strategy. Rehearse backup/restore and data migrations on copies. Preserve issued URLs, schema compatibility and public export formats across versions. Update changelog, project state and acceptance evidence each session. Next features should follow user value and measured bottlenecks: publication receipts, inventory search/filter, multi-profile UI, labeling/print workflow, better diagnostics, then a separately secured phone adapter. Public AI chat is not a prerequisite for working cards.

## Quality rules you may not trade away

1. Mock success != hardware success != deployed URL != phone/print QA != ready to distribute.
2. A reservation is durable before the first page mutation; uncertainty never recycles a slug.
3. Recovery checks the exact original assignment and saved partial memory evidence.
4. Agent tools cannot arm hardware or change chip protection. Do not fetch my operator token to get around this.
5. Readback/configuration checks, exclusive ownership and the safe page allowlist stay enabled.
6. Do not expose a local control endpoint to LAN/public Internet, and do not load private memories into the public card site.
7. No unsafe overwrite/reset, mass locking, global toolchain changes, secret commits, unrelated project edits or undocumented data migration.
8. All counts, screenshots, timings and deployment statements must come from real evidence; label missing tests NOT_RUN/BLOCKED.

## How to work with me

Start acting after a brief statement of your first concrete steps. Keep updates short and show meaningful findings as they appear. You may refine this plan, choose implementation details, add tests and fix issues independently within the repo. Optimize for a useful product and reliable execution, not for generating many documents or using every available framework.

Ask questions only when a consequential action requires a value/approval you cannot discover safely. Do not ask again which name I chose or whether I want the project completed. Do not stop all work because a reader, phone, hostname or cloud permission is missing; finish the other slices and state the exact blocked gate.

At the end, leave a working tree with coherent changes and report, in Traditional Chinese: what changed; how I start/stop the app; exact checks that passed/failed/were not run; local/hardware/preview/production status separately; artifacts produced; migration/rollback notes; and the smallest next action that needs me. Save a continuation note so another agent can resume without guessing. Never say "fully deployed" when only the demo started.

**Begin now: inspect this repository and environment, run the baseline, then implement the highest-value unblocked slice.**
