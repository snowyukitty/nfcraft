package best.tgs.cardwriter;

import java.util.List;

/**
 * Prints the Java encoder's output so it can be diffed against nfcraft/ndef.py.
 * Desktop-only; Ndef has no Android dependencies.
 */
public final class Harness {

    private static final String[] URLS = {
            "https://tgs.best",
            "https://tgs.best/",
            "https://tap.example.com/c/AAAAAAAAAAAAAAAAAAAAAA",
            "https://a.co/x?y=1",
            "https://" + repeat("a", 60) + ".example.com/" + repeat("b", 100),
    };

    private static final String[] BAD = {
            "http://tgs.best",
            "https://",
            "https://tgs.best#f",
            "https://user:pw@tgs.best",
            "https://-bad.example.com",
            "https://tgs.best\\x",
            "https://" + repeat("a", 200),
            "https://æ.example.com",
    };

    public static void main(String[] args) {
        for (String url : URLS) {
            System.out.println("URL " + url);
            System.out.println("  validate " + Ndef.validate(url));
            byte[] area = Ndef.encodeArea(url);
            System.out.println("  area " + Ndef.hex(area));
            List<Ndef.Step> plan = Ndef.writePlan(url);
            StringBuilder sb = new StringBuilder();
            for (Ndef.Step step : plan) {
                sb.append(String.format("%02X", step.page)).append(':')
                        .append(Ndef.hex(step.data)).append(' ');
            }
            System.out.println("  plan " + sb.toString().trim());
            byte[] full = new byte[Ndef.NDEF_CAPACITY];
            System.arraycopy(area, 0, full, 0, area.length);
            System.out.println("  decode " + Ndef.decodeArea(full));
            System.out.println("  empty " + Ndef.isEmpty(full));
        }
        // Indexed, not echoed: one case is deliberately non-ASCII and a
        // console encoding must not show up as an encoder difference.
        for (int i = 0; i < BAD.length; i++) {
            System.out.println("BAD[" + i + "] rejected " + (Ndef.validate(BAD[i]) != null));
        }
        byte[] blank = new byte[Ndef.NDEF_CAPACITY];
        System.out.println("blank empty " + Ndef.isEmpty(blank));
        blank[0] = 0x03;
        blank[1] = 0x00;
        blank[2] = (byte) 0xFE;
        System.out.println("emptytlv empty " + Ndef.isEmpty(blank));
        System.out.println("emptytlv hides " + Ndef.hidesDataUnderEmptyTlv(blank, 24));
        blank[9] = 0x41;
        System.out.println("emptytlv+data empty " + Ndef.isEmpty(blank));
        System.out.println("emptytlv+data hides " + Ndef.hidesDataUnderEmptyTlv(blank, 24));
        System.out.println("emptytlv+data hides(short) " + Ndef.hidesDataUnderEmptyTlv(blank, 8));
    }

    private static String repeat(String s, int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(s);
        }
        return sb.toString();
    }
}
