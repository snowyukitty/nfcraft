package best.tgs.cardwriter;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Desktop checks for the pruned write plan.
 *
 * Pruning decides which pages travel over the radio, so it is the one part of
 * the encoder that can be wrong without the bytes on a finished card looking
 * wrong. These checks pin the two properties that matter: whatever is skipped,
 * the card ends up holding exactly the area the full plan would have left, and
 * a length is never advertised while the body is still in flight.
 *
 * Ndef has no Android dependencies, so this runs on a plain JVM.
 */
public final class PlanTest {

    private static final String[] URLS = {
            "https://tgs.best",
            "https://tgs.best/",
            "https://tap.example.com/c/AAAAAAAAAAAAAAAAAAAAAA",
            "https://a.co/x?y=1",
            "https://" + repeat("a", 60) + ".example.com/" + repeat("b", 100),
    };

    private static int checks;

    public static void main(String[] args) {
        for (String url : URLS) {
            byte[] target = Ndef.encodeArea(url);

            // A factory card shares nothing with the target, so nothing is skipped.
            byte[] factory = new byte[Ndef.NDEF_CAPACITY];
            factory[0] = 0x03;
            factory[1] = 0x00;
            factory[2] = (byte) 0xFE;
            equal("factory plan is the whole plan",
                    Ndef.writePlan(url).size(), Ndef.writePlan(url, factory).size());

            // Every prefix of the plan is a state a torn write can leave behind.
            List<Ndef.Step> full = Ndef.writePlan(url);
            for (int torn = 0; torn <= full.size(); torn++) {
                byte[] card = apply(factory, full.subList(0, torn));
                check(url, card, target);
            }

            // And so is any subset of body pages, which is what a rewrite from a
            // neighbouring destination looks like.
            Random random = new Random(20260916L + url.length());
            for (int round = 0; round < 200; round++) {
                List<Ndef.Step> some = new ArrayList<Ndef.Step>();
                for (Ndef.Step step : full) {
                    if (random.nextBoolean()) {
                        some.add(step);
                    }
                }
                check(url, apply(factory, some), target);
            }

            // Noise outside the planned region must survive untouched, and must
            // not be mistaken for a page worth skipping.
            byte[] noisy = apply(factory, full);
            noisy[Ndef.NDEF_CAPACITY - 1] = (byte) 0xAD;
            check(url, noisy, target);
        }

        System.out.println("PASS: " + checks + " pruned-plan states end at the intended area.");
    }

    /**
     * Applying the pruned plan to this card must leave the same area the full
     * plan would, and must never expose a message length before the body.
     */
    private static void check(String url, byte[] card, byte[] target) {
        List<Ndef.Step> pruned = Ndef.writePlan(url, card);

        if (pruned.isEmpty()) {
            throw new AssertionError("The plan may never be empty: the commit page is the"
                    + " evidence that the message is complete.");
        }
        Ndef.Step commit = pruned.get(pruned.size() - 1);
        equal("commit page", Ndef.FIRST_PAGE, commit.page);
        if (commit.data[1] != target[1]) {
            throw new AssertionError("The last step must be the real message length.");
        }
        for (int i = 0; i < pruned.size() - 1; i++) {
            Ndef.Step step = pruned.get(i);
            Ndef.assertSafePage(step.page, step.data);
            if (step.page == Ndef.FIRST_PAGE && step.data[1] != 0) {
                throw new AssertionError("A length was advertised before the body was written.");
            }
        }

        // The invariant the staging exists for: from the first write until the
        // commit, page 0x04 carries a zero length, so a card pulled away mid
        // plan advertises no message rather than a truncated one.
        byte[] progressive = card.clone();
        for (int i = 0; i < pruned.size() - 1; i++) {
            progressive = apply(progressive, pruned.subList(i, i + 1));
            if (progressive[1] != 0) {
                throw new AssertionError("Mid-plan the card advertised a length it cannot back.");
            }
        }

        byte[] finished = apply(card, pruned);
        byte[] expected = card.clone();
        System.arraycopy(target, 0, expected, 0, target.length);
        for (int i = 0; i < Ndef.NDEF_CAPACITY; i++) {
            if (finished[i] != expected[i]) {
                throw new AssertionError("Pruned plan for " + url + " left byte " + i
                        + " as " + (finished[i] & 0xFF) + ", not " + (expected[i] & 0xFF));
            }
        }
        checks++;
    }

    private static byte[] apply(byte[] area, List<Ndef.Step> steps) {
        byte[] out = area.clone();
        for (Ndef.Step step : steps) {
            System.arraycopy(step.data, 0, out, (step.page - Ndef.FIRST_PAGE) * 4, 4);
        }
        return out;
    }

    private static void equal(String what, int expected, int actual) {
        if (expected != actual) {
            throw new AssertionError(what + ": expected " + expected + ", got " + actual);
        }
    }

    private static String repeat(String s, int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(s);
        }
        return sb.toString();
    }

    private PlanTest() {
    }
}
