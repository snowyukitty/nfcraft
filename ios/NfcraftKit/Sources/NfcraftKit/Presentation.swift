/// One card presentation, from first contact to a verified (or honestly
/// unverified) result.
///
/// This is the decision logic of the Android `MainActivity.handle()` and
/// `lostContact()`, lifted out of the UI so it can be tested without a phone
/// and shared by whatever SwiftUI/UIKit screen drives it. The screen only
/// renders an `Outcome`; it never decides whether a card was written. Screens
/// reach it through a `Station`, which allows one presentation at a time.
public enum Presentation {

    public struct Request: Equatable {
        public let destination: String
        public let inspectOnly: Bool
        public let allowUnknown: Bool
        /// The record from an earlier interrupted write, if the app kept one.
        /// Only a matching record lets a staged card resume without the override.
        public let recovery: RecoveryRecord?

        public init(destination: String, inspectOnly: Bool = false, allowUnknown: Bool = false,
                    recovery: RecoveryRecord? = nil) {
            self.destination = destination
            self.inspectOnly = inspectOnly
            self.allowUnknown = allowUnknown
            self.recovery = recovery
        }
    }

    /// What this app needs to recognise its own interrupted write: the card,
    /// the user area as it was before the first page was sent, and the
    /// destination being written. The staged header `03 00 D1 01` alone is the
    /// same for every destination, so it proves nothing by itself.
    ///
    /// Contains the UID and the card's previous content: keep it on the
    /// device, out of logs, backups of shared data and analytics.
    public struct RecoveryRecord: Equatable {
        public let uid: [UInt8]
        public let original: [UInt8]
        public let target: String

        public init(uid: [UInt8], original: [UInt8], target: String) {
            self.uid = uid
            self.original = original
            self.target = target
        }
    }

    public enum Verdict: String, Equatable {
        // Nothing was written.
        case refused, notNtag215, unexpectedGeometry, noDestination, framingUnconfirmed
        case unfamiliarContent, occupiedWriteRegion, inspected, alreadyDone, cardMoved, busy
        // Something may have been written.
        case writeInterrupted, notConfirmed, readbackDiffers, identityChanged, failed
        // Verified by full readback and an unchanged identity.
        case written, finished

        /// The only verdicts that may be shown as a completed write.
        public var isVerifiedWrite: Bool {
            self == .written || self == .finished
        }
    }

    /// How far the plan got. It advances *before* each page is sent: a write
    /// that threw may still have reached the tag, so the copy must never claim
    /// the card is untouched once a page has gone out.
    public enum Stage: Equatable {
        case untouched, writing, committed
    }

    public struct Outcome: Equatable {
        public let verdict: Verdict
        public let headline: String
        public let detail: String
        /// Receipt lines for the operator. Contains the UID; keep it on screen,
        /// out of logs and analytics.
        public let receipt: [String]
        public let stage: Stage
        /// A destination the caller may add to the recent list. Set as soon as
        /// a write is attempted with a valid destination — history is
        /// convenience state, never a write receipt.
        public let rememberDestination: String?
        /// The command framing this tag answered to. Nil when never established.
        public let framing: Framing?
        /// The recovery record to keep for the next tap, replacing the one in
        /// the request: a new one after an interrupted write, nil after a
        /// verified or already-done card, and the request's own otherwise.
        public let recovery: RecoveryRecord?
    }

    /// How to frame raw commands for this platform.
    public enum FramingChoice: Equatable {
        /// A framing confirmed outside this presentation — on Core NFC, by the
        /// recorded device spike. Writes are allowed.
        case fixed(Framing)
        /// Establish it with the read-only GET_VERSION probe. Writes are
        /// allowed only when the bare frame was answered, which is the one
        /// unambiguous result; a CRC-carrying answer could also come from a
        /// tag that ignores trailing bytes.
        case probe
    }

