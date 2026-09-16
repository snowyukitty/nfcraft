package best.tgs.cardwriter;

import android.nfc.tech.NfcA;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Arrays;

/**
 * NTAG215 command layer over Android's raw NFC-A transceive.
 *
 * The safety checks are a port of Inspection.require_safe() in
 * nfcraft/adapters/base.py, and the page mapping matches the PC/SC adapter:
 * READ 0x00 gives pages 0..3 (UID, static locks, capability container) and
 * READ 0x82 gives pages 0x82..0x85 (dynamic locks, CFG0, CFG1).
 *
 * Nothing here can write outside pages 0x04..0x7F, and no command that changes
 * locks, configuration, password or the capability container is implemented at
 * all — not disabled, absent.
 *
 * <h2>Why every exchange is retried</h2>
 *
 * One card presentation is not one radio exchange. It is a GET_VERSION, two
 * head reads, a full 496-byte read, the write plan, a second full read and a
 * second inspection — of the order of thirty exchanges over a link a wooden
 * card holds weakly. A single CRC failure, a momentary detune from the
 * operator's hand, or the platform's own presence check landing between two of
 * our commands used to end the whole presentation, and the operator saw a card
 * that "failed" and had to be nudged until one pass happened to survive.
 *
 * Every exchange here is therefore attempted more than once: first plainly,
 * then after re-establishing the connection, which Android permits while the
 * tag is still in the field. Reads are naturally idempotent. A four-byte page
 * write is idempotent too — the same bytes at the same address land the same
 * way — so a write whose answer was lost is settled by reading the page back
 * rather than by assuming either outcome.
 */
final class Tag215 {

    /** Attempts per exchange. The first is plain; later ones reconnect first. */
    private static final int ATTEMPTS = 4;

    /** Pause before each retry: long enough for a hand to settle, short enough to feel instant. */
    private static final long[] BACKOFF_MS = {15, 45, 100};

    /** NTAG215 writes take well under a millisecond; this only bounds a dying link. */
    private static final int TIMEOUT_MS = 1000;

    private static final byte[] EMPTY = new byte[0];

    /** A refusal that is a property of the card, not a transport failure. */
    static final class Refusal extends Exception {
        final String headline;

        Refusal(String headline, String detail) {
            super(detail);
            this.headline = headline;
        }
    }

    /** A card that answered, and said no. Never retried: the answer will not change. */
    private static final class Rejected extends IOException {
        Rejected(String detail) {
            super(detail);
        }
    }

    /** The identity and protected configuration this app reads but never writes. */
    static final class Inspection {
        final byte[] version;
        final byte[] uid;
        final byte[] cc;
        final byte[] staticLocks;
        final byte[] dynamicLocks;
        final byte[] cfg0;
        final byte[] cfg1;

        Inspection(byte[] version, byte[] uid, byte[] cc, byte[] staticLocks,
                   byte[] dynamicLocks, byte[] cfg0, byte[] cfg1) {
            this.version = version;
            this.uid = uid;
            this.cc = cc;
            this.staticLocks = staticLocks;
            this.dynamicLocks = dynamicLocks;
            this.cfg0 = cfg0;
            this.cfg1 = cfg1;
        }

        /** Returns why this card must not be written, or null when it is safe. */
        String unsafe() {
            if (!Arrays.equals(version, Ndef.VERSION)) {
                return "Exact NTAG215 GET_VERSION response is required; no geometry guessing.";
            }
            if (!Arrays.equals(cc, Ndef.CC)) {
                return "Expected writable factory NTAG215 capability container E1103E00.";
            }
            if (any(staticLocks) || any(dynamicLocks)) {
                return "Lock bits are set. This app never clears or changes locks.";
            }
            if ((cfg0[3] & 0xFF) != 0xFF) {
                return "Password-protected or unusual tag; AUTH0 is not the factory value.";
            }
            if ((cfg0[0] & 0xC0) != 0 || cfg1[0] != 0) {
                return "Mirroring, counters, access limits or config locking are not supported.";
            }
            if (uid.length != 7 || (uid[0] & 0xFF) != 0x04) {
                return "Expected an NXP-style 7-byte UID. This is not an authenticity check.";
            }
            return null;
        }

