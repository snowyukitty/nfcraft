# nfcraft mobile store copy — local draft

English matches the current app UI. Public support: dokoii@proton.me. Developer
identity, privacy/support URLs, countries and audience are unresolved. Download is free. Do not
upload this draft until those fields and physical acceptance are complete.

## Google Play

Name: nfcraft

Short description: Write HTTPS links to NTAG215 cards. Keep your last 10 destinations handy.

Full description:

Give an NFC card the right destination with nfcraft.

Enter an HTTPS link, hold a compatible NTAG215 card against your Android phone,
and keep it still while nfcraft writes and checks the result. Save up to 10
recent destinations on your phone, select one to use again, or clear the list.

- Write one HTTPS link to one NTAG215 card at a time.
- Inspect a card without writing to it.
- Verify the written data by reading it back.
- Reuse recent links without typing them again.
- Share a link from your browser, review it, and start in Inspect only mode.
- Follow the built-in guide and explicitly confirm unfamiliar-content overwrite.
- Work without an account, ads or an Internet connection for NFC operations.
- Get help from the local guide or contact dokoii@proton.me.

Requires an NFC-capable Android phone and compatible, writable NTAG215 tags.
Other tag models and protected cards are not supported. Keep the card in place
until verification completes. nfcraft does not lock cards or set passwords.
A saved link is not proof of a successful write. Test a written card with a
recipient phone before sharing it. Opening its destination requires whatever
network access the destination website needs.

## App Store — deferred until an iOS app exists

Proposed name: nfcraft

Proposed subtitle: Your links, ready to tap

Do not reuse the Android description or device compatibility claims as an iOS
listing until Core NFC behavior is implemented and physically tested. The
1024px icon is prepared artwork only. Screenshots, description, review notes
and App Privacy answers must be produced from the tested iOS build.

## Release notes draft

Share a destination from your browser and confirm it before use. Dialogs pause
new NFC scans. Unknown-content overwrite now requires confirmation and resets
when you leave the app. Includes a quick guide, more accessible controls, and
a fix for uppercase hosts in Turkish device locales.

## Asset inventory

- `google-play-icon.png`: opaque 512 x 512 PNG.
- `app-store-icon.png`: opaque 1024 x 1024 PNG; future iOS source asset.
- `../master.svg`: editable identity; `../master-review.json`: reviewed contract.
- `feature-graphic.png`: 1024 x 500 opaque RGB editorial graphic; reproducible
  through `../tools/build_store_assets.py`.
- Real device screenshots: outstanding. Robolectric images
  in build reports are engineering evidence, not store screenshots.
