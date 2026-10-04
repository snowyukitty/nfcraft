/// The radio underneath the command layer.
///
/// On an iPhone this is an `NFCMiFareTag` from an `NFCTagReaderSession`:
/// `transceive` maps to `sendMiFareCommand(commandPacket:)`, which appends the
/// CRC itself, and `connect` to `session.connect(to:)`. In tests it is a
/// simulated NTAG215 that can be told to misbehave. Nothing in this package
/// imports Core NFC, so the decision logic is exercised without a phone.
public protocol Type2Link: AnyObject {
    /// Establish (or re-establish) the link to the tag in the field.
    func connect() async throws
    /// Drop the link. Closing a link that is already gone is not a failure.
    func disconnect() async
    /// One raw NFC-A exchange, CRC excluded in both directions.
    func transceive(_ command: [UInt8]) async throws -> [UInt8]
    /// Largest response the platform will carry, or nil when it does not say.
    var maxResponseBytes: Int? { get }
}

/// A transport failure: the exchange may be retried.
public struct LinkError: Error, Equatable, CustomStringConvertible {
    public let description: String

    public init(_ description: String) {
        self.description = description
    }
}

/// A refusal that is a property of the card, not a transport failure.
public struct Refusal: Error, Equatable {
    public let headline: String
    public let detail: String
}

/// NTAG215 command layer, ported from the Android `Tag215.java`.
///
/// The safety checks are a port of `Inspection.require_safe()` in
/// `nfcraft/adapters/base.py`. Nothing here can write outside pages
/// 0x04..0x7F, and no command that changes locks, configuration, password or
/// the capability container exists at all — not disabled, absent.
///
/// Every exchange is attempted more than once, first plainly and then after
/// re-establishing the link. Reads are idempotent; a four-byte page write is
/// too, and a write whose answer was lost is settled by reading the page back
/// rather than by assuming either outcome.
public final class Tag215 {

    /// Attempts per exchange. The first is plain; from the third on, the link
    /// is re-established first.
    static let attempts = 4

    /// Pause before each retry: long enough for a hand to settle, short enough to feel instant.
    static let backoffMilliseconds = [15, 45, 100]

    /// The identity and protected configuration this app reads but never writes.
    public struct Inspection: Equatable {
        public let version: [UInt8]
        public let uid: [UInt8]
        public let cc: [UInt8]
        public let staticLocks: [UInt8]
        public let dynamicLocks: [UInt8]
        public let cfg0: [UInt8]
        public let cfg1: [UInt8]

        /// Why this card must not be written, or nil when it is safe.
        public var unsafe: String? {
            if version != Ndef.version {
                return "Exact NTAG215 GET_VERSION response is required; no geometry guessing."
            }
            if cc != Ndef.cc {
                return "Expected writable factory NTAG215 capability container E1103E00."
            }
            if staticLocks.contains(where: { $0 != 0 }) || dynamicLocks.contains(where: { $0 != 0 }) {
                return "Lock bits are set. This app never clears or changes locks."
            }
            if cfg0[3] != 0xFF {
                return "Password-protected or unusual tag; AUTH0 is not the factory value."
            }
            if cfg0[0] & 0xC0 != 0 || cfg1[0] != 0 {
                return "Mirroring, counters, access limits or config locking are not supported."
            }
            if uid.count != 7 || uid[0] != 0x04 {
                return "Expected an NXP-style 7-byte UID. This is not an authenticity check."
            }
            return nil
        }

        public var uidHex: String {
            uid.map { Ndef.hex([$0]) }.joined(separator: ":")
        }
    }

    private let link: Type2Link
    private let pause: (Int) async -> Void

    /// Pages per FAST_READ. Halved when the link will not carry the answer.
    private var fastReadPages: Int

    public private(set) var retries: Int
    public private(set) var reconnects = 0
    public private(set) var readPath = ""

    /// Told once, the moment the link starts needing help, so the screen can
    /// ask the operator to hold still while it still matters.
    public var onStruggling: (() -> Void)?
    private var warned = false

    /// Set only by `inspect()`: exact GET_VERSION seen on this link. Every
    /// user-area read requires it.
    private var versionVerified = false
    /// Set only by `inspect()`: identity and protection passed the checks.
    /// Every write requires it.
    private var writable = false

