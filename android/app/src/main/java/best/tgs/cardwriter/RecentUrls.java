package best.tgs.cardwriter;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Device-local destination choices, not evidence that a card was written. */
final class RecentUrls {
    static final int LIMIT = 10;
    private final List<String> values = new ArrayList<>();

    RecentUrls(List<String> saved) {
        for (String value : saved) {
            String clean = clean(value);
            if (clean != null && !values.contains(clean)) values.add(clean);
            if (values.size() == LIMIT) break;
        }
    }

    boolean remember(String value) {
        String clean = clean(value);
        if (clean == null) return false;
        values.remove(clean);
        values.add(0, clean);
        if (values.size() > LIMIT) values.remove(LIMIT);
        return true;
    }

    List<String> entries() {
        return Collections.unmodifiableList(new ArrayList<>(values));
    }

    void clear() {
        values.clear();
    }

    private static String clean(String value) {
        if (value == null) return null;
        String trimmed = value.trim();
        return Ndef.validate(trimmed) == null ? trimmed : null;
    }
}
