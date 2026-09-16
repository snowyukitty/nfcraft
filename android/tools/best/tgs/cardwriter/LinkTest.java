package best.tgs.cardwriter;

import android.nfc.tech.NfcA;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Desktop checks for the command layer's behaviour on a link that misbehaves.
 *
 * The reason cards used to fail on the bench is not in the encoder — the
 * encoder has been byte-exact since the first card. It is in what happens when
 * one exchange out of thirty goes wrong, which on real hardware is both common
 * and impossible to schedule. So the link is simulated here instead: a card
 * that drops exchanges, truncates answers, swallows acknowledgements or
 * answers NAK, and the checks say what Tag215 must do about each.
 *
 * Every property below is a claim the app makes to the operator. A write that
 * is reported as done must have been confirmed by the card, and a card that
 * refuses must not be asked again as if it had merely stuttered.
 */
public final class LinkTest {

    private static int passed;

    public static void main(String[] args) throws Exception {
        cleanCardReadsAndWrites();
        transientDropsAreRidden();
        truncatedAnswersAreRidden();
        swallowedAckIsConfirmedByReadback();
        swallowedAckOverALostWriteFails();
        recoverableNakIsRetried();
        finalNakIsNotRetried();
        deadLinkGivesUpAndSaysSo();
        fastReadLadderFallsBackToPlainRead();
        openRetriesAWeakFirstContact();
        System.out.println("PASS: " + passed + " link behaviours hold.");
    }

    // ---------------------------------------------------------------- checks

    private static void cleanCardReadsAndWrites() throws Exception {
        Card card = new Card();
        Tag215 tag = Tag215.open(card);
        Tag215.Inspection inspection = tag.inspect();
        is("a factory card is safe to write", null, inspection.unsafe());
        is("the whole advertised area is read", Ndef.NDEF_CAPACITY, tag.readArea().length);
        tag.writePage(0x04, new byte[]{0x03, 0x00, (byte) 0xD1, 0x01});
        is("the page took the write", "03 00 D1 01", render(card.page(0x04)));
        is("a clean link reports no effort", "", tag.effort());
        ok("a clean link is not flagged", !tag.struggled());
        passed++;
    }

    private static void transientDropsAreRidden() throws Exception {
        // Every third exchange is lost, which is far worse than any real card,
        // and the presentation must still complete.
        Card card = new Card();
        card.dropEvery = 3;
        Tag215 tag = Tag215.open(card);
        tag.inspect();
        byte[] area = tag.readArea();
        is("the area survives a lossy link", Ndef.NDEF_CAPACITY, area.length);
        for (Ndef.Step step : Ndef.writePlan("https://tgs.best")) {
            tag.writePage(step.page, step.data);
        }
        is("the card ends up holding the message", "https://tgs.best",
                Ndef.decodeArea(tag.readArea()));
        ok("the receipt admits the link struggled", tag.struggled());
        ok("and says so in words", tag.effort().contains("retr"));
        passed++;
    }

    private static void truncatedAnswersAreRidden() throws Exception {
        // A short answer is a corrupted answer, not a card with something
        // different to say, so it is retried rather than believed.
        Card card = new Card();
        card.truncateEvery = 4;
        Tag215 tag = Tag215.open(card);
        tag.inspect();
        is("a truncating link still yields the area", Ndef.NDEF_CAPACITY, tag.readArea().length);
        passed++;
    }

    private static void swallowedAckIsConfirmedByReadback() throws Exception {
        Card card = new Card();
        card.swallowAcks = true;
        Tag215 tag = Tag215.open(card);
        tag.writePage(0x05, new byte[]{0x11, 0x22, 0x33, 0x44});
        is("a swallowed ACK is settled by reading the page back", "11 22 33 44",
                render(card.page(0x05)));
        passed++;
    }

    private static void swallowedAckOverALostWriteFails() throws Exception {
        // The dangerous case: the HAL says nothing and the page did not take.
        // Silence must never be read as success.
        Card card = new Card();
        card.swallowAcks = true;
        card.ignoreWrites = true;
        Tag215 tag = Tag215.open(card);
        threw("an unconfirmed write is a failure", tag, 0x06, new byte[]{1, 2, 3, 4});
        passed++;
    }

    private static void recoverableNakIsRetried() throws Exception {
        // NAK 1h is a parity or CRC error: the card did not understand, not
        // the card refusing. A steadier moment can clear it.
        Card card = new Card();
        card.nakWrites = 0x01;
        card.nakBudget = 2;
        Tag215 tag = Tag215.open(card);
        tag.writePage(0x07, new byte[]{(byte) 0xAA, 0x00, 0x00, 0x00});
        is("a CRC NAK is ridden out", "AA 00 00 00", render(card.page(0x07)));
        ok("and is counted as effort", tag.struggled());
        passed++;
    }

    private static void finalNakIsNotRetried() throws Exception {
        // NAK 0h is the card refusing the operation. Asking again is not
        // persistence, it is pretending not to have heard.
        Card card = new Card();
        card.nakWrites = 0x00;
        card.nakBudget = Integer.MAX_VALUE;
        Tag215 tag = Tag215.open(card);
        threw("a refusal stops the run", tag, 0x08, new byte[]{1, 2, 3, 4});
        is("and the card was asked exactly once", 1, card.writeCommands);
        passed++;
    }

    private static void deadLinkGivesUpAndSaysSo() throws Exception {
        Card card = new Card();
        Tag215 tag = Tag215.open(card);
        card.dead = true;
        try {
            tag.readArea();
            throw new AssertionError("A dead link must not produce an area.");
        } catch (IOException expected) {
            ok("a dead link is bounded, not infinite", true);
        }
        ok("giving up is recorded as effort", tag.struggled());
        passed++;
    }

