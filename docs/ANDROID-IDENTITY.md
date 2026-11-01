# Android identity before the first Play release

Updated 2026-10-09. **Store creation is on hold pending the owner's identity
choice.** Do not copy the legacy test application's ID into a new Play record
just because the current APK still uses it.

## What the old name means

`best.tgs.cardwriter` entered this repository with the early Android Card Writer
prototype (`d9634d1`). Its prefix follows the reverse-domain form of `tgs.best`,
the old default test destination. The owner has clarified that the website was
only a test target and must not define nfcraft's broader product identity.

Neither Android nor the NFC encoder requires that prefix. Application identity,
store display name and a card's destination are separate concepts. The writer
accepts validated arbitrary HTTPS destinations; renaming the app does not
rewrite already-issued cards or change their URLs.

## Candidate and present decision state

Recommended candidate: **`app.nfcraft`**. It is short, product-centered, and
independent of the test website. Alternative: `me.dokoii.nfcraft` if the owner
prefers a publisher prefix. Neither is selected, registered or verified as
available in Play Console. No ownership of a corresponding domain is implied.

The current 0.5.1 build deliberately remains a compatible **legacy test build**
under `best.tgs.cardwriter` while independent quality work proceeds. Its ID is
not a renewed recommendation for the public release. Do not publish this build.

[Android's application ID documentation](https://developer.android.com/build/configure-app-module)
requires at least two segments, with each beginning with a letter and using
letters, digits or underscores. Thus `nfcraft` alone is not a valid ID;
`app.nfcraft` satisfies the syntax. Availability remains a separate Console check.
The Java namespace and the installed application ID can technically differ;
for the final cleanup, prefer a coherent namespace/source rename after the
owner chooses the public identity.

## Safe switch checklist

1. Confirm the owner's final ID and whether any Play app record has already
   been created. Do not delete a record or assume a name is available.
2. Preserve the old test installation and its destination/recent list. A new
   application ID creates a separate Android sandbox, even with the same
   signing key; keeping the preferences filename does not migrate data.
3. Version 0.4.2 provides Recent → Transfer links: manually copy recent URLs,
   then paste, preview and confirm a lossless merge in the new installation.
   Synthetic tests pass; physical cross-installation acceptance is pending.
   Never use uninstall,
   backup flags, direct private-storage scraping or a shared UID as a shortcut.
   Test the transfer with synthetic links before using owner data.
4. Rename `applicationId`, namespace/Java packages, JVM harness imports/paths,
   manifest references, artifact expectations and current release docs together.
   Historical reports retain their original facts.
5. Build both a preserved old test artifact and the new candidate, inspect
   compiled identities/signers, and rehearse side-by-side installation and
   link transfer on a chosen test phone. This migration has no phone QA yet.
6. Recheck sharing, data deletion, lifecycle/NFC admission and any pending
   platform services. Do not change encoded card URLs or the desktop package.
7. Only then create/reconcile the Play record and proceed with signed internal
   testing. After public release, keep the chosen ID stable for updates.

This identity decision is independent of the visual and interaction quality
work. A short name cannot replace the hardware, privacy, signing and testing
gates, and those gates should be completed before publication.
