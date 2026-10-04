@testable import NfcraftKit
import XCTest

/// Encoder, pruned-plan and CRC_A checks. Byte parity with the Python
/// reference is checked separately by ios/tools/check.sh.
final class NdefTests: XCTestCase {

    static let urls = [
        "https://tgs.best",
        "https://tgs.best/",
        "https://tap.example.com/c/AAAAAAAAAAAAAAAAAAAAAA",
        "https://a.co/x?y=1",
        "https://" + String(repeating: "a", count: 60) + ".example.com/" + String(repeating: "b", count: 100),
    ]

    func testKnownAreaBytes() throws {
        // Value printed by nfcraft/ndef.py encode_area("https://tgs.best").
        XCTAssertEqual(Ndef.hex(try Ndef.encodeArea("https://tgs.best")),
                       "030DD1010955047467732E62657374FE")
    }

    func testRoundTripAndEmptiness() throws {
        for url in Self.urls {
            var full = [UInt8](repeating: 0, count: Ndef.capacity)
            let area = try Ndef.encodeArea(url)
            full.replaceSubrange(0..<area.count, with: area)
            XCTAssertEqual(Ndef.decodeArea(full), url)
            XCTAssertFalse(Ndef.isEmpty(full))
        }
        XCTAssertTrue(Ndef.isEmpty([UInt8](repeating: 0, count: Ndef.capacity)))
        XCTAssertFalse(Ndef.isEmpty([UInt8](repeating: 0, count: Ndef.capacity - 1)))
    }

    func testEncoderRefusesInvalidAndOversized() {
        XCTAssertThrowsError(try Ndef.encodeArea("http://tgs.best"))
        XCTAssertThrowsError(try Ndef.encodeArea("https://a.co/" + String(repeating: "x", count: 188)))
        XCTAssertNoThrow(try Ndef.encodeArea("https://a.co/" + String(repeating: "x", count: 187)))
    }

    func testDecodeRejectsForeignAndMalformedRecords() throws {
        var area = [UInt8](repeating: 0, count: Ndef.capacity)
        let good = try Ndef.encodeArea("https://tgs.best")
        area.replaceSubrange(0..<good.count, with: good)
        var wrongPrefix = area
        wrongPrefix[6] = 0x03 // http:// rather than https://
        XCTAssertNil(Ndef.decodeArea(wrongPrefix))
        var noTerminator = area
        noTerminator[Int(area[1]) + 2] = 0x00 // the FE right after the record; the URL stays intact
        XCTAssertNil(Ndef.decodeArea(noTerminator))
        var nonASCII = area
        nonASCII[8] = 0xC3
        XCTAssertNil(Ndef.decodeArea(nonASCII))
        var badLength = area
        badLength[1] = 0xFF
        XCTAssertNil(Ndef.decodeArea(badLength))
        XCTAssertNil(Ndef.decodeArea([0x03, 0x05]))
    }

    func testRecoveryMatchesOnlyThisOperationsPages() throws {
        let target = try Ndef.encodeArea("https://tgs.best/next")
        var original = [UInt8](repeating: 0, count: Ndef.capacity)
        let old = try Ndef.encodeArea("https://tgs.best/")
        original.replaceSubrange(0..<old.count, with: old)
        original[300] = 0x77
        let staged: [UInt8] = [0x03, 0x00, target[2], target[3]]

        var torn = original
        torn.replaceSubrange(0..<4, with: staged)
        torn.replaceSubrange(4..<12, with: target[4..<12])
        XCTAssertTrue(Ndef.recoveryMatches(current: torn, original: original, target: target))
        XCTAssertTrue(Ndef.recoveryMatches(current: original, original: original, target: target))

        var foreignBody = torn
        foreignBody[13] = 0xEE
        XCTAssertFalse(Ndef.recoveryMatches(current: foreignBody, original: original, target: target))
        var changedTail = torn
        changedTail[300] = 0x00
        XCTAssertFalse(Ndef.recoveryMatches(current: changedTail, original: original, target: target))
        XCTAssertFalse(Ndef.recoveryMatches(current: Array(torn.dropLast()), original: original, target: target))
    }

