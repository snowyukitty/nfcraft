# Public card publishing

The authoritative procedure is now **`DEPLOYMENT.md`, sections C–F**. It includes explicit preview/production configs, separate D1 targets, manifest review, external checks and rollback.

This handoff has not deployed any cloud resources. Public Worker handler tests use a mocked D1 interface. Local verification, export, SQL generation, deployment and phone QA are separate states. Suspending a card or editing a profile locally does not automatically update the public service.

The Worker serves `/c/<22-character-slug>` and `/c/<slug>/contact.vcf`; `/` is deliberately not a health check. Public manifests exclude raw UIDs, while inventory CSV and database backups are private. A manifest checksum detects accidental edits, not authenticity or a physical tap.