        boolean sameAs(Inspection o) {
            return Arrays.equals(version, o.version)
                    && Arrays.equals(uid, o.uid)
                    && Arrays.equals(cc, o.cc)
                    && Arrays.equals(staticLocks, o.staticLocks)
                    && Arrays.equals(dynamicLocks, o.dynamicLocks)
                    && Arrays.equals(cfg0, o.cfg0)
                    && Arrays.equals(cfg1, o.cfg1);
        }

        String uidHex() {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < uid.length; i++) {
                if (i > 0) {
                    sb.append(':');
                }
                sb.append(String.format("%02X", uid[i] & 0xFF));
            }
            return sb.toString();
        }

        private static boolean any(byte[] b) {
            for (byte x : b) {
                if (x != 0) {
                    return true;
                }
            }
            return false;
        }
    }

    private final NfcA nfcA;

    /** Pages per FAST_READ. Halved when the link will not carry the answer. */
    private int fastReadPages;

    private int retries;
    private int reconnects;
    private String readPath = "";
    private Watcher watcher;
    private boolean warned;

    /** Told once, the moment the link starts needing help. */
    interface Watcher {
        void struggling();
    }

    /**
     * The operator is holding the card while this runs, and the one thing they
     * can do about a weak link is hold it more still. Telling them the moment
     * the link starts repeating itself is worth more than telling them after
     * the fact that it failed.
     */
    void watch(Watcher watcher) {
        this.watcher = watcher;
    }

    private void struggled(int count) {
        retries += count;
        if (warned || watcher == null) {
            return;
        }
        warned = true;
        watcher.struggling();
    }

    private Tag215(NfcA nfcA, int retriesSoFar) {
        this.nfcA = nfcA;
        this.retries = retriesSoFar;
        this.fastReadPages = maxFastReadPages();
        applyTimeout();
    }

    /**
     * Opens the link and hands back the card, giving a weak first contact more
     * than one chance.
     *
     * The first connect is where a card resting slightly off the antenna used
     * to be turned away outright, and it is the cheapest exchange of the whole
     * presentation to repeat — nothing has been read, nothing decided, nothing
     * written.
     */
    static Tag215 open(NfcA nfcA) throws IOException {
        IOException last = null;
        for (int attempt = 0; attempt < ATTEMPTS; attempt++) {
            if (attempt > 0) {
                pause(BACKOFF_MS[Math.min(attempt - 1, BACKOFF_MS.length - 1)]);
                try {
                    nfcA.close();
                } catch (IOException ignored) {
                    // A link that never opened does not need closing.
                } catch (RuntimeException ignored) {
                    // Nor does one this stack never considered open.
                }
            }
            try {
                nfcA.connect();
                return new Tag215(nfcA, attempt);
            } catch (IOException e) {
                last = e;
            } catch (RuntimeException e) {
                last = new IOException(describe(e));
            }
        }
        throw last == null ? new IOException("The card did not answer.") : last;
    }

    /** What the link cost, for the receipt. Empty when nothing had to be repeated. */
    String effort() {
        if (retries == 0 && reconnects == 0) {
            return "";
        }
        String note = retries + (retries == 1 ? " retry" : " retries");
        if (reconnects > 0) {
            note += ", " + reconnects + (reconnects == 1 ? " reconnect" : " reconnects");
        }
        return note;
    }

    /** Which read path answered, so a weak link can be told from a fussy one. */
    String readPath() {
        return readPath;
    }

    boolean struggled() {
        return retries > 0 || reconnects > 0;
    }

    /**
     * High pages are only touched after exact GET_VERSION evidence, so an
     * unknown chip is never probed at addresses that may mean something else.
     */
    Inspection inspect() throws IOException, Refusal {
        byte[] version = exchange(new byte[]{0x60}, 8);
        if (!Arrays.equals(version, Ndef.VERSION)) {
            throw new Refusal("Not an NTAG215",
                    "GET_VERSION does not match NTAG215, so no further pages were read.");
        }
        byte[] head = read(0x00);
        byte[] tail = read(0x82);

        byte[] uid = new byte[7];
        System.arraycopy(head, 0, uid, 0, 3);
        System.arraycopy(head, 4, uid, 3, 4);

        return new Inspection(
                version,
                uid,
                Arrays.copyOfRange(head, 12, 16),
                Arrays.copyOfRange(head, 10, 12),
                Arrays.copyOfRange(tail, 0, 3),
                Arrays.copyOfRange(tail, 4, 8),
                Arrays.copyOfRange(tail, 8, 12));
    }

    /**
     * The whole CC-advertised NDEF area: pages 0x04..0x7F, 496 bytes.
     *
     * A chunk size this link will not carry is not a reason to abandon
     * FAST_READ altogether. It is a reason to ask for less of the card at a
     * time, so the request walks down towards what this coupling actually
     * supports before plain four-page READs take over.
     */
    byte[] readArea() throws IOException {
        while (fastReadPages >= 4) {
            try {
                byte[] area = fastReadArea(fastReadPages);
                readPath = "FAST_READ " + fastReadPages + "p";
                return area;
            } catch (IOException e) {
                fastReadPages /= 2;
            }
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream(Ndef.NDEF_CAPACITY);
        for (int page = Ndef.FIRST_PAGE; page <= Ndef.LAST_NDEF_PAGE; page += 4) {
            out.write(read(page));
        }
        readPath = "READ 4p";
        return out.toByteArray();
    }

    private byte[] fastReadArea(int perCall) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream(Ndef.NDEF_CAPACITY);
        for (int page = Ndef.FIRST_PAGE; page <= Ndef.LAST_NDEF_PAGE; page += perCall) {
            int end = Math.min(Ndef.LAST_NDEF_PAGE, page + perCall - 1);
            out.write(exchange(new byte[]{0x3A, (byte) page, (byte) end}, (end - page + 1) * 4));
        }
        return out.toByteArray();
    }

    /**
     * Writes one page, and does not return until the card has either confirmed
     * it or refused it.
     *
     * A Type 2 WRITE answers with a four-bit ACK (0xA). Android stacks disagree
     * on how they surface that: some return {0x0A}, some throw, and some return
     * nothing at all for either an ACK or a NAK. The datasheet's NAK codes are
     * not all final either — 1h is a parity or CRC error and 5h is an EEPROM
     * write error, both of which a steadier moment can clear, while 0h and 4h
     * are the card refusing the operation and will not read differently on a
     * second attempt.
     */
    void writePage(int page, byte[] data) throws IOException {
        Ndef.assertSafePage(page, data);
        byte[] command = new byte[]{
                (byte) 0xA2, (byte) page, data[0], data[1], data[2], data[3]};
        IOException last = null;
        for (int attempt = 0; attempt < ATTEMPTS; attempt++) {
            if (attempt > 0) {
                struggled(1);
                pause(BACKOFF_MS[Math.min(attempt - 1, BACKOFF_MS.length - 1)]);
                if (attempt > 1 && !reconnect()) {
                    continue;
                }
                // The answer that went missing may have been an ACK. Writing
                // the same four bytes again would be harmless, but asking the
                // card first is cheaper, and it is the only way to tell the
                // two apart honestly.
                try {
                    if (pageHolds(page, data)) {
                        return;
                    }
                } catch (IOException e) {
                    last = e;
                    continue;
                }
            }
            try {
                byte[] response = nfcA.transceive(command);
                if (response != null && response.length > 0) {
                    int answer = response[0] & 0x0F;
                    if (answer == 0x0A) {
                        return;
                    }
                    if (answer != 0x01 && answer != 0x05) {
                        throw new Rejected("The card refused the write to page "
                                + hexPage(page) + " (NAK " + answer + ").");
                    }
                    last = new IOException("The card answered NAK " + answer + " for page "
                            + hexPage(page) + ".");
                    continue;
                }
                // Nothing came back, so this HAL is not surfacing the ACK — and
                // a swallowed NAK looks exactly the same. Read the page back
                // rather than letting the plan continue on an assumption.
                if (pageHolds(page, data)) {
                    return;
                }
                last = new IOException("Page " + hexPage(page) + " did not take the write"
                        + " (no acknowledgement, and the page read back differently).");
            } catch (Rejected e) {
                throw e;
            } catch (IOException e) {
                last = e;
            } catch (RuntimeException e) {
                last = new IOException(describe(e));
            }
        }
        throw last == null ? new IOException("Page " + hexPage(page) + " was not written.") : last;
    }

    /** One unretried look at a page, used to settle what a lost answer meant. */
    private boolean pageHolds(int page, byte[] data) throws IOException {
        byte[] echo = readOnce(page);
        for (int i = 0; i < 4; i++) {
            if (echo[i] != data[i]) {
                return false;
            }
        }
        return true;
    }

    /** READ returns four consecutive pages: 16 bytes. */
    private byte[] read(int page) throws IOException {
        return exchange(new byte[]{0x30, (byte) page}, 16);
    }

    private byte[] readOnce(int page) throws IOException {
        byte[] r;
        try {
            r = nfcA.transceive(new byte[]{0x30, (byte) page});
        } catch (RuntimeException e) {
            throw new IOException(describe(e));
        }
        if (r == null || r.length != 16) {
            throw new IOException("READ of page " + hexPage(page) + " returned "
                    + (r == null ? 0 : r.length) + " bytes, not 16.");
        }
        return r;
    }

    /**
     * One idempotent exchange, attempted until the link cooperates.
     *
     * A response of the wrong length is treated the same as no response: on
     * this link it means a truncated or corrupted answer, not a card with
     * something different to say. Only a card that answers correctly and says
     * something we refuse to accept stops the run, and that decision belongs to
     * the caller, not here.
     */
    private byte[] exchange(byte[] command, int expected) throws IOException {
        IOException last = null;
        for (int attempt = 0; attempt < ATTEMPTS; attempt++) {
            if (attempt > 0) {
                struggled(1);
                pause(BACKOFF_MS[Math.min(attempt - 1, BACKOFF_MS.length - 1)]);
                if (attempt > 1 && !reconnect()) {
                    continue;
                }
            }
            try {
                byte[] r = nfcA.transceive(command);
                if (r == null) {
                    r = EMPTY;
                }
                if (expected >= 0 && r.length != expected) {
                    last = new IOException("The card answered " + r.length + " bytes where "
                            + expected + " were expected.");
                    continue;
                }
                return r;
            } catch (IOException e) {
                last = e;
            } catch (RuntimeException e) {
                // A stack that has dropped the tag reports it as an
                // IllegalStateException rather than an IOException.
                last = new IOException(describe(e));
            }
        }
        throw last == null ? new IOException("The card did not answer.") : last;
    }

    /**
     * Re-establishes the link without the operator lifting the card. Android
     * allows a technology to be closed and connected again while the tag is
     * still in the field, and that is what recovers a presence check or a hand
     * movement that landed between two of our commands.
     */
    private boolean reconnect() {
        try {
            nfcA.close();
        } catch (IOException ignored) {
            // Closing a link that is already gone is not a failure.
        } catch (RuntimeException ignored) {
            // Nor is closing one this stack never considered open.
        }
        try {
            nfcA.connect();
        } catch (IOException e) {
            return false;
        } catch (RuntimeException e) {
            return false;
        }
        applyTimeout();
        reconnects++;
        return true;
    }

    private void applyTimeout() {
        try {
            nfcA.setTimeout(TIMEOUT_MS);
        } catch (RuntimeException ignored) {
            // Not every stack honours a timeout change; the default is workable.
        }
    }

    private static void pause(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /**
     * getMaxTransceiveLength() bounds what may be *sent*, and a FAST_READ
     * command is only three bytes — it says nothing about how large a response
     * this link can carry. Wooden cards couple weakly, so a long answer is the
     * first thing to CRC-fail. Start at 16 pages (64 bytes); readArea() walks
     * this down when the link will not carry it.
     */
    private int maxFastReadPages() {
        int limit = nfcA.getMaxTransceiveLength();
        if (limit <= 0) {
            limit = 64;
        }
        int pages = (limit - 2) / 4;
        if (pages < 1) {
            pages = 1;
        }
        return Math.min(pages, 16);
    }

    private static String hexPage(int page) {
        return String.format("0x%02X", page);
    }

    private static String describe(Throwable e) {
        String message = e.getMessage();
        return message == null || message.isEmpty() ? e.getClass().getSimpleName() : message;
    }
}
