@testable import NfcraftKit
import XCTest

/// The command layer on a link that misbehaves — a port of LinkTest.java,
/// plus the iOS command-framing cases. Every property is a claim the app
/// makes to the operator: a write reported as done was confirmed by the
/// card, and a card that refuses is not asked again as if it had stuttered.
final class LinkTests: XCTestCase {

    func testCleanCardReadsAndWrites() async throws {
        let card = SimulatedNTAG215()
        let tag = try await Tag215.open(card, pause: noPause)
        let inspection = try await tag.inspect()
        XCTAssertNil(inspection.unsafe)
        XCTAssertEqual(inspection.uidHex, "04:11:22:33:44:55:66")
        let area = try await tag.readArea()
        XCTAssertEqual(area.count, Ndef.capacity)
        try await tag.writePage(0x04, [0x03, 0x00, 0xD1, 0x01])
        XCTAssertEqual(card.page(0x04), [0x03, 0x00, 0xD1, 0x01])
        XCTAssertEqual(tag.effort, "")
        XCTAssertFalse(tag.struggled)
    }

    func testTransientDropsAreRidden() async throws {
        let card = SimulatedNTAG215()
        card.dropEvery = 3
        var warnings = 0
        let tag = try await Tag215.open(card, pause: noPause)
        tag.onStruggling = { warnings += 1 }
        _ = try await tag.inspect()
        let area = try await tag.readArea()
        XCTAssertEqual(area.count, Ndef.capacity)
        for step in try Ndef.writePlan("https://tgs.best") {
            try await tag.writePage(step.page, step.data)
        }
        let after = try await tag.readArea()
        XCTAssertEqual(Ndef.decodeArea(after), "https://tgs.best")
        XCTAssertTrue(tag.struggled)
        XCTAssertTrue(tag.effort.contains("retr"))
        XCTAssertEqual(warnings, 1, "the operator is told once, not on every retry")
    }

    func testTruncatedAnswersAreRidden() async throws {
        let card = SimulatedNTAG215()
        card.truncateEvery = 4
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        let area = try await tag.readArea()
        XCTAssertEqual(area.count, Ndef.capacity)
    }

    func testSwallowedAckIsConfirmedByReadback() async throws {
        let card = SimulatedNTAG215()
        card.swallowAcks = true
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        try await tag.writePage(0x05, [0x11, 0x22, 0x33, 0x44])
        XCTAssertEqual(card.page(0x05), [0x11, 0x22, 0x33, 0x44])
    }

    func testSwallowedAckOverALostWriteFails() async throws {
        // Silence must never be read as success.
        let card = SimulatedNTAG215()
        card.swallowAcks = true
        card.ignoreWrites = true
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        await assertThrows { try await tag.writePage(0x06, [1, 2, 3, 4]) }
    }

    func testRecoverableNakIsRetried() async throws {
        let card = SimulatedNTAG215()
        card.nakWrites = 0x01
        card.nakBudget = 2
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        try await tag.writePage(0x07, [0xAA, 0, 0, 0])
        XCTAssertEqual(card.page(0x07), [0xAA, 0, 0, 0])
        XCTAssertTrue(tag.struggled)
    }

    func testFinalNakIsNotRetried() async throws {
        let card = SimulatedNTAG215()
        card.nakWrites = 0x00
        card.nakBudget = .max
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        await assertThrows { try await tag.writePage(0x08, [1, 2, 3, 4]) }
        XCTAssertEqual(card.writeCommands, 1, "the card was asked exactly once")
    }

    func testDeadLinkGivesUpAndSaysSo() async throws {
        let card = SimulatedNTAG215()
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        card.dead = true
        await assertThrows { _ = try await tag.readArea() }
        XCTAssertTrue(tag.struggled)
    }

    func testFastReadLadderFallsBackToPlainRead() async throws {
        let card = SimulatedNTAG215()
        card.refuseFastRead = true
        let tag = try await Tag215.open(card, pause: noPause)
        _ = try await tag.inspect()
        let area = try await tag.readArea()
        XCTAssertEqual(area.count, Ndef.capacity)
        XCTAssertEqual(tag.readPath, "READ 4p")
    }

    func testFastReadLadderStepsDownToWhatTheLinkCarries() async throws {
        let card = SimulatedNTAG215()
        card.maxResponseBytes = 40 // carries 8 pages, not 16
        card.answersWithCRC = false
        let tag = try await Tag215.open(LimitHiding(card), pause: noPause)
        _ = try await tag.inspect()
        let area = try await tag.readArea()
        XCTAssertEqual(area, card.area)
        XCTAssertEqual(tag.readPath, "FAST_READ 8p")
    }

    func testOpenRetriesAWeakFirstContact() async throws {
        let card = SimulatedNTAG215()
        card.failConnects = 2
        let tag = try await Tag215.open(card, pause: noPause)
        XCTAssertEqual(card.connects, 3)
        XCTAssertTrue(tag.struggled)

        let hopeless = SimulatedNTAG215()
        hopeless.failConnects = .max
        await assertThrows { _ = try await Tag215.open(hopeless, pause: noPause) }
    }

