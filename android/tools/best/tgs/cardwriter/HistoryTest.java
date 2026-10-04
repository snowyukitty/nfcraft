package best.tgs.cardwriter;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Regression checks for retention, exact URL identity, restoration and clear. */
public final class HistoryTest {
    private static void require(boolean pass, String label) {
        if (!pass) throw new AssertionError(label);
    }

    public static void main(String[] args) {
        RecentUrls history = new RecentUrls(Collections.emptyList());
        require(!history.remember("http://example.com"), "refuse insecure URL");
        require(!history.remember("https://user:pass@example.com"), "refuse credentials");
        require(!history.remember("https://example.com/#fragment"), "same encoder rules");
        require(!history.remember(null) && !history.remember(" "), "ignore blanks");
        require(history.entries().isEmpty(), "invalid drafts never enter history");
        for (int i = 0; i < 12; i++) history.remember("https://example.com/" + i);
        require(history.entries().size() == 10, "bound at ten");
        require(history.entries().get(0).endsWith("/11"), "newest first");
        require(history.entries().get(9).endsWith("/2"), "evict oldest");
        List<String> snapshot = history.entries();
        history.remember("  https://example.com/5  ");
        require(history.entries().size() == 10, "deduplicate trimmed URL");
        require(history.entries().get(0).endsWith("/5"), "reuse moves to front");
        require(snapshot.get(0).endsWith("/11"), "dialog snapshot stays stable");
        RecentUrls restored = new RecentUrls(history.entries());
        require(restored.entries().equals(history.entries()), "restart preserves order");
        restored.clear();
        require(new RecentUrls(restored.entries()).entries().isEmpty(), "clear survives restart");
        RecentUrls dirty = new RecentUrls(Arrays.asList(null, "bad", "https://example.com/A",
                "https://example.com/A", "https://example.com/a", "https://example.com/?x=1",
                "https://example.com/?x=2"));
        require(dirty.entries().size() == 4, "restore drops invalid and duplicates, preserves exact paths and queries");
        require(dirty.remember("https://example.com/new"), "saving after clear remains possible");
        System.out.println("PASS: history retention, reuse, validation, restore, snapshots and clear");
    }
}
