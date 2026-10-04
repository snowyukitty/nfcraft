/// ISO/IEC 14443-3 Type A CRC (CRC_A): reflected polynomial 0x8408, initial
/// value 0x6363, no final XOR, transmitted low byte first.
public enum CRCA {
    public static func compute(_ bytes: [UInt8]) -> [UInt8] {
        var crc: UInt16 = 0x6363
        for byte in bytes {
            var b = byte ^ UInt8(crc & 0x00FF)
            b ^= b << 4
            let bb = UInt16(b)
            crc = (crc >> 8) ^ (bb << 8) ^ (bb << 3) ^ (bb >> 4)
        }
        return [UInt8(crc & 0x00FF), UInt8(crc >> 8)]
    }

    public static func append(_ bytes: [UInt8]) -> [UInt8] {
        bytes + compute(bytes)
    }

    /// True when the last two bytes are the CRC_A of everything before them.
    public static func isValid(_ framed: [UInt8]) -> Bool {
        framed.count >= 3 && Array(framed.suffix(2)) == compute(Array(framed.dropLast(2)))
    }
}

/// How raw NFC-A commands must be framed for this platform.
///
/// Apple's `sendMiFareCommand(commandPacket:)` reference (DocC, read
/// 2026-10-04) says that for `ultralight` commands the app must calculate the
/// two-byte CRC and append it. Whether responses then carry a CRC is not
/// documented. Neither is settled on real hardware yet, so the framing is
/// established per tag by a read-only GET_VERSION probe, never by trying a
/// WRITE.
public struct Framing: Equatable, CustomStringConvertible {
    /// The app appends CRC_A to every command.
    public let appendsCRC: Bool
    /// Multi-byte responses arrive with a CRC_A that must be checked and removed.
    public let responseCarriesCRC: Bool

    public static let platformHandlesCRC = Framing(appendsCRC: false, responseCarriesCRC: false)

    public var description: String {
        (appendsCRC ? "app CRC" : "platform CRC") + (responseCarriesCRC ? ", response CRC" : "")
    }

    /// Sends GET_VERSION — which changes nothing on any Type 2 tag — first
    /// as a bare command, then with an app-supplied CRC, and accepts only the
    /// exact NTAG215 version (optionally followed by a valid response CRC).
    ///
    /// The bare frame goes first on purpose. A tag never answers a frame whose
    /// CRC is missing, so if the bare command is answered the platform must
    /// have added the CRC. The reverse is ambiguous: a platform that adds its
    /// own CRC would deliver `60 F8 32` plus a second CRC, and a tag lenient
    /// about trailing bytes would still answer — after which every WRITE would
    /// carry two stray bytes. Returns nil when neither frame is answered
    /// exactly: not an NTAG215, or a link too weak to tell, and either way
    /// nothing may be written.
    public static func probe(_ link: Type2Link, rounds: Int = 2) async -> Framing? {
        for _ in 0..<rounds {
            for appendsCRC in [false, true] {
                let command: [UInt8] = appendsCRC ? CRCA.append([0x60]) : [0x60]
                guard let response = try? await link.transceive(command) else { continue }
                if response == Ndef.version {
                    return Framing(appendsCRC: appendsCRC, responseCarriesCRC: false)
                }
                if response.count == Ndef.version.count + 2, CRCA.isValid(response),
                   Array(response.prefix(Ndef.version.count)) == Ndef.version {
                    return Framing(appendsCRC: appendsCRC, responseCarriesCRC: true)
                }
            }
        }
        return nil
    }
}

/// Applies a `Framing` to a platform link, so the command layer above it
/// always speaks CRC-free Type 2.
public final class FramedLink: Type2Link {
    private let inner: Type2Link
    public let framing: Framing

    public init(_ inner: Type2Link, framing: Framing) {
        self.inner = inner
        self.framing = framing
    }

    public var maxResponseBytes: Int? {
        inner.maxResponseBytes.map { framing.responseCarriesCRC ? $0 - 2 : $0 }
    }

    public func connect() async throws {
        try await inner.connect()
    }

    public func disconnect() async {
        await inner.disconnect()
    }

    public func transceive(_ command: [UInt8]) async throws -> [UInt8] {
        let response = try await inner.transceive(framing.appendsCRC ? CRCA.append(command) : command)
        // A four-bit ACK/NAK never carries a CRC, and an empty answer has none to check.
        guard framing.responseCarriesCRC, response.count > 1 else { return response }
        guard CRCA.isValid(response) else {
            throw LinkError("Response CRC did not check.")
        }
        return Array(response.dropLast(2))
    }
}
