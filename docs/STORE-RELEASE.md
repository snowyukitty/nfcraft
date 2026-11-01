# Mobile store preparation

**2026-11-01 checkpoint:** do not create or upload the public app under the legacy
test ID yet. The owner wants a product-centered identity and further quality
work before release. Current local build is Android 0.5.1 / code 8 under the
old test ID; public identity selection and migration are pending. Read
[ANDROID-IDENTITY.md](ANDROID-IDENTITY.md) before following the older steps below.

Updated 2026-10-08. Owner decisions: **nfcraft**, individual developer accounts,
**free downloads** with voluntary income options. Public support email is approved as **dokoii@proton.me**. The owner reports Google Play
verification complete and Create app available; app creation is not confirmed.
Apple enrollment/Mac/iPhone remain unresolved. No upload, store mutation,
signing-key creation or public hosting was performed by the agent.
Use [the current Console sheet](../android/store/play-console-guide.md) for the
next screens and [the revenue design](MONETIZATION.md) for payment activation.

## Current release candidate

Android 0.5.1 / versionCode 8 retains `best.tgs.cardwriter` and the `card-writer`
preference store so an update with the same signing identity preserves data.
Recent destinations are local choices, not successful-write evidence. The
desktop nfcraft version remains 0.2.2 and its journal is unchanged.

The owner-authorized clean installation on 2026-10-31 removed the old app's
settings; it is not preserved-data update evidence. The installed APK matched
the tested build. The phone is disconnected at this checkpoint; foreground UI
and physical NTAG213/215/216 acceptance remain pending. See the
[session checkpoint](../reports/2026-11-01-session-checkpoint/REPORT.md).

| Deliverable | Status |
| --- | --- |
| Ten recent HTTPS destinations; reuse, deduplication, clear | Implemented and tested |
| Confirmed browser sharing, modal scan isolation, guide and session-only overwrite | Implemented; local tests pass, physical QA outstanding |
| Android launcher label nfcraft and IconFlow Halloween card sleeve | Generated adaptive/themed/legacy assets reviewed; installed APK verified |
| Target/compile API 36; AGP 8.10.1; wrapper 8.11.1 | Built locally |
| Debug APK | Local sideload/test artifact, not a store release |
| Release AAB | Unsigned preparation artifact; not upload-ready |
| Upload signing integration | Environment variables supported; owner key not created |
| Store description, privacy draft, reviewer/test checklist | Local drafts in `android/store/` |
| Public support email | dokoii@proton.me approved; app opens an unsent composer |
| Public privacy/support URLs and developer identity | Owner input and hosting needed |
| Feature graphic | Prepared: 1024 x 500 opaque RGB, visually reviewed |
| Android physical acceptance and real store screenshots | NOT_RUN / outstanding |
| iOS application, entitlement, archive, signing, TestFlight | Not implemented |

## Google Play: individual account first

