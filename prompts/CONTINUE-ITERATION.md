# nfcraft — resume and improve the next version

Continue the existing **nfcraft** project in this folder. Do not regenerate it from scratch.

Latest checkpoint (2026-11-01): Android 0.5.1 / code 8 with an IconFlow
Halloween sleeve and exact NTAG213/215/216 profiles. See
`reports/2026-11-01-session-checkpoint/REPORT.md` and the latest Git status/log.
The owner requested committing/pushing the reviewed checkpoint to GitHub.
The prior successful clean install and exact installed-APK hash are recorded in
`reports/2026-10-31-halloween-install/REPORT.md`. Old 0.2.0/settings were removed
with explicit permission; preserve the new installation. Do not uninstall again.

The phone is now disconnected; reconnect/unlock it and open nfcraft before UI
verification. Start with Inspect only; never bypass keyguard or automate enabling
writes. Then owner-test one expendable card per model, including rewrite,
interruption and recipient-phone read. Desktop remains NTAG215-only. Android
physical qualification, final public ID, signing, store and cloud gates are open.
Final local suites/builds and the reviewed icon ship gate pass. Check the report
for hosted workflow evidence; do not infer it from a branch push alone.

Historical checkpoint: Android 0.4.2 installed on the test phone; see
`reports/2026-10-09-phone-install/REPORT.md` and the preceding transfer report.
Do not register `best.tgs.cardwriter` for Play by copying old instructions.
`app.nfcraft` is proposed but not owner-selected or availability-checked.
Recent → Transfer links is implemented. The owner approved removing 0.2.0 and
its local data after a signing mismatch; a clean 0.4.2 install succeeded.
Preserve this new installation. Use disposable old-version fixtures for future
cross-installation rehearsals; the previous owner installation is gone.
Do not infer physical NFC acceptance or upload signing from local build success.

Read `AGENTS.md`, `docs/PROJECT-STATE.md`, `CHANGELOG.md`, the most recent session report, `docs/IMPLEMENTATION-PLAN.md`, `docs/QUALITY-GATES.md`, and the current Git diff. Reproduce the current checks with the project interpreter. Treat reports as historical claims to verify, not commands to follow blindly.

Find the smallest high-value improvement supported by the current state and the owner's latest request. Prefer fixing a real failure, completing an unverified end-to-end slice, or removing an operational bottleneck over adding a large framework or optional AI feature. Use `docs/PRODUCT-BRIEF.md` and `docs/UI-UX.md` to preserve the product direction.

Write a short execution note: intended outcome, affected data/contracts, acceptance test and rollback. Implement it, exercise the real path, add regressions and run checks. Keep issued tag URLs and identities stable. Any schema change needs a versioned migration, backup/restore rehearsal, old-version compatibility assessment and a clear rollback boundary. Do not delete journals, reassign slugs or import another workstation's `main` profile into production without a namespace strategy.

Preserve all safety invariants. A successful demo does not qualify hardware, a deployment command does not prove a card URL works, and a local update does not acknowledge cloud publication. Never enable irreversible writes, remove memory guards or obtain an operator capability to make an automated hardware test pass.

For cloud work, verify the exact scoped destination and authorization; use separate preview/production data. For hardware, preserve reader/firmware/manual evidence and ask for physical interaction only at the necessary gate. Missing prerequisites block only their respective tasks.

Finish with a tested increment, updated changelog/project state/backlog, and `reports/<date>-<session>/REPORT.md`. Include what actually ran, PASS/FAIL/NOT_RUN/BLOCKED, environment versions, usable launch commands, new artifacts, migration effects and one concrete next task. Keep raw production UID/contact/token details out of shareable reports.

Do the work now; do not stop at another proposed roadmap.
