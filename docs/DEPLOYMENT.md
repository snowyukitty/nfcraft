# nfcraft — deployment runbook

There are **four different deployments/acceptance paths**. Completing one does not complete the others. This handoff has not changed the owner's machine, cloud account or NFC cards.

| Path | Target | Evidence required |
|---|---|---|
| Local app | Owner's computer, loopback only | Start/stop/restart, browser workflow, safe persistent data |
| Desktop distribution | Windows build artifact | Clean-machine launch, packaged assets/dependencies, persistence; signing status explicit |
| Public preview | Disposable local/remote Worker + separate D1 | Real handler/D1 integration and route/vCard checks with demo data |
| Public production | Approved durable origin, approved Worker/D1 | Exact encoded URLs work externally; reviewed content/data; backup/rollback and phone QA |

## A. Local setup

Use the existing repository, not a second scaffold. Check whether a `.venv` and legacy/current workspaces already exist. Do not overwrite `.git`, local settings or card journals. On Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe scripts\preflight.py
.\.venv\Scripts\python.exe scripts\verify.py --require-node
.\.venv\Scripts\python.exe run.py
```

Create the venv only if absent; do not recreate a working environment. `Start nfcraft.cmd` uses it automatically. `scripts/bootstrap.ps1` is an optional reviewed convenience script; if the machine blocks PowerShell scripts, use the explicit commands rather than weakening execution policy. Core demo startup has no optional-package requirement. Install only needed extras into the venv after review, for example `-m pip install -e ".[qr]"`.

Start in demo. Verify browser operation, not just an HTTP status. Stop with Ctrl+C; a closed tab does not stop the engine. Default data is `%LOCALAPPDATA%\nfcraft\demo`, or `~/nfcraft/demo` when LOCALAPPDATA is absent. Hardware uses a different `hardware` subdirectory. Back up before migration. An explicit `--data-dir` specifies a **root**, to which the app appends the mode.

A WSL agent may edit the repo, but a Windows-owned USB reader should be driven by Windows Python. Resolve Windows/WSL path translations explicitly and test the CLI connection. Do not make the local operator service public to solve cross-OS networking.

## B. Reader qualification and Windows package

Follow `HARDWARE.md` and `QUALITY-GATES.md` first. Installing pyscard is not installing/qualifying a reader. Do not modify Windows services, drivers or USB forwarding without a reviewed need and explicit approval. Hardware mode remains read-only by default.

After local validation, the Windows build recipe is:

```powershell
# Review before executing. This script is not claimed tested on Windows here.
.\scripts\build-windows.ps1 -InstallDependencies
```

It uses the repo venv and creates an **unsigned** PyInstaller `dist\nfcraft` directory. Resolve/pin dependencies for the target platform, test on a clean Windows user profile, and capture the actual output and hash. A file named `.exe` is not proof of a signed installer, antivirus compatibility, desktop tray correctness or hardware support.

## C. Public-site tooling and destination

The public Worker has no control API, no reader bridge, no AI calls and no private profile data. Local operator tokens and SQLite journals must never be bundled or uploaded. Use the existing `cloudflare/worker.mjs`, not the loopback server.

Resolve Wrangler against its current official engine requirements and pin the tested version locally in `cloudflare/package.json`/lockfile. Use local installed tooling thereafter; do not use an unrecorded global version or claim an invented lockfile was resolved. `package.json` initially contains test scripts only.

The local agent must identify the **intended** Cloudflare account and environment from approved project configuration or a specific owner decision. An authenticated CLI session can point at the wrong account. Request a scoped approval if the destination is unresolved; do not block other local tasks.

Use `wrangler.example.toml` for preview and `wrangler.production.example.toml` for production. Copy them to ignored `wrangler.preview.toml` and `wrangler.production.toml`. Replace account and database placeholders only with approved values. Different environments must not share their D1 database. Cloudflare documents that environment bindings such as D1 are non-inheritable; explicitly configure each selected target. See source references below.

No implicit production default: every command below names a config. Database creation is a remote mutation and requires the destination decision. For example, create `nfcraft-preview` or `nfcraft-production` **only after** confirming the account and need; do not copy a database ID from unrelated projects.

## D. Local/preview integration before production

From the repo root, export a disposable demo manifest using the app or CLI and convert it to SQL for review:

```powershell
.\.venv\Scripts\python.exe nfcraftctl.py manifest
# Save the manifest as UTF-8 JSON, preferably with the app's export action.
.\.venv\Scripts\python.exe scripts\manifest_to_sql.py .local\preview-manifest.json --output cloudflare\preview-routes.sql --allow-demo
```

The converter validates schema/checksum/fields/URLs and refuses replacing an existing output. An explicit simulation marker is not a hardware attestation. Never manually remove `simulated` or recompute a checksum to turn demo data into production data.

From `cloudflare/`, using reviewed preview configuration:

```sh
npx wrangler d1 execute nfcraft-preview --config wrangler.preview.toml --local --file schema.sql
npx wrangler d1 execute nfcraft-preview --config wrangler.preview.toml --local --file preview-routes.sql
npx wrangler dev --config wrangler.preview.toml
```

These are runbook commands; they have not been executed in this handoff. Check current CLI syntax before use. Visit `/c/<actual-exported-slug>` and `/c/<slug>/contact.vcf` on the preview origin. The Worker intentionally has no root homepage. A demo manifest using example.com is tested at its path on preview, not at that example-domain origin.

Only an approved remote preview should use `--remote` or `wrangler deploy`. Never import demo rows into production. Review public content before a remote preview too; "preview" still means accessible to others unless explicitly protected.

## E. Production publication

Before mutation, show a deployment plan: account label, environment, Worker, D1 ID/name, intended hostname, public profile fields, card count, file hashes, schema/data diff and rollback. No token values. Confirm the hostname is long-lived and owner-controlled before encoding it on physical cards.

Back up the selected production D1 and record its restore procedure. Do not use a source-file rollback as a substitute for database rollback. Generate a fresh **hardware-workspace** public manifest after local readback, then review/convert it without `--allow-demo`.

```sh
# Run from cloudflare/, only for the explicitly approved production target.
npx wrangler d1 execute nfcraft-production --config wrangler.production.toml --remote --file schema.sql
npx wrangler d1 execute nfcraft-production --config wrangler.production.toml --remote --file production-routes.sql
npx wrangler deploy --config wrangler.production.toml
```

These steps mutate the remote database and public service. If the selected resources are existing/live, first validate schema compatibility and the precise import plan. The current upsert export is for one authoritative workspace. It has no multi-station namespace or automatic conflict-resolution system. See `IMPLEMENTATION-PLAN.md` before enabling automated publication.

Configure only the approved hostname. Then check from outside the workstation: exact encoded HTTPS URL, correct profile, TLS, vCard download/import, 404 for unknown card, 410 for suspension, method/security behavior and no private fields in output. Record actual URL tests and deployment version. Do not claim success solely from Wrangler's exit code.

## F. Updates and rollback

Local profile edits and suspension are publication intent only. Re-export/review/import to change the public site. The app does not automatically synchronize or prove availability. Keep exported hashes, publication receipt and independent checks per release; avoid publicly archiving personal contact details.

For failures: pause any new issuance, preserve local card identities, restore compatible Worker code and approved database state, and verify the same encoded URLs. **Never rewrite issued cards or recycle slugs merely to roll back a web deployment.** Follow `RELEASE-PROCESS.md` for a complete state-aware rollback.

## Official references checked for this handoff

- Cloudflare D1 getting started: https://developers.cloudflare.com/d1/get-started/
- D1 migrations: https://developers.cloudflare.com/d1/reference/migrations/
- Wrangler environments and non-inheritable bindings: https://developers.cloudflare.com/workers/wrangler/environments/

Checked 2026-09-05. Commands/configuration must be rechecked against the installed version at execution time. These references explain the platform; they are not evidence of a deployment performed for this project.