    func testFenceAcceptsOnlyNdefPages() {
        XCTAssertTrue(Ndef.isSafePage(0x04, [0, 0, 0, 0]))
        XCTAssertTrue(Ndef.isSafePage(0x7F, [0, 0, 0, 0]))
        for page in [0x00, 0x02, 0x03, 0x80, 0x82, 0x83, 0x84, 0x85, 0x86] {
            XCTAssertFalse(Ndef.isSafePage(page, [0, 0, 0, 0]), "page \(page)")
        }
        XCTAssertFalse(Ndef.isSafePage(0x04, [0, 0, 0]))
    }

    // MARK: Pruned plan — a port of PlanTest.java

    func testEveryTornAndPartialStateEndsAtTheIntendedArea() throws {
        var checks = 0
        for url in Self.urls {
            let target = try Ndef.encodeArea(url)
            var factory = [UInt8](repeating: 0, count: Ndef.capacity)
            factory[0] = 0x03; factory[2] = 0xFE
            let full = try Ndef.writePlan(url)
            XCTAssertEqual(try Ndef.writePlan(url, current: factory).count, full.count)

            for torn in 0...full.count {
                try check(url, apply(factory, full[0..<torn]), target); checks += 1
            }
            var rng = SplitMix64(seed: 20_260_916 &+ UInt64(url.count))
            for _ in 0..<200 {
                try check(url, apply(factory, full.filter { _ in rng.next() & 1 == 1 }[...]), target); checks += 1
            }
            var noisy = apply(factory, full[...])
            noisy[Ndef.capacity - 1] = 0xAD
            try check(url, noisy, target); checks += 1
        }
        XCTAssertGreaterThan(checks, 1000)
    }

    private func check(_ url: String, _ card: [UInt8], _ target: [UInt8]) throws {
        let pruned = try Ndef.writePlan(url, current: card)
        let commit = try XCTUnwrap(pruned.last, "the commit page is the evidence the message is complete")
        XCTAssertEqual(commit.page, Ndef.firstPage)
        XCTAssertEqual(commit.data[1], target[1], "the last step must carry the real length")
        var progressive = card
        for step in pruned.dropLast() {
            XCTAssertTrue(Ndef.isSafePage(step.page, step.data))
            progressive = apply(progressive, [step][...])
            XCTAssertEqual(progressive[1], 0, "mid-plan the card advertised a length it cannot back")
        }
        var expected = card
        expected.replaceSubrange(0..<target.count, with: target)
        XCTAssertEqual(apply(card, pruned[...]), expected, url)
    }

    private func apply(_ area: [UInt8], _ steps: ArraySlice<Ndef.Step>) -> [UInt8] {
        var out = area
        for step in steps {
            let offset = (step.page - Ndef.firstPage) * 4
            out.replaceSubrange(offset..<(offset + 4), with: step.data)
        }
        return out
    }

    // MARK: CRC_A

    func testCRCAKnownVectors() {
        // Published ISO 14443-3 / NXP frames: GET_VERSION, READ page 0, HLTA.
        XCTAssertEqual(CRCA.append([0x60]), [0x60, 0xF8, 0x32])
        XCTAssertEqual(CRCA.append([0x30, 0x00]), [0x30, 0x00, 0x02, 0xA8])
        XCTAssertEqual(CRCA.append([0x50, 0x00]), [0x50, 0x00, 0x57, 0xCD])
        XCTAssertTrue(CRCA.isValid([0x30, 0x00, 0x02, 0xA8]))
        XCTAssertFalse(CRCA.isValid([0x30, 0x00, 0x02, 0xA9]))
        XCTAssertFalse(CRCA.isValid([0x0A]))
    }
}

/// Deterministic generator so the random plan states are reproducible.
struct SplitMix64 {
    var state: UInt64
    init(seed: UInt64) { state = seed }
    mutating func next() -> UInt64 {
        state &+= 0x9E37_79B9_7F4A_7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58_476D_1CE4_E5B9
        z = (z ^ (z >> 27)) &* 0x94D0_49BB_1331_11EB
        return z ^ (z >> 31)
    }
}
