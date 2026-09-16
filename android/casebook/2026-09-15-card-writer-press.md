---
slug: card-writer-press
date: 2026-09-15
project: 
targets: 
essence: restamp
style_family: 
signature_device: Detached amber imprint struck below the press
device_family: detached-accent
device_detail: 144-unit imprint, 380 wide, held 128 units clear of the platen
concept_lens: verb
cliche_avoided: NFC wave arcs and a second contact card with a tap cue
status: shipped
scores_first: legibility=4 distinctiveness=4 balance=4 color=4 scalability=3 craft=3
scores_final: legibility=4 distinctiveness=4 balance=4 color=4 scalability=4 craft=4
iterations: 2
---

## Summary
A cream hand press on a rust ground, with the amber imprint it has just
struck held clear beneath it, expresses restamp. The sibling constraint drove the
concept: nfcraft already owns a clipped contact card with a curved tap aperture, so
this surface had to be a different object rather than a restyled one. The
neighbourhood proof puts the parent mark at distance 0.483 and the nearest avoid-set
neighbour (a plus sign) at 0.196, against a 0.12 gate.
<!-- One paragraph: the brief, the winning concept, why it won. -->

## What failed first
<!-- What the earlier passes got wrong and which change fixed it. This is the
     raw material for future lessons — be specific (axis, size, shape). -->
The bake-off killed two of three concepts on silhouette alone. A luggage tag
with a chevron cut read best at 128px but its outline is the Material label/tag icon,
so the mark would have borrowed that meaning at small sizes (L9); it also sat close to
the house canon's price tag. A nameplate with a swapped address strip reduced to a
plain filled rectangle with a bar across it and named no object at all.

The press then failed its own first review pass on the maskable row. Every element
satisfied the 128-unit two-pixel budget, and `check` reported no warnings, but the
amber imprint's corners fell outside the 40% safe-zone circle: the accent was far
enough from the centre that its size was never the binding constraint. Tightening the
composition to 154-870 on the vertical and narrowing the imprint from 480 to 380 units
brought every extreme inside the circle without costing 16px mass.

## Lessons
<!-- One reusable rule per bullet. `- [ ]` = not yet distilled into the docs;
     flip to `- [x]` after promoting it (see docs/EVOLUTION.md). -->
- [ ] Budget a detached accent radially, not only by size: an accent that clears the 128-unit two-pixel rule can still fall outside the 40% maskable safe circle because of how far it sits from the centre.
