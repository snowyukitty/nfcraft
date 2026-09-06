# Security and safety boundaries

## Protect the card before improving convenience

This is a public business-card system, not authentication, payment, access control or anti-counterfeit infrastructure. NTAG215 UIDs and URL payloads can be observed/copied. The application's random slug identifies a route; it does not authenticate the holder. Anyone with a shared URL can visit it without physically touching a card.

An unlocked tag remains rewritable by another NFC writer in physical proximity. Preventing the agent from changing lock bits does **not** make the issued card tamper-resistant. Before broader distribution, decide and validate a separate write-protection/sealing process after the final URL is proven stable. This release does not implement or track that process; keep the initial pilot rewritable for diagnosis, rather than treating it as a finished tamper-resistant deployment.

There is no permanent-lock or password feature in this release. Unknown, locked, protected, mirrored or noncanonical tags are refused. The physical adapter is experimental and all writes require an explicit launch flag plus an operator-approved lease. Never overwrite a tag whose provenance you have not established.

EEPROM and SQLite do not form a transaction. A write error can mean the write happened partially or even fully. The engine journals before I/O, records uncertainty, re-reads and compares data, and retains assignments. This is recovery-oriented orchestration, not atomic hardware rollback. Recovery accepts only whole pages attributable to the saved original and plan; a torn or unrelated page requires separate diagnosis.

## Local API

The server binds only 127.0.0.1. API requests require a random bearer token; operator and agent capabilities are separate. Host and Origin are checked, cross-site fetches are refused, and CORS is not enabled. The operator token is sent in the launch URL fragment and retained in browser session storage; it is removed from the address bar after startup. The agent runtime file contains only the less-privileged token. Closing the app invalidates tokens on restart.

These protections are not a boundary against a malicious same-user agent, an administrator, a hostile browser extension or modified application code. An unrestricted local coding agent can bypass application policy by modifying the application or controlling the operator UI. Keep your trusted operator environment separate from untrusted execution when a stronger boundary is required. Do not relay the operator URL through chat, include it in screenshots or expose the API over LAN.

No API is provided for uploading files, arbitrary shell commands, arbitrary network requests or raw memory writes. Data read from NFC or entered into profiles is data, not instructions to an agent. The public Worker has no local-agent, admin, email or calendar connector.

## Stored data

Raw UIDs, memory snapshots, URLs and profile drafts are stored locally. SQLite is plaintext. Newly controlled POSIX workspace directories use 0700; the agent runtime file is created with 0600. Windows relies on the user's inherited profile ACLs; no custom Windows ACL hardening or database encryption is implemented. Inventory CSV and backup files are private operational artifacts.

The public manifest contains verified route slugs, URLs and approved-to-export profile content, but excludes UIDs and raw memory dumps. Its SHA-256 is an integrity checksum, not a signature or attestation. The SQL converter consumes a trusted local export; inspect it before importing. A simulation marker is not proof of physical testing and can be edited by a privileged user.

The audit journal is hash chained. Ordinary edits can be detected; an attacker who rewrites the entire chain or deletes its suffix cannot be reliably detected without a trusted external checkpoint. Arming refuses an already-broken chain. No claim of tamper-proof or regulatory-grade auditing is made.

## Public service

No application-level analytics, cookies, public chatbot or lead form are implemented. The hosting provider may still process infrastructure logs and network metadata; review hosting settings before making privacy promises. Profile HTML is escaped, website links allow HTTPS only, and vCard fields escape line/field separators. Remote deployment requires independent review of the hostname, TLS, publication data, provider credentials and profile accuracy.

## Reporting an issue

No hosted security inbox is configured. Record local findings without public UIDs, operator tokens or private profile details, stop the run, and involve the repository owner. Public issue trackers should receive a sanitized reproduction, not a workspace backup.


## 0.1.1 handoff hardening

The machine client does not use environment-configured HTTP proxies or follow redirects. Export SQL generation validates its public schema, checksum, explicit simulation marker, slugs and public-only fields. Those checks do not authenticate a manifest author or prove physical card origin. Legacy import retains original identity data and does not transfer runtime capability tokens; old/new copied workspaces must not operate independently. Empty NDEF content does not authorize overwriting occupied bytes inside the planned write region.