    private static void fastReadLadderFallsBackToPlainRead() throws Exception {
        Card card = new Card();
        card.refuseFastRead = true;
        Tag215 tag = Tag215.open(card);
        byte[] area = tag.readArea();
        is("plain READ completes the area", Ndef.NDEF_CAPACITY, area.length);
        is("and the receipt names the path that answered", "READ 4p", tag.readPath());
        passed++;
    }

    private static void openRetriesAWeakFirstContact() throws Exception {
        Card card = new Card();
        card.failConnects = 2;
        Tag215 tag = Tag215.open(card);
        is("a weak first contact is retried, not refused", 3, card.connects);
        ok("and the retries show on the receipt", tag.struggled());

        Card hopeless = new Card();
        hopeless.failConnects = Integer.MAX_VALUE;
        try {
            Tag215.open(hopeless);
            throw new AssertionError("An absent card must not open.");
        } catch (IOException expected) {
            ok("an absent card still gives up", true);
        }
        passed++;
    }

    // ----------------------------------------------------------- simulation

    /**
     * An NTAG215 whose radio can be told to misbehave. Only the commands this
     * app issues are implemented; anything else is an error, which is itself
     * the check that the app issues nothing else.
     */
    private static final class Card extends NfcA {
        static final int PAGES = 135;

        final byte[] memory = new byte[PAGES * 4];
        final List<String> log = new ArrayList<String>();

        int connects;
        int failConnects;
        int exchanges;
        int writeCommands;

        int dropEvery;
        int truncateEvery;
        boolean swallowAcks;
        boolean ignoreWrites;
        boolean refuseFastRead;
        boolean dead;
        int nakWrites = -1;
        int nakBudget;

        Card() {
            // UID, BCC, and the factory capability container.
            byte[] head = {0x04, 0x11, 0x22, 0x00, 0x33, 0x44, 0x55, 0x66,
                    0x00, 0x00, 0x00, 0x00, (byte) 0xE1, 0x10, 0x3E, 0x00};
            head[3] = (byte) (0x88 ^ head[0] ^ head[1] ^ head[2]);
            head[8] = (byte) (head[4] ^ head[5] ^ head[6] ^ head[7]);
            System.arraycopy(head, 0, memory, 0, 16);
            // An empty NDEF TLV, as a factory card carries.
            memory[16] = 0x03;
            memory[17] = 0x00;
            memory[18] = (byte) 0xFE;
            // CFG0 / CFG1 at pages 0x83 and 0x84, with the factory AUTH0.
            memory[0x83 * 4 + 3] = (byte) 0xFF;
        }

        byte[] page(int page) {
            return Arrays.copyOfRange(memory, page * 4, page * 4 + 4);
        }

        @Override
        public void connect() throws IOException {
            connects++;
            if (failConnects > 0) {
                failConnects--;
                throw new IOException("Simulated weak coupling on connect.");
            }
        }

        @Override
        public byte[] transceive(byte[] command) throws IOException {
            exchanges++;
            if (dead) {
                throw new IOException("Simulated dead link.");
            }
            if (dropEvery > 0 && exchanges % dropEvery == 0) {
                throw new IOException("Simulated lost exchange.");
            }
            byte[] answer = answer(command);
            if (truncateEvery > 0 && exchanges % truncateEvery == 0 && answer.length > 1) {
                return Arrays.copyOf(answer, answer.length - 1);
            }
            return answer;
        }

        private byte[] answer(byte[] command) throws IOException {
            switch (command[0] & 0xFF) {
                case 0x60:
                    log.add("VERSION");
                    return Ndef.VERSION.clone();
                case 0x30: {
                    int page = command[1] & 0xFF;
                    log.add("READ " + page);
                    byte[] out = new byte[16];
                    for (int i = 0; i < 16; i++) {
                        out[i] = memory[((page * 4) + i) % memory.length];
                    }
                    return out;
                }
                case 0x3A: {
                    if (refuseFastRead) {
                        throw new IOException("This card does not answer FAST_READ.");
                    }
                    int from = command[1] & 0xFF;
                    int to = command[2] & 0xFF;
                    log.add("FAST_READ " + from + ".." + to);
                    return Arrays.copyOfRange(memory, from * 4, (to + 1) * 4);
                }
                case 0xA2: {
                    int page = command[1] & 0xFF;
                    writeCommands++;
                    log.add("WRITE " + page);
                    if (nakWrites >= 0 && nakBudget > 0) {
                        nakBudget--;
                        return new byte[]{(byte) nakWrites};
                    }
                    if (!ignoreWrites) {
                        System.arraycopy(command, 2, memory, page * 4, 4);
                    }
                    return swallowAcks ? new byte[0] : new byte[]{0x0A};
                }
                default:
                    throw new AssertionError("The app issued an unexpected command: "
                            + Ndef.hex(command));
            }
        }
    }

    // --------------------------------------------------------------- helpers

    private static void threw(String what, Tag215 tag, int page, byte[] data) {
        try {
            tag.writePage(page, data);
        } catch (IOException expected) {
            ok(what, true);
            return;
        }
        throw new AssertionError(what + ": the write was reported as done.");
    }

    private static String render(byte[] page) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < page.length; i++) {
            if (i > 0) {
                sb.append(' ');
            }
            sb.append(String.format("%02X", page[i] & 0xFF));
        }
        return sb.toString();
    }

    private static void is(String what, Object expected, Object actual) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(what + ": expected " + expected + ", got " + actual);
        }
    }

    private static void ok(String what, boolean value) {
        if (!value) {
            throw new AssertionError(what);
        }
    }

    private LinkTest() {
    }
}
