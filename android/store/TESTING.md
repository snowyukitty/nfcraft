# Mobile acceptance and reviewer preparation

No physical NFC acceptance was run for 0.4.0. Use disposable test links and
owner-approved expendable NTAG215 cards. Never include real UIDs in store media.

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
