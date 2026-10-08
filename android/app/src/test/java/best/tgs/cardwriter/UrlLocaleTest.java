package best.tgs.cardwriter;

import org.junit.Test;
import java.util.Locale;
import static org.junit.Assert.*;

public class UrlLocaleTest {
    @Test public void uppercaseAsciiHostsWorkInTurkishWithoutChangingThePayload() {
        Locale original = Locale.getDefault();
        try {
            Locale.setDefault(new Locale("tr", "TR"));
            String url = "https://INDIGO.example/Path?Case=I";
            assertNull(Ndef.validate(url));
            assertEquals(url, Ndef.decodeArea(Ndef.encodeArea(url)));
        } finally {
            Locale.setDefault(original);
        }
    }
}
