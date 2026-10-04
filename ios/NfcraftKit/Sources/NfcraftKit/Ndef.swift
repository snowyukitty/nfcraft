/// Deliberately narrow NFC Forum Type 2, single HTTPS URI encoder.
///
/// A port of `nfcraft/ndef.py` by way of the Android `Ndef.java`. The rules are
/// intentionally identical so a card written by an iPhone, an Android phone or
/// the PC/SC path carries byte-for-byte the same area, and still decodes under
/// the Python tooling. `ios/tools/check.sh` diffs this against the Python
/// reference; keep all three in step if any of them changes.
public enum Ndef {

    public static let cc: [UInt8] = [0xE1, 0x10, 0x3E, 0x00]
    public static let version: [UInt8] = [0x00, 0x04, 0x04, 0x02, 0x01, 0x00, 0x11, 0x03]

    public static let capacity = 496
    public static let firstPage = 0x04
    public static let lastNdefPage = 0x7F
    public static let maxURLBytes = 200

    /// One four-byte page write.
    public struct Step: Equatable {
        public let page: Int
        public let data: [UInt8]

        public init(page: Int, data: [UInt8]) {
            self.page = page
            self.data = data
        }
    }

    public enum EncodeError: Error, Equatable {
        case invalid(String)
        case tooLarge(String)
    }

    /// Returns a human-readable problem, or nil when the URL is acceptable.
    /// Mirrors `validate_https()` without the production-domain checks, which
    /// belong to the desktop provisioning flow rather than a rewrite tool.
    public static func validate(_ url: String) -> String? {
        if url.isEmpty {
            return "Enter an HTTPS destination."
        }
        if url.unicodeScalars.contains(where: { $0.value < 33 || $0.value >= 127 }) {
            return "Use an ASCII HTTPS URL; encode Unicode with IDNA or percent escapes."
        }
        // ASCII from here on, so scalars, UTF-8 bytes and characters coincide.
        let bytes = Array(url.utf8)
        if bytes.count > maxURLBytes {
            return "URL is too long (maximum \(maxURLBytes) bytes)."
        }
        if bytes.contains(UInt8(ascii: "\\")) {
            return "URL contains a backslash."
        }
        if !url.hasPrefix("https://") {
            return "An HTTPS URL is required."
        }
        if bytes.contains(UInt8(ascii: "#")) {
            return "An HTTPS URL without a fragment is required."
        }
        let rest = bytes[8...]
        let cut = rest.firstIndex { $0 == UInt8(ascii: "/") || $0 == UInt8(ascii: "?") } ?? rest.endIndex
        let authority = Array(rest[rest.startIndex..<cut])
        if authority.contains(UInt8(ascii: "@")) {
            return "An HTTPS URL without credentials is required."
        }
        var host = authority
        if let colon = authority.lastIndex(of: UInt8(ascii: ":")) {
            host = Array(authority[..<colon])
            // As urlsplit() reads it: an empty port means the default, and a
            // present one must be ASCII digits in 0...65535. (The Java port
            // differs on both; ios/tools/parity-cases.json pins this side.)
            let port = authority[(colon + 1)...]
            if !port.isEmpty {
                guard port.allSatisfy({ $0 >= UInt8(ascii: "0") && $0 <= UInt8(ascii: "9") }),
                      port.reduce(0, { min($0 * 10 + Int($1 - UInt8(ascii: "0")), 65_536) }) <= 65_535 else {
                    return "Malformed port."
                }
            }
        }
        host = host.map { $0 >= UInt8(ascii: "A") && $0 <= UInt8(ascii: "Z") ? $0 + 32 : $0 }
        if host.isEmpty || host.count > 253 {
            return "Use a valid ASCII DNS hostname."
        }
        for label in host.split(separator: UInt8(ascii: "."), omittingEmptySubsequences: false)
        where !isDnsLabel(Array(label)) {
            return "Use a valid ASCII DNS hostname."
        }
        return nil
    }

    private static func isDnsLabel(_ label: [UInt8]) -> Bool {
        let n = label.count
        guard (1...63).contains(n) else { return false }
        for (i, c) in label.enumerated() {
            let alnum = (c >= UInt8(ascii: "a") && c <= UInt8(ascii: "z"))
                || (c >= UInt8(ascii: "0") && c <= UInt8(ascii: "9"))
            if !alnum && !(c == UInt8(ascii: "-") && i > 0 && i < n - 1) {
                return false
            }
        }
        return true
    }

    /// A single short URI record using NFC URI prefix code 0x04 (https://).
    static func uriRecord(_ url: String) -> [UInt8] {
        let rest = Array(url.utf8.dropFirst(8))
        return [0xD1, 0x01, UInt8(1 + rest.count), 0x55, 0x04] + rest
    }