    private init(link: Type2Link, retriesSoFar: Int, pause: @escaping (Int) async -> Void) {
        self.link = link
        self.retries = retriesSoFar
        self.pause = pause
        // Core NFC does not state a response limit, so an unknown limit starts
        // the ladder at 16 pages (64 bytes) and lets it walk down 8, 4. (The
        // Java formula gives 15 for an unknown limit, which halves to 7 and 3
        // and skips the intermediate FAST_READ sizes.)
        if let limit = link.maxResponseBytes, limit > 0 {
            self.fastReadPages = min(max((limit - 2) / 4, 1), 16)
        } else {
            self.fastReadPages = 16
        }
    }

    public static func sleep(_ milliseconds: Int) async {
        try? await Task.sleep(nanoseconds: UInt64(milliseconds) * 1_000_000)
    }

    /// Opens the link, giving a weak first contact more than one chance.
    public static func open(_ link: Type2Link,
                            pause: @escaping (Int) async -> Void = Tag215.sleep) async throws -> Tag215 {
        var last: Error?
        for attempt in 0..<attempts {
            if attempt > 0 {
                await pause(backoff(attempt))
                await link.disconnect()
            }
            do {
                try await link.connect()
                return Tag215(link: link, retriesSoFar: attempt, pause: pause)
            } catch {
                last = error
            }
        }
        throw last ?? LinkError("The card did not answer.")
    }

    /// What the link cost, for the receipt. Empty when nothing had to be repeated.
    public var effort: String {
        if retries == 0 && reconnects == 0 {
            return ""
        }
        var note = "\(retries) " + (retries == 1 ? "retry" : "retries")
        if reconnects > 0 {
            note += ", \(reconnects) " + (reconnects == 1 ? "reconnect" : "reconnects")
        }
        return note
    }

    public var struggled: Bool {
        retries > 0 || reconnects > 0
    }

    /// High pages are only touched after exact GET_VERSION evidence, so an
    /// unknown chip is never probed at addresses that may mean something else.
    public func inspect() async throws -> Inspection {
        versionVerified = false
        writable = false
        let version = try await exchange([0x60], expected: 8)
        if version != Ndef.version {
            throw Refusal(headline: "Not an NTAG215",
                          detail: "GET_VERSION does not match NTAG215, so no further pages were read.")
        }
        versionVerified = true
        let head = try await read(0x00)
        let tail = try await read(0x82)
        let inspection = Inspection(
            version: version,
            uid: Array(head[0..<3]) + Array(head[4..<8]),
            cc: Array(head[12..<16]),
            staticLocks: Array(head[10..<12]),
            dynamicLocks: Array(tail[0..<3]),
            cfg0: Array(tail[4..<8]),
            cfg1: Array(tail[8..<12]))
        writable = inspection.unsafe == nil
        return inspection
    }

    /// The whole CC-advertised NDEF area: pages 0x04..0x7F, 496 bytes. A chunk
    /// size this link will not carry walks down — 16, 8, 4 pages — before
    /// plain four-page READs take over.
    public func readArea() async throws -> [UInt8] {
        guard versionVerified else { throw NotInspected(operation: "read") }
        while fastReadPages >= 4 {
            do {
                let area = try await fastReadArea(fastReadPages)
                readPath = "FAST_READ \(fastReadPages)p"
                return area
            } catch {
                fastReadPages /= 2
            }
        }
        var out: [UInt8] = []
        out.reserveCapacity(Ndef.capacity)
        for page in stride(from: Ndef.firstPage, through: Ndef.lastNdefPage, by: 4) {
            out += try await read(page)
        }
        readPath = "READ 4p"
        return out
    }

    private func fastReadArea(_ perCall: Int) async throws -> [UInt8] {
        var out: [UInt8] = []
        out.reserveCapacity(Ndef.capacity)
        for page in stride(from: Ndef.firstPage, through: Ndef.lastNdefPage, by: perCall) {
            let end = min(Ndef.lastNdefPage, page + perCall - 1)
            out += try await exchange([0x3A, UInt8(page), UInt8(end)], expected: (end - page + 1) * 4)
        }
        return out
    }

