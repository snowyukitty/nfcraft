/// Device-local destination choices, not evidence that a card was written.
///
/// Port of the Android `RecentUrls.java`: ten valid, distinct entries, newest
/// first, exact-string deduplication. Persistence (for example
/// `UserDefaults`) belongs to the app; this type only decides the list.
public struct RecentURLs: Equatable {
    public static let limit = 10

    public private(set) var entries: [String] = []

    public init(saved: [String] = []) {
        for value in saved {
            guard let clean = RecentURLs.clean(value), !entries.contains(clean) else { continue }
            entries.append(clean)
            if entries.count == RecentURLs.limit { break }
        }
    }

    /// Moves a valid destination to the front. Returns false, changing
    /// nothing, when the value is not a valid destination.
    @discardableResult
    public mutating func remember(_ value: String) -> Bool {
        guard let clean = RecentURLs.clean(value) else { return false }
        entries.removeAll { $0 == clean }
        entries.insert(clean, at: 0)
        if entries.count > RecentURLs.limit {
            entries.removeLast(entries.count - RecentURLs.limit)
        }
        return true
    }

    public mutating func clear() {
        entries.removeAll()
    }

    private static func clean(_ value: String) -> String? {
        let trimmed = value.trimmingASCIIWhitespace()
        return Ndef.validate(trimmed) == nil ? trimmed : nil
    }
}

extension String {
    /// Java's `String.trim()`: strips code points at or below U+0020 from both
    /// ends. Kept Foundation-free so the package builds anywhere.
    func trimmingASCIIWhitespace() -> String {
        let scalars = unicodeScalars
        guard let start = scalars.firstIndex(where: { $0.value > 0x20 }),
              let end = scalars.lastIndex(where: { $0.value > 0x20 }) else { return "" }
        return String(scalars[start...end])
    }
}
