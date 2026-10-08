package best.tgs.cardwriter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;
import static org.junit.Assert.*;

public class LinkTransferTest {
    @Test public void roundTripPreservesOrderAndExactDestinations() {
        List<String> links = Arrays.asList("https://example.com/a?x=1&y=2", "https://example.com/A");
        assertEquals(links, LinkTransfer.merge(Collections.emptyList(), LinkTransfer.export(links)));
        assertEquals(links, LinkTransfer.merge(links, "\r\n https://example.com/A \r\n"));
    }

    @Test public void mergeDoesNotEvictOrReorderExistingLinks() {
        List<String> existing = new ArrayList<>();
        for (int i = 0; i < 10; i++) existing.add("https://example.com/" + i);
        assertEquals(existing, LinkTransfer.merge(existing, existing.get(9)));
        assertThrows(IllegalArgumentException.class,
                () -> LinkTransfer.merge(existing, "https://example.com/new"));
        assertEquals(10, existing.size());
        assertEquals("https://example.com/0", existing.get(0));
        assertEquals(Arrays.asList("https://example.com/old", "https://example.com/new"),
                LinkTransfer.merge(Collections.singletonList("https://example.com/old"),
                        "https://example.com/new\nhttps://example.com/old\nhttps://example.com/new"));
    }

    @Test public void hostileAndOversizedInputIsRejectedAsAWhole() {
        String[] invalid = {"", " \n ", "https://example.com\nhttp://example.com",
                "https://example.com/#fragment", "https://user:password@example.com",
                "https://example.com https://example.org", "javascript:alert(1)",
                "https://example.com/\u0000", "https://example.com/\u202e",
                new String(new char[4097]).replace('\0', ' ')};
        for (String value : invalid) assertThrows(value, IllegalArgumentException.class,
                () -> LinkTransfer.merge(Collections.emptyList(), value));
        List<String> tooMany = new ArrayList<>();
        for (int i = 0; i < 11; i++) tooMany.add("https://example.com/" + i);
        assertThrows(IllegalArgumentException.class,
                () -> LinkTransfer.merge(Collections.emptyList(), LinkTransfer.export(tooMany)));
    }
}