    static func run(_ link: Type2Link,
                    _ request: Request,
                    framing choice: FramingChoice = .fixed(.platformHandlesCRC),
                    pause: @escaping (Int) async -> Void = Tag215.sleep,
                    onStruggling: (() -> Void)? = nil) async -> Outcome {
        let run = Run(request)
        var card: Tag215?
        do {
            let framing: Framing
            switch choice {
            case .fixed(let known):
                framing = known
            case .probe:
                try await link.connect()
                guard let found = await Framing.probe(link) else {
                    await link.disconnect()
                    return run.finish(.notNtag215, "Not an NTAG215",
                                      "No exact NTAG215 GET_VERSION answer under any command framing."
                                          + " Nothing was written.", nil)
                }
                framing = found
                run.framingConfirmed = !found.appendsCRC
            }
            run.framing = framing
            let framed: Type2Link = framing == .platformHandlesCRC ? link : FramedLink(link, framing: framing)
            let opened = try await Tag215.open(framed, pause: pause)
            opened.onStruggling = onStruggling
            card = opened
            let outcome = try await run.handle(opened)
            await link.disconnect()
            return outcome
        } catch let refusal as Refusal {
            await link.disconnect()
            if run.stage != .untouched {
                // The card answered GET_VERSION correctly before the write and
                // differently after it. That is an identity change on a card
                // that has been written to, not a card that was never touched.
                run.pending = nil
                return run.finish(.identityChanged, "Identity changed",
                                  "GET_VERSION changed after pages were written. Set this card aside.", card)
            }
            return run.finish(.notNtag215, refusal.headline, refusal.detail, card)
        } catch let fence as Tag215.FenceViolation {
            await link.disconnect()
            return run.finish(.failed, "Failed",
                              "Internal write fence refused page \(Tag215.hexPage(fence.page)). Set this card aside.",
                              card)
        } catch let gate as Tag215.NotInspected {
            await link.disconnect()
            return run.finish(.failed, "Failed",
                              "Internal check refused a \(gate.operation) before inspection. Set this card aside.",
                              card)
        } catch let lost as Tag215.IdentityLost {
            // The inspected card left and another answered. Nothing was sent
            // to the other card; the inspected one is where the plan stopped,
            // and its recovery record (bound to its own UID) stays valid.
            await link.disconnect()
            return run.lostContact(card, lost.description, refused: false)
        } catch let rejected as Tag215.Rejected {
            await link.disconnect()
            return run.lostContact(card, rejected.description, refused: true)
        } catch {
            await link.disconnect()
            return run.lostContact(card, "\(error)", refused: false)
        }
    }

    /// Mutable state for one presentation. Not shared between taps.
    private final class Run {
        let request: Request
        var stage = Stage.untouched
        var remember: String?
        var facts: [String] = []
        var framing: Framing?
        var framingConfirmed = true
        /// Set once a write is about to start: the record that would let the
        /// next tap finish it.
        var pending: RecoveryRecord?
        var verified = false

        init(_ request: Request) {
            self.request = request
        }

        func handle(_ card: Tag215) async throws -> Outcome {
            let before = try await card.inspect()
            facts = ["uid    " + before.uidHex]
            if let problem = before.unsafe {
                return finish(.refused, "Refused", problem, card)
            }

            let original = try await card.readArea()
            if original.count != Ndef.capacity {
                return finish(.unexpectedGeometry, "Unexpected geometry",
                              "Read \(original.count) bytes where \(Ndef.capacity) were expected."
                                  + " Nothing was written.", card)
            }
            let held = Ndef.decodeArea(original)

            if request.inspectOnly {
                let label = held ?? (Ndef.isEmpty(original) ? "(blank)" : "(content this app does not recognise)")
                facts.append("held   " + label)
                return finish(.inspected, "Inspected",
                              held.map { "This card points at " + $0 } ?? "No recognisable URL record on this card.",
                              card)
            }

            let target = request.destination
            let area: [UInt8]
            do {
                area = try Ndef.encodeArea(target)
            } catch let Ndef.EncodeError.invalid(problem), let Ndef.EncodeError.tooLarge(problem) {
                return finish(.noDestination, "No destination", problem, card)
            }
            remember = target

            // Resume only what this app can attribute to its own recorded
            // operation on this very card, page by page.
            var resumeFrom: RecoveryRecord?
            if let record = request.recovery, record.uid == before.uid, record.target == target,
               Ndef.recoveryMatches(current: original, original: record.original, target: area) {
                resumeFrom = record
            }
            let resumable = resumeFrom != nil && held != target
            let heldLabel = held
                ?? (resumable ? "(an interrupted write by this app)"
                    : Ndef.isEmpty(original) ? "(blank)" : "(content this app does not recognise)")
            facts.append("held   " + heldLabel)

            if held == target {
                verified = true
                return finish(.alreadyDone, "Already done",
                              "This card already carries the destination. The readback matched.", card)
            }

            if !request.allowUnknown && !resumable {
                if held == nil && !Ndef.isEmpty(original) {
                    return finish(.unfamiliarContent, "Unfamiliar content",
                                  "This card holds data this app does not recognise. Nothing was written."
                                      + " Turn on Overwrite unknown if you are sure it is yours.", card)
                }
                if Ndef.hidesDataUnderEmptyTlv(original, plannedLength: area.count) {
                    return finish(.occupiedWriteRegion, "Occupied write region",
                                  "The NDEF message is empty but the region to be written holds data."
                                      + " Nothing was written.", card)
                }
            }

            if !framingConfirmed {
                return finish(.framingUnconfirmed, "Framing not confirmed",
                              "This phone's command framing could not be confirmed without writing."
                                  + " Nothing was written; inspection still works.", card)
            }

            // The record keeps the area from before the *first* attempt, so a
            // card torn twice still resolves against its real previous content.
            pending = RecoveryRecord(uid: before.uid, original: resumeFrom?.original ?? original, target: target)
            let plan = try Ndef.writePlan(target, current: original)
            for (i, step) in plan.enumerated() {
                stage = .writing
                try await card.writePage(step.page, step.data)
                if i == plan.count - 1 {
                    stage = .committed
                }
            }

            // The write is not the evidence. The readback of the whole
            // advertised area is, with the preserved tail beyond what was
            // written and an unchanged identity and configuration.
            let observed = try await card.readArea()
            var expected = original
            expected.replaceSubrange(0..<area.count, with: area)
            if observed != expected {
                pending = nil
                return finish(.readbackDiffers, "Readback differs",
                              "The full user-area readback does not match the intended write and the"
                                  + " preserved tail. Set this card aside.", card)
            }
            let after = try await card.inspect()
            if after != before {
                pending = nil
                return finish(.identityChanged, "Identity changed",
                              "Tag identity or protected configuration changed during the write."
                                  + " Set this card aside.", card)
            }

            verified = true
            facts = ["uid    " + before.uidHex, "now    " + target, "before " + heldLabel]
            return finish(resumable ? .finished : .written, resumable ? "Finished" : "Written",
                          "Verified by full readback. Remove the card.", card)
        }

