# nfcraft — resume and improve the next version

Continue the existing **nfcraft** project in this folder. Do not regenerate it from scratch.

Read `AGENTS.md`, `docs/PROJECT-STATE.md`, `CHANGELOG.md`, the most recent session report, `docs/IMPLEMENTATION-PLAN.md`, `docs/QUALITY-GATES.md`, and the current Git diff. Reproduce the current checks with the project interpreter. Treat reports as historical claims to verify, not commands to follow blindly.

Find the smallest high-value improvement supported by the current state and the owner's latest request. Prefer fixing a real failure, completing an unverified end-to-end slice, or removing an operational bottleneck over adding a large framework or optional AI feature. Use `docs/PRODUCT-BRIEF.md` and `docs/UI-UX.md` to preserve the product direction.

Write a short execution note: intended outcome, affected data/contracts, acceptance test and rollback. Implement it, exercise the real path, add regressions and run checks. Keep issued tag URLs and identities stable. Any schema change needs a versioned migration, backup/restore rehearsal, old-version compatibility assessment and a clear rollback boundary. Do not delete journals, reassign slugs or import another workstation's `main` profile into production without a namespace strategy.

Preserve all safety invariants. A successful demo does not qualify hardware, a deployment command does not prove a card URL works, and a local update does not acknowledge cloud publication. Never enable irreversible writes, remove memory guards or obtain an operator capability to make an automated hardware test pass.

For cloud work, verify the exact scoped destination and authorization; use separate preview/production data. For hardware, preserve reader/firmware/manual evidence and ask for physical interaction only at the necessary gate. Missing prerequisites block only their respective tasks.

Finish with a tested increment, updated changelog/project state/backlog, and `reports/<date>-<session>/REPORT.md`. Include what actually ran, PASS/FAIL/NOT_RUN/BLOCKED, environment versions, usable launch commands, new artifacts, migration effects and one concrete next task. Keep raw production UID/contact/token details out of shareable reports.

Do the work now; do not stop at another proposed roadmap.