    func testFenceSendsNothingOutsideTheNdefPages() async throws {
        let card = SimulatedNTAG215()
        let tag = try await Tag215.open(card, pause: noPause)
        for page in [0x02, 0x03, 0x80, 0x83, 0x84, 0x85] {
            await assertThrows { try await tag.writePage(page, [0, 0, 0, 0]) }
        }
        await assertThrows { try await tag.writePage(0x04, [0, 0]) }
        XCTAssertEqual(card.writeCommands, 0)
        XCTAssertEqual(card.exchanges, 0)
    }

    func testNothingIsReadOrWrittenBeforeAnInspectionAllowsIt() async throws {
        let card = SimulatedNTAG215()
        let tag = try await Tag215.open(card, pause: noPause)
        await assertThrows { _ = try await tag.readArea() }
        await assertThrows { try await tag.writePage(0x05, [1, 2, 3, 4]) }
        XCTAssertEqual(card.exchanges, 0, "an uninspected card is sent nothing")

        let other = SimulatedNTAG215()
        other.version = [0x00, 0x04, 0x04, 0x02, 0x01, 0x00, 0x0F, 0x03] // NTAG213
        let foreign = try await Tag215.open(other, pause: noPause)
        await assertThrows { _ = try await foreign.inspect() }
        await assertThrows { _ = try await foreign.readArea() }
        await assertThrows { try await foreign.writePage(0x05, [1, 2, 3, 4]) }
        XCTAssertEqual(other.log, ["VERSION"], "a wrong GET_VERSION is the last thing sent")

        let locked = SimulatedNTAG215()
        locked.memory[10] = 0x08
        let refused = try await Tag215.open(locked, pause: noPause)
        let inspection = try await refused.inspect()
        XCTAssertNotNil(inspection.unsafe)
        await assertThrows { try await refused.writePage(0x05, [1, 2, 3, 4]) }
        XCTAssertEqual(locked.writeCommands, 0, "an unsafe card is never written")
    }

    func testUnsafeCardsAreNamed() async throws {
        let locked = SimulatedNTAG215()
        locked.memory[10] = 0x08
        var tag = try await Tag215.open(locked, pause: noPause)
        var inspection = try await tag.inspect()
        XCTAssertEqual(inspection.unsafe, "Lock bits are set. This app never clears or changes locks.")

        let protected = SimulatedNTAG215()
        protected.memory[0x83 * 4 + 3] = 0x10
        tag = try await Tag215.open(protected, pause: noPause)
        inspection = try await tag.inspect()
        XCTAssertNotNil(inspection.unsafe)

        let mirrored = SimulatedNTAG215()
        mirrored.memory[0x83 * 4] = 0x40
        tag = try await Tag215.open(mirrored, pause: noPause)
        inspection = try await tag.inspect()
        XCTAssertNotNil(inspection.unsafe)

        let foreignCC = SimulatedNTAG215()
        foreignCC.memory[14] = 0x6D
        tag = try await Tag215.open(foreignCC, pause: noPause)
        inspection = try await tag.inspect()
        XCTAssertNotNil(inspection.unsafe)
    }

    // MARK: Command framing (iOS)

    func testProbeFindsEachPlatformFraming() async throws {
        for (appCRC, responseCRC) in [(true, false), (true, true), (false, false), (false, true)] {
            let card = SimulatedNTAG215()
            card.requiresAppCRC = appCRC
            card.answersWithCRC = responseCRC
            let framing = await Framing.probe(card)
            XCTAssertEqual(framing, Framing(appendsCRC: appCRC, responseCarriesCRC: responseCRC))
            XCTAssertEqual(card.writeCommands, 0, "the probe never writes")
            XCTAssertTrue(card.log.allSatisfy { $0 == "VERSION" }, "the probe only sends GET_VERSION")

            let framed = FramedLink(card, framing: try XCTUnwrap(framing))
            let tag = try await Tag215.open(framed, pause: noPause)
            _ = try await tag.inspect()
            try await tag.writePage(0x05, [9, 8, 7, 6])
            XCTAssertEqual(card.page(0x05), [9, 8, 7, 6])
            let area = try await tag.readArea()
            XCTAssertEqual(area, card.area)
        }
    }

    func testProbeOnSomethingElseFindsNothing() async {
        let card = SimulatedNTAG215()
        card.dead = true
        let framing = await Framing.probe(card)
        XCTAssertNil(framing)
    }

    func testCorruptResponseCRCIsALinkErrorNotData() async throws {
        let card = SimulatedNTAG215()
        card.answersWithCRC = true
        card.truncateEvery = 2 // a truncated framed answer no longer checks
        let tag = try await Tag215.open(FramedLink(card, framing: Framing(appendsCRC: false, responseCarriesCRC: true)),
                                        pause: noPause)
        _ = try await tag.inspect()
        let area = try await tag.readArea()
        XCTAssertEqual(area, card.area)
        XCTAssertTrue(tag.struggled)
    }
}

/// Presents a link without advertising its response limit, as Core NFC does,
/// so the FAST_READ ladder has to discover it.
final class LimitHiding: Type2Link {
    let inner: Type2Link
    init(_ inner: Type2Link) { self.inner = inner }
    var maxResponseBytes: Int? { nil }
    func connect() async throws { try await inner.connect() }
    func disconnect() async { await inner.disconnect() }
    func transceive(_ command: [UInt8]) async throws -> [UInt8] { try await inner.transceive(command) }
}

func assertThrows(_ body: () async throws -> Void, file: StaticString = #filePath, line: UInt = #line) async {
    do {
        try await body()
        XCTFail("expected an error", file: file, line: line)
    } catch {}
}
