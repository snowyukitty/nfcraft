# Android 0.5.1 installation follow-up

Owner-authorized uninstall of differently signed 0.2.0 and clean installation
of 0.5.1 / code 8 passed on 2026-10-31; installed APK hash matches the tested
build. Previous settings were removed. Phone keyguard prevents foreground UI
acceptance until the owner unlocks it. Do not bypass keyguard. Verify Inspect
only and launcher icon first; physical model testing below is still NOT_RUN.

# Android 0.5.0 follow-up

Use [the supported profile contract](../../docs/ANDROID-TAGS.md) for model
vectors/fences and capacity. Local tests cover NTAG213/215/216; physical NFC
acceptance remains NOT_RUN. Rehearse blank, rewrite, oversize refusal,
protected-card refusal, interrupted write and a different recipient phone for
each model. NTAG213 factory Lock Control TLV must survive rewriting.

The initial 2026-10-31 in-place update was refused for mismatching signatures.
The later explicitly authorized clean 0.5.1 installation above resolves this
installation gate, with data loss acknowledged; it is not an in-place migration.

# Mobile acceptance and reviewer preparation

No physical NFC acceptance was run for 0.4.2. Use disposable test links and
owner-approved expendable NTAG215 cards. Never include real UIDs in store media.

Installation evidence (2026-10-09): clean 0.4.2 installation and package-version
inspection passed on the test phone. An attempted in-place 0.2.0 update failed
for a signing mismatch; the owner explicitly authorized uninstall/data removal
before the successful fresh install. This does not pass item 1 below or NFC QA.
Use disposable fixtures for legacy-update tests; preserve the new installation.

## Android UI and update acceptance

1. Update a same-key 0.2.0 install without uninstalling. Confirm its destination
   and Inspect only setting survive and its valid destination enters history once.
   Unknown-content overwrite deliberately resets to OFF, including legacy ON.
2. Save 12 distinct HTTPS URLs; see 10 newest entries. Reuse an older entry;
   confirm exact path/query, single entry and most-recent ordering.
3. Try blank, HTTP, credentials and overlong input; confirm rejection from
   history. Partly typed input must not fill history with prefixes.
4. Kill/reopen the app; destination and history persist. Cancel clear; list
   remains. Confirm clear; reopen; list stays empty while current input remains.
5. Save a new URL after clearing. Inspect a card; its URL must not silently
   enter destination history. Reading a card is not choosing its destination.
6. Check large font, landscape, keyboard, system-bar cutouts, gesture and
   three-button navigation on Android 16 and one older supported device.
7. Check launcher icon in normal/round/themed modes and the Privacy screen.
8. Share one HTTPS URL from Chrome: cancel leaves destination/history unchanged;
   Use link stores exactly the confirmed link and turns Inspect only ON. Repeat
   on cold launch, existing Activity, rotation and process recreation. Multiple
   URLs, extra text, HTTP, credentials, fragments and overlong values are refused.
9. Read the whole Quick guide by scrolling. On 320dp width and 160% font scale,
   mode controls stack; no label may disappear. TalkBack announces switch state.
10. Turn NFC off, return, use Open NFC settings, enable it and return. No NFC
    hardware shows an honest unsupported state. Check gesture/three-button bars.
11. Confirm local history does not transfer through an Android 12+ device-copy
    rehearsal on disposable data. OEM behavior remains physical QA, not a promise.

## Link transfer acceptance (before an application ID change)

1. Save three disposable links with different paths/query strings. Recent →
   Transfer links → Export links: long-press, select all and copy. Confirm exact
   values/order; unsaved current input and card identifiers are absent.
2. In a separate test installation, paste into Import links. Preview and cancel:
   no changes. Repeat and confirm: current destination stays unchanged,
   Inspect only is ON and overwrite is OFF. Restart and verify retention.
3. Merge overlapping lists: keep existing order and append new distinct links.
   Exceed ten combined links: reject without evicting any saved entry.
4. Try invalid HTTP, credentials, fragments, embedded controls and oversized
   text. Reject the complete import, with a useful error; no partial save.
5. Rotate/background during entry and confirmation: never import without a
   new confirmation. Check keyboard, scrolling and 200% font on the actual phone.
6. Dialogs pause new NFC admission. Clear history does not clear a copied list
   outside the app. Clean up disposable clipboard copies after this rehearsal.
7. Preserve the old installation until the new list is verified. This feature
   is not automatic Android backup and does not transfer app identity/signing.

## NFC acceptance

1. Blank NTAG215: write, full-area/tail readback, unchanged identity/protection.
2. Already-matching URL: no needless writes; receipt distinguishes this result.
3. Wrong geometry, protected/locked/unknown cards: expected refusals. Unknown
   overwrite remains an explicit operator choice.
4. Controlled link loss during a permitted test: do not claim unchanged after
   mutation; confirm original-target recovery and preserved memory.
5. Change the UI destination while an operation is running: the current card
   uses its captured destination; the next presentation uses the new one.
6. During an operation, opening history/help/privacy/overwrite confirmation must
   defer until the current pass closes. While any dialog (including nested clear
   confirmation) is open, presenting a tag must not start an operation. Dismiss
   it and confirm reader mode resumes. Background/recreate during a slow operation:
   the old operation may finish, but a new Activity cannot admit a second writer.
7. Read the written card on a different Android phone and iPhone; verify the
   exact HTTPS destination opens. Record models/OS/versions and real outcomes.
8. Enable unknown-content overwrite by explicit confirmation, then leave/reopen
   the app. It must be OFF. Cancel confirmation must never enable it. Never use
   a bank/access tag or card whose content matters for this test.

## Reviewer notes draft

No login, subscription or server is required. Provide an NFC-capable phone
and unlocked factory-default NTAG215 sample tag. Use an approved public test
URL, keep the card stationary until readback finishes, then read it with a
second phone. Inspect only never writes. The app does not support other NFC
chip types, payment cards, locks or password provisioning.

Do not submit until those hardware instructions have been followed on the
release build. There is no fabricated demo success mode for reviewers.
