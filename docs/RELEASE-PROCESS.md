# nfcraft — iterative release and compatibility policy

## Each increment

Start with project state, current diff and last report. Reproduce baseline; choose a bounded user outcome; implement with failure/recovery tests; rerun checks; update changelog, state and report. Preserve the owner-facing workflow and all issued identities. Use `prompts/CONTINUE-ITERATION.md` for future sessions.

Versions follow a simple discipline: patch for compatible fixes/packaging/docs; minor for additive product capabilities; explicitly document any breaking API/data/deployment change. A version bump does not imply hardware qualification. Record validation scope separately.

## Stable surfaces

Issued HTTPS URLs/slugs are durable. SQLite schema, public manifest schema, CLI output, MCP names and interpretation of state are contracts. Do not rename payload keys or package the database inside the executable for cosmetic consistency. Backward-compatible CLI aliases are deliberate. New public namespaces require a migration strategy, not global search/replace.

## Release candidate procedure

1. Freeze the intended diff and record source commit/version. Use platform-resolved lockfiles for optional build tooling; include license/security review of new dependencies.
2. Back up the authoritative local journal and any affected public database. Restore them into isolated test targets; verify counts, identities, audit and public routes. Do not use production state for destructive tests.
3. Run hardware-free tests and actual target-OS/browser/package checks. Run hardware/phone tests when that support is claimed. Record FAIL/NOT_RUN/BLOCKED explicitly.
4. Deploy an approved preview before production. Review schema/data diff, profile and environment. Only deploy to the scoped destination. Check the encoded URLs after deployment, not just a homepage.
5. Build the deliverable without tokens, `.venv`, journals, `virtual-tags`, production manifests, private CSVs, logs with capability URLs, vendor PDFs or font files. Create file hashes and release notes. Do not publish to GitHub/package registries without a chosen destination/visibility.

## Migration and rollback

Use versioned, tested data migrations and a documented minimum reader version. Prefer additive changes. Rehearse both a clean install and an upgrade from the prior real schema. An import/migration must preserve every UID-to-slug assignment and uncertain outcome.

Code rollback and data rollback are distinct. Once new cards have been written or new public revisions published, restoring an older database may lose assignments or reactivate obsolete routes. Do not blindly restore it. Pause operations, reconcile newer identities/attempts, and choose a compatible code/forward-fix path. Preserve issued URLs even when changing the public page implementation.

An irreversible tag operation is not part of software rollback. Never lock/erase/rewrite cards to compensate for a failed deploy. If a release cannot be rolled back safely, state the boundary before deploying and keep a forward-repair plan.

## Evidence persistence

Keep this delivery's historical evidence unchanged. New runs go in ignored `.local/verification` and sanitized `reports/<date>-<session>/`. Reports include actual versions, commands, outcomes, remaining gates and the next bounded task. Store private deployment IDs/card evidence outside public report history as needed. Do not turn old mocks into fake current screenshots or copy test totals from a previous report without rerunning.