    /// The exact bytes the NDEF area should hold, padded to whole pages.
    ///
    /// Like `encode_area()` in the Python reference, and unlike the Java port,
    /// an invalid URL is refused here rather than left to the caller.
    public static func encodeArea(_ url: String) throws -> [UInt8] {
        if let problem = validate(url) {
            throw EncodeError.invalid(problem)
        }
        let record = uriRecord(url)
        if record.count >= 255 {
            throw EncodeError.tooLarge("Only short NDEF TLVs are supported.")
        }
        let areaLength = 1 + 1 + record.count + 1
        let padded = areaLength + ((4 - (areaLength % 4)) % 4)
        if padded > capacity {
            throw EncodeError.tooLarge("Payload exceeds the NTAG215 CC-advertised area.")
        }
        var area = [UInt8](repeating: 0, count: padded)
        area[0] = 0x03
        area[1] = UInt8(record.count)
        area.replaceSubrange(2..<(2 + record.count), with: record)
        area[2 + record.count] = 0xFE
        return area
    }

    /// Strictly decode our own canonical record, or nil. Arbitrary tag data is
    /// deliberately not interpreted: anything this does not recognise is
    /// treated as unfamiliar content, not as something safe to replace.
    public static func decodeArea(_ area: [UInt8]) -> String? {
        guard area.count >= 8, area[0] == 0x03, area[1] != 0 else { return nil }
        let n = Int(area[1])
        guard area.count >= n + 3, n >= 5 else { return nil }
        let r = Array(area[2..<(2 + n)])
        guard r[0] == 0xD1, r[1] == 0x01, r[3] == 0x55, r[4] == 0x04 else { return nil }
        guard Int(r[2]) == r.count - 4 else { return nil }
        guard area[n + 2] == 0xFE else { return nil }
        let tail = r[5...]
        // US-ASCII only; anything else is not a record this app wrote.
        guard tail.allSatisfy({ $0 < 0x80 }) else { return nil }
        let url = "https://" + String(decoding: tail, as: UTF8.self)
        return validate(url) == nil ? url : nil
    }

    /// Factory-initialised empty TLV, or an all-zero unpopulated user area.
    public static func isEmpty(_ area: [UInt8]) -> Bool {
        guard area.count == capacity else { return false }
        if area[0] == 0x03 && area[1] == 0x00 && area[2] == 0xFE {
            return true
        }
        return area.allSatisfy { $0 == 0 }
    }

    /// True when an empty TLV is hiding data inside the region about to be written.
    public static func hidesDataUnderEmptyTlv(_ area: [UInt8], plannedLength: Int) -> Bool {
        guard area.count >= 3, area[0] == 0x03, area[1] == 0x00, area[2] == 0xFE else { return false }
        let end = min(plannedLength, area.count)
        guard end > 3 else { return false }
        return area[3..<end].contains { $0 != 0 }
    }

    /// True when the card holds the staged first page this tool writes before
    /// the body — `03 00` followed by the target's own record header — so an
    /// interrupted write by this app can be finished without the override.
    public static func isOurStagedWrite(_ area: [UInt8], target: [UInt8]) -> Bool {
        area.count >= 4 && target.count >= 4
            && area[0] == 0x03 && area[1] == 0x00
            && area[2] == target[2] && area[3] == target[3]
    }

    /// Expose an empty message first; make the message length visible only
    /// after the body is in place. This reduces partially advertised records.
    /// It does NOT make EEPROM writes atomic.
    public static func writePlan(_ url: String) throws -> [Step] {
        let target = try encodeArea(url)
        var steps = [Step(page: firstPage, data: [target[0], 0x00, target[2], target[3]])]
        for i in stride(from: 4, to: target.count, by: 4) {
            steps.append(Step(page: firstPage + i / 4, data: Array(target[i..<(i + 4)])))
        }
        steps.append(Step(page: firstPage, data: Array(target[0..<4])))
        return steps
    }

    /// The same plan with the pages the card already holds left out. The
    /// commit step is always kept and always last; the staged step is dropped
    /// only when the card already advertises a zero-length message, so no
    /// length is ever visible while the body is in flight.
    public static func writePlan(_ url: String, current: [UInt8]?) throws -> [Step] {
        let full = try writePlan(url)
        guard let current, current.count >= capacity else { return full }
        var pruned: [Step] = []
        for (i, step) in full.enumerated() {
            if i < full.count - 1 && alreadyHolds(current, step) {
                continue
            }
            pruned.append(step)
        }
        return pruned
    }

    private static func alreadyHolds(_ area: [UInt8], _ step: Step) -> Bool {
        let offset = (step.page - firstPage) * 4
        guard offset >= 0, offset + 4 <= area.count else { return false }
        return Array(area[offset..<(offset + 4)]) == step.data
    }

    /// The write fence. Every page write passes through here first.
    public static func isSafePage(_ page: Int, _ data: [UInt8]) -> Bool {
        page >= firstPage && page <= lastNdefPage && data.count == 4
    }

    public static func hex(_ bytes: [UInt8]) -> String {
        let digits = Array("0123456789ABCDEF")
        var out = ""
        out.reserveCapacity(bytes.count * 2)
        for b in bytes {
            out.append(digits[Int(b >> 4)])
            out.append(digits[Int(b & 0x0F)])
        }
        return out
    }
}
