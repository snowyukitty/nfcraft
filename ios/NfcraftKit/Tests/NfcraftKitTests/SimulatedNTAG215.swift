@testable import NfcraftKit
import XCTest

/// An NTAG215 whose radio can be told to misbehave, in the manner of the
/// Android `LinkTest.Card`. Only the commands the app is allowed to issue are
/// implemented; anything else fails the test, which is itself the check that
/// the app issues nothing else. This is a fixture, never device evidence.
final class SimulatedNTAG215: Type2Link {
    static let pages = 135

    var memory = [UInt8](repeating: 0, count: pages * 4)
    var log: [String] = []

    var connects = 0
    var failConnects = 0
    var exchanges = 0
    var writeCommands = 0
    var writtenPages: [Int] = []

    var dropEvery = 0
    var truncateEvery = 0
    var swallowAcks = false
    var ignoreWrites = false
    var refuseFastRead = false
    var dead = false
    var nakWrites: UInt8?
    var nakBudget = 0
    /// The card leaves the field after this many WRITE commands have landed.
    var leaveAfterWrites: Int?
    /// The card acknowledges this many WRITEs, then leaves the field.
    var leaveAfterAcks: Int?
    /// The card leaves the field when this exchange arrives (1-based).
    var leaveAtExchange: Int?
    /// READ of these pages never gets an answer.
    var silentReadPages: Set<Int> = []
    /// What GET_VERSION answers.
    var version = Ndef.version
    /// Answer GET_VERSION differently once a WRITE has landed.
    var changeVersionOnWrite = false
    /// Suspend every exchange this long, so overlapping presentations overlap.
    var exchangeDelayMilliseconds = 0
    /// Change CFG0 the moment the first WRITE lands, to fake an identity change.
    var mutateConfigOnWrite = false
    var maxResponseBytes: Int?

    /// Platform framing: the link only understands commands carrying CRC_A.
    var requiresAppCRC = false
    /// Platform framing: multi-byte answers come back with their CRC_A.
    var answersWithCRC = false
    /// A tag that ignores trailing bytes after a complete command, instead of
    /// staying silent on a wrong-length frame.
    var lenientLength = false

    init() {
        var head: [UInt8] = [0x04, 0x11, 0x22, 0x00, 0x33, 0x44, 0x55, 0x66,
                             0x00, 0x00, 0x00, 0x00, 0xE1, 0x10, 0x3E, 0x00]
        head[3] = 0x88 ^ head[0] ^ head[1] ^ head[2]
        head[8] = head[4] ^ head[5] ^ head[6] ^ head[7]
        memory.replaceSubrange(0..<16, with: head)
        // An empty NDEF TLV, as a factory card carries.
        memory[16] = 0x03
        memory[17] = 0x00
        memory[18] = 0xFE
        // CFG0 at page 0x83 with the factory AUTH0.
        memory[0x83 * 4 + 3] = 0xFF
    }

    func page(_ page: Int) -> [UInt8] {
        Array(memory[(page * 4)..<(page * 4 + 4)])
    }

    var area: [UInt8] {
        get { Array(memory[16..<(16 + Ndef.capacity)]) }
        set { memory.replaceSubrange(16..<(16 + Ndef.capacity), with: newValue) }
    }

    func connect() async throws {
        connects += 1
        if dead { throw LinkError("Simulated: no card in the field.") }
        if failConnects > 0 {
            failConnects -= 1
            throw LinkError("Simulated weak coupling on connect.")
        }
    }

    func disconnect() async {}

    func transceive(_ framed: [UInt8]) async throws -> [UInt8] {
        exchanges += 1
        if exchangeDelayMilliseconds > 0 { await Tag215.sleep(exchangeDelayMilliseconds) }
        if let leave = leaveAtExchange, exchanges >= leave {
            dead = true
        }
        if dead { throw LinkError("Simulated dead link.") }
        var command = framed
        if requiresAppCRC {
            // A tag that does not get a valid CRC_A stays silent.
            guard CRCA.isValid(framed) else { throw LinkError("Simulated timeout: no CRC.") }
            command = Array(framed.dropLast(2))
        }
        if dropEvery > 0 && exchanges % dropEvery == 0 {
            throw LinkError("Simulated lost exchange.")
        }
        var answer = try answer(command)
        if answersWithCRC && answer.count > 1 {
            answer = CRCA.append(answer)
        }
        if truncateEvery > 0 && exchanges % truncateEvery == 0 && answer.count > 1 {
            return Array(answer.dropLast())
        }
        return answer
    }

    private func answer(_ received: [UInt8]) throws -> [UInt8] {
        let lengths: [UInt8: Int] = [0x60: 1, 0x30: 2, 0x3A: 3, 0xA2: 6]
        guard let op = received.first, let length = lengths[op] else {
            XCTFail("The app issued an unexpected command: \(Ndef.hex(received))")
            throw LinkError("unexpected command")
        }
        if received.count != length && !(lenientLength && received.count > length) {
            throw LinkError("Simulated: a wrong-length frame gets no answer.")
        }
        let command = Array(received.prefix(length))
        switch command.first {
        case 0x60:
            XCTAssertEqual(command.count, 1, "GET_VERSION carries no argument")
            log.append("VERSION")
            return version
        case 0x30:
            XCTAssertEqual(command.count, 2)
            let page = Int(command[1])
            if silentReadPages.contains(page) {
                throw LinkError("Simulated: no answer to READ \(page).")
            }
            log.append("READ \(page)")
            return (0..<16).map { memory[(page * 4 + $0) % memory.count] }
        case 0x3A:
            XCTAssertEqual(command.count, 3)
            if refuseFastRead { throw LinkError("This card does not answer FAST_READ.") }
            let from = Int(command[1]), to = Int(command[2])
            if let max = maxResponseBytes, (to - from + 1) * 4 > max {
                throw LinkError("Simulated: response longer than the link carries.")
            }
            log.append("FAST_READ \(from)..\(to)")
            return Array(memory[(from * 4)..<((to + 1) * 4)])
        case 0xA2:
            XCTAssertEqual(command.count, 6)
            let page = Int(command[1])
            guard (Ndef.firstPage...Ndef.lastNdefPage).contains(page) else {
                XCTFail("WRITE outside the NDEF fence: page \(page)")
                throw LinkError("fence")
            }
            writeCommands += 1
            log.append("WRITE \(page)")
            if let nak = nakWrites, nakBudget > 0 {
                nakBudget -= 1
                return [nak]
            }
            if !ignoreWrites {
                memory.replaceSubrange((page * 4)..<(page * 4 + 4), with: command[2..<6])
                writtenPages.append(page)
            }
            if changeVersionOnWrite {
                version = [0x00, 0x04, 0x04, 0x02, 0x01, 0x00, 0x13, 0x03] // NTAG216
            }
            if mutateConfigOnWrite {
                memory[0x83 * 4] = 0x40
            }
            if let limit = leaveAfterWrites, writtenPages.count >= limit {
                dead = true
                throw LinkError("Simulated: card left the field.")
            }
            if let acks = leaveAfterAcks, writtenPages.count >= acks {
                dead = true
            }
            return swallowAcks ? [] : [0x0A]
        default:
            XCTFail("The app issued an unexpected command: \(Ndef.hex(command))")
            throw LinkError("unexpected command")
        }
    }
}

/// Retries in tests must not wait for real time.
let noPause: (Int) async -> Void = { _ in }
