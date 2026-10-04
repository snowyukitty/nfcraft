@testable import NfcraftKit
import XCTest

/// Port of HistoryTest.java: retention, exact URL identity, restoration and clear.
final class HistoryTests: XCTestCase {

    func testRetentionReuseValidationRestoreAndClear() {
        var history = RecentURLs()
        XCTAssertFalse(history.remember("http://example.com"), "refuse insecure URL")
        XCTAssertFalse(history.remember("https://user:pass@example.com"), "refuse credentials")
        XCTAssertFalse(history.remember("https://example.com/#fragment"), "same encoder rules")
        XCTAssertFalse(history.remember(" "), "ignore blanks")
        XCTAssertTrue(history.entries.isEmpty, "invalid drafts never enter history")
        for i in 0..<12 { history.remember("https://example.com/\(i)") }
        XCTAssertEqual(history.entries.count, 10, "bound at ten")
        XCTAssertTrue(history.entries[0].hasSuffix("/11"), "newest first")
        XCTAssertTrue(history.entries[9].hasSuffix("/2"), "evict oldest")
        let snapshot = history.entries
        history.remember("  https://example.com/5  ")
        XCTAssertEqual(history.entries.count, 10, "deduplicate trimmed URL")
        XCTAssertTrue(history.entries[0].hasSuffix("/5"), "reuse moves to front")
        XCTAssertTrue(snapshot[0].hasSuffix("/11"), "a list snapshot stays stable")
        var restored = RecentURLs(saved: history.entries)
        XCTAssertEqual(restored.entries, history.entries, "restart preserves order")
        restored.clear()
        XCTAssertTrue(RecentURLs(saved: restored.entries).entries.isEmpty, "clear survives restart")
        var dirty = RecentURLs(saved: ["bad", "https://example.com/A", "https://example.com/A",
                                       "https://example.com/a", "https://example.com/?x=1",
                                       "https://example.com/?x=2"])
        XCTAssertEqual(dirty.entries.count, 4, "restore drops invalid and duplicates, keeps exact paths and queries")
        XCTAssertTrue(dirty.remember("https://example.com/new"), "saving after clear remains possible")
    }

    func testRestoreStopsAtTheLimit() {
        let saved = (0..<15).map { "https://example.com/\($0)" }
        XCTAssertEqual(RecentURLs(saved: saved).entries, Array(saved.prefix(10)))
    }

    func testTrimMatchesJava() {
        XCTAssertEqual("\t https://a.co \n".trimmingASCIIWhitespace(), "https://a.co")
        XCTAssertEqual("   ".trimmingASCIIWhitespace(), "")
    }
}
