# nfcraft: a free tool with voluntary support

Decision recorded 2026-10-08: the owner wants free downloads and income options,
including voluntary contributions. The release remains free; the proposals
below are not live products, prices, subscriptions, or revenue forecasts.

## Recommendation

Keep the useful tool free: writing, inspection, readback, ten recent links,
clearing history, browser sharing, privacy and recovery explanations. A card
operation must never wait for an ad, payment, rating, account, or network.

Build trust with the first closed test. Then introduce **Workshop finishes**:
one optional, non-consumable Google Play purchase of three visual finishes and
a small supporter mark inside the app. Payment buys a defined digital item,
while also supporting development. It is not described as a charitable donation.
No subscription or repeated tip prompt is needed for a utility used occasionally.

| Offering | Concrete value | Model | Order |
| --- | --- | --- | --- |
| Core workshop | Safe single-card writing, inspection, local history | Free, no ads | 0.4.0 test candidate |
| Workshop finishes | Moss, Indigo and Walnut decoration, optional supporter mark | One-time Play purchase; restore on the same Play account | First revenue experiment after billing QA |
| Label studio | Offline, printable card labels with matching QR and editable typography | Separate one-time Play product only when the exporter exists | Validate demand with testers first |
| Physical craft kits | Wooden NTAG215 cards, printed/engraved labels, human-readable fallback | Physical goods checkout, separate from digital entitlements | After supplier cost, delivery, returns and card QA are known |
| Custom card preparation | Small, individually scoped batches for a shop, event or maker | Quoted service, actual deliverables and support terms | Owner-operated pilot; do not promise hosted lifetime services |

The digital finishes are the smallest maintainable starting point. Label studio
has stronger recurring usefulness than charging for more history. Physical kits
connect the product's identity to something buyers can hold, but require a real
fulfillment operation. These are recommendations, not approved commitments to
operate a store or add a server.

## Payment policy research

Reviewed 2026-10-08 against primary sources:

- [Payments policy](https://support.google.com/googleplay/android-developer/answer/9858738):
  digital in-app items normally use Play Billing; physical goods are treated
  separately. Tax-exempt donations are a separate category; an individual
  developer is not assumed to be a tax-exempt charity.
- [Payments FAQ](https://support.google.com/googleplay/android-developer/answer/10281818):
  direct contributions can qualify for the peer-to-peer exception only when
  the whole contribution reaches the creator and grants no digital benefits.
  A supporter badge/finish is a digital benefit. Do not assume an arbitrary
  coffee/payment provider meets the exception, or infer regional program
  eligibility from the device locale.
- [Service fees](https://support.google.com/googleplay/android-developer/answer/112622):
  fees depend on applicable programs and enrollment. Show gross and actual net
  receipts separately; do not promise a universal commission rate.
- [Billing integration](https://developer.android.com/google/play/billing/integrate)
  and [billing testing](https://developer.android.com/google/play/billing/test):
  verify purchases, handle pending states, restore purchases, and acknowledge
  completed purchases. A payment sheet opening is not a successful purchase.
- [Billing release notes](https://developer.android.com/google/play/billing/release-notes):
  current documentation lists 9.1.0; versions from 8.1 raise minSdk to 23.
  The existing app supports API 21. Decide the compatibility approach explicitly
  before integrating; do not silently drop existing users to add monetization.

For this first release, external donation links, ads, billing libraries and
placeholder purchase buttons are absent. There is no configured receiving
account or real transaction evidence. No claim of an operational revenue
feature belongs in the current listing or Data safety declaration.

## Reviewable first product

Proposed product ID: `nfcraft_workshop_finishes` (not yet registered).
Proposed price hypothesis: US$2.99 equivalent, localized through Play Console;
owner chooses final markets/prices after seeing the merchant account's currency,
fees and tax handling. Do not hardcode this number into the app.

The three finishes change the background and secondary cards only. Success,
refusal, uncertainty, write progress and read-only labels retain the same
semantics, readable contrast and text. Never sell a different safety behavior.

Suggested screen copy:

> Support the workshop
>
> nfcraft's writing, verification and recent links are free. Workshop finishes
> adds three quiet color palettes and an optional supporter mark. One purchase,
> no subscription. Thank you for helping this small tool grow.

Actions: `Preview finishes`, `Get finishes · {Play localized price}`,
`Restore purchase`, `Keep using nfcraft`. Entry lives under Help/About; no
launch popup, countdown, guilt copy, fake discount, or interruption after writing.
Free users can preview the appearance without changing their current choice.

| State | User-facing behavior |
| --- | --- |
| Product loading | Core app works; checkout disabled until a fresh product result |
| Play unavailable / unsupported OS | Explain availability, keep all free tools usable; no alternate-payment detour |
| Ready | Exact localized price and one-time nature shown before opening Play |
| User cancels | Return quietly, no success message and no entitlement |
| Pending payment | Explain pending, no unlock and no repeated purchase invitation |
| Verified purchase | Grant finishes, acknowledge, show thanks once |
| Acknowledgment retry | Persist necessary transaction state privately and retry safely; no duplicate grants |
| Restore / reinstall | Query existing purchases and verify before unlocking |
| Refund / revocation | Reconcile with Play; return to free finish without touching links or card data |
| Offline after verified purchase | Retain cached cosmetic entitlement; reconcile when available |

Do not trust a local Boolean as proof of payment. A cosmetic-only client-side
verification approach has different fraud/restore tradeoffs from a backend;
choose and document one before implementation. Any backend needs a separately
approved destination, billing-unit analysis and tested consumption stop under
the workspace metered-services policy. None is introduced by this milestone.

## Measure use without surveillance

During the closed test, ask testers directly whether they successfully wrote
and re-read a card, reused a recent destination, understood the overwrite
warning, and would choose finishes or labels. Use opt-in feedback and Play
Console aggregate sales reports when available; no analytics SDK is needed.
Judge the first experiment by completed useful workflows, voluntary purchases,
refund reasons and support burden. Download count alone does not validate income.

Public support address approved by the owner: dokoii@proton.me. The app opens
an unsent composer and attaches no card data automatically. Merchant country
and payments-profile readiness remain unresolved.

## Activation gates

1. Confirm merchant account country/support and finish payments profile privately.
2. Approve the actual product, territory list, local prices and public support identity.
3. Resolve API 21/22 compatibility, choose verification/restore architecture, then
   implement Billing and update privacy/Data safety for the resulting binary.
4. Create the Play product and run license-tester purchases: success, cancel,
   decline, pending/complete, pending/cancel, reconnect, process death, duplicate
   callback, restore/reinstall, refund/revoke and unavailable product.
5. Prove NFC cannot start behind checkout and billing cannot block or modify NFC.
6. Review the signed build, exact declarations and receipts before rollout.

The free release can proceed through internal/closed testing while these gates
are completed. Adding revenue later does not require changing the free app to
paid download or replacing its application ID.
