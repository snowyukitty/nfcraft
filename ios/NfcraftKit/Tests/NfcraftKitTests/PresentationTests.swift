@testable import NfcraftKit
import XCTest

/// Whole presentations against the simulated card: what the operator is told,
/// and whether that is true of the card afterwards.
final class PresentationTests: XCTestCase {

    let url = "https://tgs.best/"

    private func present(_ card: SimulatedNTAG215,
                         _ request: Presentation.Request,
                         framing: Presentation.FramingChoice = .fixed(.platformHandlesCRC)) async -> Presentation.Outcome {
        await Presentation.run(card, request, framing: framing, pause: noPause)
    }

    func testBlankCardIsWrittenAndVerified() async {
        let card = SimulatedNTAG215()
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .written)
        XCTAssertTrue(outcome.verdict.isVerifiedWrite)
        XCTAssertEqual(Ndef.decodeArea(card.area), url)
        XCTAssertEqual(outcome.rememberDestination, url)
        XCTAssertEqual(outcome.receipt, ["uid    04:11:22:33:44:55:66", "now    " + url, "before (blank)"])
    }

    func testTheTailBeyondTheMessageIsPreserved() async {
        let card = SimulatedNTAG215()
        card.memory[16 + 400] = 0x5A
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .written)
        XCTAssertEqual(card.memory[16 + 400], 0x5A)
    }

    func testSecondTapIsAlreadyDoneAndWritesNothing() async {
        let card = SimulatedNTAG215()
        _ = await present(card, .init(destination: url))
        let writes = card.writeCommands
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .alreadyDone)
        XCTAssertEqual(card.writeCommands, writes)
    }

    func testRewriteToAnotherDestinationOfOurs() async {
        let card = SimulatedNTAG215()
        _ = await present(card, .init(destination: url))
        let outcome = await present(card, .init(destination: "https://tgs.best/next"))
        XCTAssertEqual(outcome.verdict, .written)
        XCTAssertEqual(Ndef.decodeArea(card.area), "https://tgs.best/next")
        XCTAssertTrue(outcome.receipt.contains("before " + url))
    }

    func testInspectOnlyNeverWrites() async {
        let card = SimulatedNTAG215()
        let outcome = await present(card, .init(destination: url, inspectOnly: true))
        XCTAssertEqual(outcome.verdict, .inspected)
        XCTAssertEqual(card.writeCommands, 0)
        XCTAssertNil(outcome.rememberDestination, "inspection is not a use of the destination")
        XCTAssertTrue(outcome.receipt.contains("held   (blank)"))
    }

    func testUnfamiliarContentIsRefusedUnlessAllowed() async {
        let card = SimulatedNTAG215()
        card.memory[16..<24] = [0x03, 0x04, 0xD8, 0x00, 0x00, 0x00, 0xFE, 0x00]
        var outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .unfamiliarContent)
        XCTAssertEqual(card.writeCommands, 0)

        outcome = await present(card, .init(destination: url, allowUnknown: true))
        XCTAssertEqual(outcome.verdict, .written)
        XCTAssertEqual(Ndef.decodeArea(card.area), url)
    }

    func testDataHiddenUnderAnEmptyTlvIsRefused() async {
        let card = SimulatedNTAG215()
        card.memory[16 + 9] = 0x41
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .occupiedWriteRegion)
        XCTAssertEqual(card.writeCommands, 0)
    }

    func testLockedCardIsRefusedBeforeAnythingIsRead() async {
        let card = SimulatedNTAG215()
        card.memory[0x82 * 4] = 0x01
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .refused)
        XCTAssertEqual(card.writeCommands, 0)
        XCTAssertFalse(card.log.contains { $0.hasPrefix("FAST_READ") }, "the user area is not read on a refused card")
    }

    func testInvalidDestinationWritesNothingAndIsNotRemembered() async {
        let card = SimulatedNTAG215()
        let outcome = await present(card, .init(destination: "http://tgs.best"))
        XCTAssertEqual(outcome.verdict, .noDestination)
        XCTAssertEqual(card.writeCommands, 0)
        XCTAssertNil(outcome.rememberDestination)
    }

    func testRemovalBeforeAnyWriteSaysTheCardIsUnchanged() async {
        let card = SimulatedNTAG215()
        card.dead = true
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .cardMoved)
        XCTAssertEqual(outcome.stage, .untouched)
    }

    func testTornWriteIsReportedThenFinishedOnTheNextTap() async {
        let card = SimulatedNTAG215()
        card.leaveAfterWrites = 2
        var outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .writeInterrupted)
        XCTAssertFalse(outcome.verdict.isVerifiedWrite)
        XCTAssertNil(Ndef.decodeArea(card.area), "no length is advertised while the body is incomplete")
        XCTAssertEqual(outcome.rememberDestination, url, "a write was attempted with a valid destination")

        // The card comes back. Without the override, the app recognises its
        // own interrupted write and finishes it.
        card.dead = false
        card.leaveAfterWrites = nil
        let before = card.writeCommands
        outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .finished)
        XCTAssertEqual(Ndef.decodeArea(card.area), url)
        XCTAssertLessThan(card.writeCommands - before, try! Ndef.writePlan(url).count,
                          "pages that already took are not sent again")
        XCTAssertTrue(outcome.receipt.contains("before (an interrupted write by this app)"))
    }

    func testLossAfterCommitIsNotConfirmedRatherThanWritten() async throws {
        let card = SimulatedNTAG215()
        card.leaveAfterAcks = try Ndef.writePlan(url).count
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .notConfirmed)
        XCTAssertEqual(outcome.stage, .committed)
        XCTAssertFalse(outcome.verdict.isVerifiedWrite)
    }

    func testAcknowledgedButLostWriteIsCaughtByReadback() async {
        let card = SimulatedNTAG215()
        card.ignoreWrites = true // the card ACKs and keeps nothing
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .readbackDiffers)
        XCTAssertFalse(outcome.verdict.isVerifiedWrite)
    }

    func testIdentityChangeDuringTheWriteIsCaught() async {
        let card = SimulatedNTAG215()
        card.mutateConfigOnWrite = true
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .identityChanged)
    }

    func testLostAnswerToTheCommitWriteIsStillAnInterruptedWrite() async throws {
        // The commit landed but its answer did not: the app cannot know it
        // landed, so it must not claim the message is committed.
        let card = SimulatedNTAG215()
        card.leaveAfterWrites = try Ndef.writePlan(url).count
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .writeInterrupted)
        XCTAssertFalse(outcome.verdict.isVerifiedWrite)
    }

    func testFinalNakMidPlanIsAWriteRefusalNotACardThatMoved() async {
        let card = SimulatedNTAG215()
        card.nakWrites = 0x04
        card.nakBudget = .max
        let outcome = await present(card, .init(destination: url))
        XCTAssertEqual(outcome.verdict, .writeInterrupted)
        XCTAssertEqual(outcome.headline, "Write refused")
        XCTAssertEqual(card.writeCommands, 1)
    }

    func testAWeakLinkIsShownOnTheReceipt() async {
        let card = SimulatedNTAG215()
        card.dropEvery = 5
        var told = 0
        let outcome = await Presentation.run(card, .init(destination: url), pause: noPause, onStruggling: { told += 1 })
        XCTAssertEqual(outcome.verdict, .written)
        XCTAssertEqual(told, 1)
        XCTAssertTrue(outcome.receipt.last?.hasPrefix("link   ") ?? false)
    }

    // MARK: Command framing (iOS)

    func testProbedFramingWritesUnderEveryPlatformBehaviour() async {
        for (appCRC, responseCRC) in [(true, false), (true, true), (false, false), (false, true)] {
            let card = SimulatedNTAG215()
            card.requiresAppCRC = appCRC
            card.answersWithCRC = responseCRC
            let outcome = await present(card, .init(destination: url), framing: .probe)
            XCTAssertEqual(outcome.verdict, .written, "appCRC \(appCRC) responseCRC \(responseCRC)")
            XCTAssertEqual(outcome.framing, Framing(appendsCRC: appCRC, responseCarriesCRC: responseCRC))
            XCTAssertEqual(Ndef.decodeArea(card.area), url)
        }
    }

    func testProbeIsNotFooledByATagThatIgnoresTrailingBytes() async {
        let card = SimulatedNTAG215()
        card.lenientLength = true
        let outcome = await present(card, .init(destination: url), framing: .probe)
        XCTAssertEqual(outcome.framing, .platformHandlesCRC, "two stray CRC bytes must never ride on a WRITE")
        XCTAssertEqual(outcome.verdict, .written)
    }

    func testADroppedBareProbeDoesNotHandTheChoiceToTheCRCFrame() async {
        // A lenient tag on a weak link: the first bare GET_VERSION is lost.
        let card = SimulatedNTAG215()
        card.lenientLength = true
        let flaky = DropFirst(card, count: 1)
        let framing = await Framing.probe(flaky)
        XCTAssertEqual(framing, .platformHandlesCRC)
    }

    func testWrongFixedFramingFailsClosed() async {
        let card = SimulatedNTAG215()
        card.requiresAppCRC = true
        let outcome = await present(card, .init(destination: url), framing: .fixed(.platformHandlesCRC))
        XCTAssertFalse(outcome.verdict.isVerifiedWrite)
        XCTAssertEqual(outcome.stage, .untouched)
        XCTAssertEqual(card.writeCommands, 0)
    }

    func testProbeThatFindsNoNTAG215WritesNothing() async {
        let card = SimulatedNTAG215()
        let silent = Silent(card)
        let outcome = await Presentation.run(silent, .init(destination: url), framing: .probe, pause: noPause)
        XCTAssertEqual(outcome.verdict, .notNtag215)
        XCTAssertEqual(card.writeCommands, 0)
        XCTAssertNil(outcome.framing)
    }
}

/// Loses the first `count` exchanges, then behaves.
final class DropFirst: Type2Link {
    let inner: SimulatedNTAG215
    var remaining: Int
    init(_ inner: SimulatedNTAG215, count: Int) { self.inner = inner; remaining = count; inner.dropEvery = 0 }
    var maxResponseBytes: Int? { nil }
    func connect() async throws { try await inner.connect() }
    func disconnect() async {}
    func transceive(_ command: [UInt8]) async throws -> [UInt8] {
        if remaining > 0 { remaining -= 1; throw LinkError("Simulated lost exchange.") }
        return try await inner.transceive(command)
    }
}

/// A tag that connects and never answers, as a non-Type-2 target might.
final class Silent: Type2Link {
    let inner: SimulatedNTAG215
    init(_ inner: SimulatedNTAG215) { self.inner = inner }
    var maxResponseBytes: Int? { nil }
    func connect() async throws { try await inner.connect() }
    func disconnect() async {}
    func transceive(_ command: [UInt8]) async throws -> [UInt8] { throw LinkError("no answer") }
}
