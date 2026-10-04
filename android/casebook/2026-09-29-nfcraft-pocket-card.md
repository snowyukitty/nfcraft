---
slug: nfcraft-pocket-card
date: 2026-09-29
project: nfcraft
targets: web, electron, Android native, store artwork
essence: keep
style_family: flat-geometric
signature_device: Tilted brass card in a thumb-cut sleeve
device_family: negative-space
device_detail: 256-unit sleeve mouth with a tilted emerging card
concept_lens: metaphor
cliche_avoided: NFC waves and pen-over-card clip art
status: shipped
scores_first: legibility=4 distinctiveness=3 balance=4 color=3 scalability=4 craft=4
scores_final: legibility=4 distinctiveness=4 balance=4 color=5 scalability=4 craft=4
iterations: 3
---

## Summary
A pocket writer keeps destinations ready for reuse. The winning mark is a cream
thumb-cut sleeve holding a tilted brass card on forest green. It beats the
folded card (SIM-card reading), shuttle (abstract link), and old press (printing
reading). A plain card control confirmed the fold alone did not add NFC meaning.
The broad pocket mouth and tilted emerging card survive 16px and adaptive crops.
Reviewed the static sheets and isolated Chromium Review Lab at light/dark/gray.
IconFlow ship passed with no automated warnings. The icon belongs to the owner;
no attribution is required and commercial use is unrestricted.

## What failed first
The transparent cream candidates disappeared on white. Adding a forest field
fixed contrast; rounding that field fixed the hard-corner audit. The upright
card read as paper in a printer; a 14-degree tilt localized to the card restored
the pocket reading. The house emoji proximity advisory was inspected: the
straight sleeve walls and thumb cut are visibly different from circular faces.
Native Android uses the same paths at 90% scale in a 108dp foreground, separate
from its solid background, and reuses alpha for themed icons. Store PNGs are
opaque. The shared toolkit is unchanged; its case-stat evolution signal is
recorded here for the toolkit owner.

## Lessons
<!-- One reusable rule per bullet. `- [ ]` = not yet distilled into the docs;
     flip to `- [x]` after promoting it (see docs/EVOLUTION.md). -->
- [ ] An upright card above a pocket can read as a printer. Tilting only the emerging card restores the card-holder reading while the pocket stays on the pixel grid.