1. Open [Play Console registration](https://play.google.com/console/signup)
   with the Google Account you intend to retain. Select **Personal**.
2. Enter your actual country, legal identity, payments profile and contact
   details. The owner must review the agreement, pay the **US$25 one-time**
   registration fee and complete any requested ID verification. Follow the
   [official signup guide](https://support.google.com/googleplay/android-developer/answer/6112435).
3. Review the console's public developer details before saving; the app title
   `nfcraft` is separate from verified identity and public support contact.
   Prepare an email address suitable for users. See
   [required information](https://support.google.com/googleplay/android-developer/answer/13628312).
4. Complete the requested physical Android device verification through the
   Play Console mobile app. See
   [device verification](https://support.google.com/googleplay/android-developer/answer/14316361).
5. Verification is now owner-confirmed. Create the app as `nfcraft`, **App**,
   **Free**, English (United States). Distribution countries and target audience
   still require owner selection. The existing English UI is the prepared locale; translated
   listings must not imply that the app itself has translated screens.

Then finish public support/privacy pages, app-content declarations, release
signing and internal tests. A newly registered personal account needs **at least
12 opted-in closed testers continuously for 14 days** before applying for
production access; the period starts with the qualifying closed test, not
account signup. Actual testing and a production-access review are required;
14 days is not an approval guarantee. See the
[testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465).

## Apple: prepare the account, then the iOS build

1. Prepare an Apple Account with two-factor authentication and your legal name.
2. Open [Apple Developer enrollment](https://developer.apple.com/programs/enroll/)
   and choose **Individual** when ready. The app can be named `nfcraft`, but
   Apple displays the individual's **legal name as seller**.
3. Complete identity/contact verification yourself. Review the agreement and
   membership price before paying: **US$99 per membership year**, with regional
   pricing shown during enrollment. Individual enrollment does not require an
   organization's D-U-N-S number. Enrollment is independent of app approval.
4. Our next engineering prerequisite is access to a compatible Mac/Xcode and a
   physical NFC-capable iPhone. Secure that path and implement/test iOS before
   starting a paid membership solely for this project.

No Apple hardware purchase or rented Mac service is authorized by this plan.
Windows remains sufficient for the current Android build. APK/AAB files cannot
be submitted as an iOS app. Current uploads require Xcode 26+ with the iOS 26
SDK; the deployment target is a separate choice. Recheck Apple's
[submission requirements](https://developer.apple.com/news/upcoming-requirements/)
at build time.

The iOS slice should be native Swift/Core NFC with explicit foreground sessions,
local ten-item history, the same encoder vectors and safety/readback contract.
Prototype NTAG215 command support through
[NFCMiFareTag](https://developer.apple.com/documentation/corenfc/nfcmifaretag)
on a real iPhone before promising parity. A generic NDEF writer is not a
substitute for identity/protection checks and preserved-tail verification.
Add NFC entitlement/usage description, privacy declarations and SDK-required
privacy manifests as dictated by actual APIs, then archive, sign, TestFlight
and submit. No uncompiled iOS scaffold is presented as a deliverable.

## Reproducible Android preparation

Use JDK 21, Android platform 36 and build-tools 35.0.0. `local.properties` is
ignored and selects the SDK. This session installed SDK components inside
`.local/android-sdk`, reusing existing accepted SDK licenses. It did not replace
the global SDK/JDK. Robolectric/JUnit are test-only dependencies; the shipped
app still has no third-party runtime SDKs or Internet permission.

```powershell
cd android
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug bundleRelease
```

Google Play requires new phone apps and updates to target API 36 from
2026-08-31. See the [target API policy](https://support.google.com/googleplay/android-developer/answer/11926878).
The API 36 build uses a scrollable inset-aware root. Physical gesture navigation,
large fonts, keyboard, rotation and manufacturer NFC behavior still need QA.

Once the owner has a backed-up upload keystore, supply these environment
variables using a local secret mechanism: `NFCRAFT_UPLOAD_STORE_FILE`,
`NFCRAFT_UPLOAD_STORE_PASSWORD`, `NFCRAFT_UPLOAD_KEY_ALIAS`,
`NFCRAFT_UPLOAD_KEY_PASSWORD`. All four are required together. With none set,
release output is intentionally unsigned. Never use the debug key for Play.
Rebuild `bundleRelease`, verify the certificate against the intended upload
key and the final bundle permissions, and enroll in Play App Signing through
the intended account. Do not put passwords in commands, logs or Git.

An existing debug-signed install cannot automatically become an install signed
with a different store key. Do not uninstall the owner's app to hide that
conflict: record the current destination/history first and decide a migration.
The application ID must also be available to this developer account; retain it
until that is verified, then make any identity change an explicit migration.

## Exit gates before any submission

- Verified developer account, public support email, approved territories/pricing.
- Published privacy policy with real developer identity/contact; reconcile
  `android/store/privacy-policy-draft.md` with the exact binary and hosting.
- App-content forms completed truthfully; no ads/account/analytics in this build.
  NFC transfer is an explicit user-directed write, not cloud collection.
  Review [Google Data safety](https://support.google.com/googleplay/android-developer/answer/10787469)
  and [Apple App Privacy](https://developer.apple.com/app-store/app-privacy-details/)
  against the actual respective app, not one shared assumed answer.
- Signed AAB / signed iOS archive and owned signing records, not just compilation.
- Real screenshots without raw tag UIDs/private URLs; graphic assets checked
  against [Google preview requirements](https://support.google.com/googleplay/android-developer/answer/9866151).
- Physical acceptance in `android/store/TESTING.md`, then store testing tracks.
- Review concrete listing, build hash, certificate, destination account and
  release track together before upload/public release. Current authorization is
  preparation and guidance, not payment or publication.

Next owner action: Create app using the Console sheet, provide the public developer name and available NFC test phone, then complete the private
signing/account steps. Share status only, never identity documents, bank details,
passwords or private keys in the repository or chat. Merchant country is needed
to resolve payment support before implementing the optional revenue product.