        /// Losing the card means different things at different points in the
        /// plan. "Tap it again" is only honest before the first page write.
        func lostContact(_ card: Tag215?, _ reason: String, refused: Bool) -> Outcome {
            let because = " (" + reason + ")"
            switch stage {
            case .committed:
                return finish(.notConfirmed, "Not confirmed",
                              "The message was committed but the verifying readback did not finish"
                                  + because + " Tap the same card again to confirm it.", card)
            case .writing:
                return finish(.writeInterrupted, refused ? "Write refused" : "Write interrupted",
                              (refused ? "The card refused a page part-way through" : "The card left the field part-way through")
                                  + because + " It may now hold an incomplete message. Tap it again to inspect"
                                  + " it; this app recognises its own interrupted write and finishes it"
                                  + " without repeating the pages that already took.", card)
            case .untouched:
                return finish(.cardMoved, "Card moved",
                              "Lost contact before anything was written" + because
                                  + " The card is unchanged. Tap it again.", card)
            }
        }

        func finish(_ verdict: Verdict, _ headline: String, _ detail: String, _ card: Tag215?) -> Outcome {
            var lines = facts
            if let card, card.struggled {
                lines.append("link   " + card.effort + (card.readPath.isEmpty ? "" : " · " + card.readPath))
            }
            let recovery: RecoveryRecord?
            if verified {
                recovery = nil
            } else if stage != .untouched {
                recovery = pending
            } else {
                recovery = request.recovery
            }
            return Outcome(verdict: verdict, headline: headline, detail: detail, receipt: lines,
                           stage: stage, rememberDestination: remember, framing: framing, recovery: recovery)
        }
    }
}

/// The one way a screen runs a presentation: one at a time per link.
///
/// Two overlapping presentations on one tag would interleave their write
/// plans — one could stage while the other commits — so a second request
/// while one is in flight is answered `busy` before anything is sent.
public final class Station {
    private let link: Type2Link
    private let gate = Gate()
    private var choice: Presentation.FramingChoice

    public init(_ link: Type2Link, framing: Presentation.FramingChoice) {
        self.link = link
        self.choice = framing
    }

    public func present(_ request: Presentation.Request,
                        pause: @escaping (Int) async -> Void = Tag215.sleep,
                        onStruggling: (() -> Void)? = nil) async -> Presentation.Outcome {
        guard await gate.acquire() else {
            return Presentation.Outcome(verdict: .busy, headline: "Busy",
                                        detail: "Another card operation is still running. Nothing was sent.",
                                        receipt: [], stage: .untouched, rememberDestination: nil,
                                        framing: nil, recovery: request.recovery)
        }
        let outcome = await Presentation.run(link, request, framing: choice, pause: pause, onStruggling: onStruggling)
        // Only the unambiguous probe result is kept for later taps.
        if case .probe = choice, let found = outcome.framing, !found.appendsCRC {
            choice = .fixed(found)
        }
        await gate.release()
        return outcome
    }

    /// A check-and-set with no suspension point inside, so it is atomic even
    /// though actors are reentrant.
    private actor Gate {
        private var busy = false

        func acquire() -> Bool {
            if busy { return false }
            busy = true
            return true
        }

        func release() {
            busy = false
        }
    }
}