    /// Writes one page, and does not return until the card has either
    /// confirmed it or refused it.
    ///
    /// A Type 2 WRITE answers with a four-bit ACK (0xA). How a platform
    /// surfaces that varies: some return {0x0A}, some throw, some return
    /// nothing for either an ACK or a NAK. How Core NFC surfaces it is an
    /// open device question, so every one of those shapes is handled. NAK 1h
    /// (parity/CRC) and 5h (EEPROM write) are retried; 0h and 4h are the card
    /// refusing and stop the run.
    public func writePage(_ page: Int, _ data: [UInt8]) async throws {
        guard Ndef.isSafePage(page, data) else {
            throw FenceViolation(page: page, length: data.count)
        }
        guard writable else { throw NotInspected(operation: "write") }
        let command: [UInt8] = [0xA2, UInt8(page)] + data
        var last: Error?
        for attempt in 0..<Tag215.attempts {
            if attempt > 0 {
                struggled(1)
                await pause(Tag215.backoff(attempt))
                if attempt > 1, !(await reconnect()) {
                    continue
                }
                // The answer that went missing may have been an ACK. Asking
                // the card first is the only honest way to tell.
                do {
                    if try await pageHolds(page, data) {
                        return
                    }
                } catch {
                    last = error
                    continue
                }
            }
            do {
                let response = try await link.transceive(command)
                if let first = response.first {
                    let answer = first & 0x0F
                    if answer == 0x0A {
                        return
                    }
                    if answer != 0x01 && answer != 0x05 {
                        throw Rejected(description: "The card refused the write to page \(Tag215.hexPage(page)) (NAK \(answer)).")
                    }
                    last = LinkError("The card answered NAK \(answer) for page \(Tag215.hexPage(page)).")
                    continue
                }
                // Nothing came back: an ACK not surfaced and a swallowed NAK
                // look exactly the same, so read the page back.
                if try await pageHolds(page, data) {
                    return
                }
                last = LinkError("Page \(Tag215.hexPage(page)) did not take the write"
                    + " (no acknowledgement, and the page read back differently).")
            } catch let rejected as Rejected {
                throw rejected
            } catch {
                last = error
            }
        }
        throw last ?? LinkError("Page \(Tag215.hexPage(page)) was not written.")
    }

    /// A card that answered, and said no. Never retried: the answer will not change.
    public struct Rejected: Error, Equatable, CustomStringConvertible {
        public let description: String
    }

    /// A write outside the four-byte NDEF pages 0x04..0x7F was asked for. Only
    /// a bug can get here; nothing is sent to the card.
    public struct FenceViolation: Error, Equatable {
        public let page: Int
        public let length: Int
    }

    /// A user-area read before an exact GET_VERSION, or a write before an
    /// inspection that passed, was asked for. Only a bug can get here;
    /// nothing is sent to the card.
    public struct NotInspected: Error, Equatable {
        public let operation: String
    }

    /// One unretried look at a page, used to settle what a lost answer meant.
    private func pageHolds(_ page: Int, _ data: [UInt8]) async throws -> Bool {
        let echo = try await link.transceive([0x30, UInt8(page)])
        guard echo.count == 16 else {
            throw LinkError("READ of page \(Tag215.hexPage(page)) returned \(echo.count) bytes, not 16.")
        }
        return Array(echo[0..<4]) == data
    }

    /// READ returns four consecutive pages: 16 bytes.
    private func read(_ page: Int) async throws -> [UInt8] {
        try await exchange([0x30, UInt8(page)], expected: 16)
    }

    /// One idempotent exchange, attempted until the link cooperates. A
    /// response of the wrong length is a corrupted answer, not a card with
    /// something different to say.
    private func exchange(_ command: [UInt8], expected: Int) async throws -> [UInt8] {
        var last: Error?
        for attempt in 0..<Tag215.attempts {
            if attempt > 0 {
                struggled(1)
                await pause(Tag215.backoff(attempt))
                if attempt > 1, !(await reconnect()) {
                    continue
                }
            }
            do {
                let r = try await link.transceive(command)
                if r.count != expected {
                    last = LinkError("The card answered \(r.count) bytes where \(expected) were expected.")
                    continue
                }
                return r
            } catch {
                last = error
            }
        }
        throw last ?? LinkError("The card did not answer.")
    }

    private func reconnect() async -> Bool {
        await link.disconnect()
        do {
            try await link.connect()
        } catch {
            return false
        }
        reconnects += 1
        return true
    }

    private func struggled(_ count: Int) {
        retries += count
        guard !warned, let onStruggling else { return }
        warned = true
        onStruggling()
    }

    private static func backoff(_ attempt: Int) -> Int {
        backoffMilliseconds[min(attempt - 1, backoffMilliseconds.count - 1)]
    }

    static func hexPage(_ page: Int) -> String {
        "0x" + Ndef.hex([UInt8(truncatingIfNeeded: page)])
    }
}
