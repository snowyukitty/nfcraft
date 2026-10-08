package best.tgs.cardwriter;

import java.util.ArrayList;
import java.util.List;

/** Bounded, portable plain text. Never drops existing links or accepts partial input. */
final class LinkTransfer {
    static final int MAX_TEXT = 4096;

    static List<String> merge(List<String> existing, String text) {
        if (text == null || text.length() > MAX_TEXT)
            throw new IllegalArgumentException("Paste at most 10 HTTPS links, one per line.");
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c < 32 && c != '\n' && c != '\r' && c != '\t')
                throw new IllegalArgumentException("Remove control characters from the pasted text.");
        }
        List<String> imported = new ArrayList<>();
        int lineNumber = 0;
        for (String line : text.split("\n", -1)) {
            lineNumber++;
            String value = line.trim();
            if (value.isEmpty()) continue;
            if (Ndef.validate(value) != null)
                throw new IllegalArgumentException("Line " + lineNumber + ": enter one valid public HTTPS link (up to 200 ASCII bytes, no login or fragment).");
            if (!imported.contains(value)) imported.add(value);
            if (imported.size() > RecentUrls.LIMIT)
                throw new IllegalArgumentException("Paste at most 10 distinct links. Nothing has changed.");
        }
        if (imported.isEmpty()) throw new IllegalArgumentException("Paste at least one HTTPS link.");
        List<String> merged = new ArrayList<>(existing);
        for (String value : imported) if (!merged.contains(value)) merged.add(value);
        if (merged.size() > RecentUrls.LIMIT)
            throw new IllegalArgumentException("These links would exceed the 10-link limit. Export your existing list before clearing history, or import fewer new links. Nothing has changed.");
        return merged;
    }

    static String export(List<String> entries) {
        StringBuilder text = new StringBuilder();
        for (String entry : entries) {
            if (text.length() > 0) text.append('\n');
            text.append(entry);
        }
        return text.toString();
    }
}
