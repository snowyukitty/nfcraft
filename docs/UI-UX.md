# nfcraft — interface direction

Preserve the workbench already shipped. Polish the workflow before changing its framework.

## Visual character

A quiet, precise workshop rather than a cyberpunk dashboard: restrained warm neutral background, legible ink, a small green accent, good spacing and consistent controls. Make the physical wooden card feel appropriate without adding fake wood texture everywhere. No particles, glossy floating panels, animated fake telemetry, decorative AI charts or gratuitous gradients.

## Information hierarchy

The most prominent area answers: **What mode am I in? Is writing permitted? What do I do with this card next?** Batch progress and the last result are secondary. Inventory and diagnostics are accessible but do not compete with the placement/removal instruction.

Never rely on color or sound alone. Show `DEMO / SIMULATED`, `HARDWARE / READ-ONLY` or `HARDWARE / EXPERIMENTAL WRITES` in words. A success refers to its specific check; a public URL not yet tested is `Not checked`, not green. Error text explains what happened, whether a write may have occurred, what not to do, and the safe next action.

## Interaction

One operator approval covers a bounded run. Each card needs no additional click. Require a removal event before processing another presentation. Pause is immediately available and means stop further writes, not undo. Recovery shows the original physical label/identity and reason, and cannot silently allocate a fresh URL.

Keyboard shortcuts must avoid accidental arming, work around focus in forms, be documented, and have visible equivalents. Keep proper focus states, labels and tab order. Avoid whole-page redraws that reset selection or focus. Inventory should become searchable/filterable as usage grows; do not display thousands of rows or recompute all history on every refresh without measurement.

## Required local UI checks

Normal empty start; reader absent/disconnected; missing optional dependency; duplicate; occupied planned region; unsupported tag; locked card; write interrupted; recovery mismatch; verification failure; expired approval; stale agent connection; no published route; mobile-width readable public page; long names/URLs and non-ASCII profiles. Exercise these against real local navigation and deployed CSP rather than only a screenshot.

## Public card page

Fast, readable and useful without login. Name, short introduction, explicitly chosen links and contact download. Validate/escape profile content and preserve Unicode in vCard import. No visitor tracking or personal-AI access by default. The recipient is not automatically known just because a route was fetched. NFC and printed QR should resolve to the same intended card route.

These are design requirements/backlog, not a claim that all are implemented in v0.1.1.
