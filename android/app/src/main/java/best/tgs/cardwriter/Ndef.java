package best.tgs.cardwriter;

import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/**
 * Deliberately narrow NFC Forum Type 2, single HTTPS URI encoder.
 *
 * This is a port of nfcraft/ndef.py. The rules are intentionally identical so a
 * card written by this phone and a card written by the PC/SC path carry
 * byte-for-byte the same area, and so a card written here still decodes under
 * the Python tooling. Keep the two in step if either changes.
 */
final class Ndef {

    static final byte[] CC = {(byte) 0xE1, 0x10, 0x3E, 0x00};
    static final byte[] VERSION = {0x00, 0x04, 0x04, 0x02, 0x01, 0x00, 0x11, 0x03};

    static final int NDEF_CAPACITY = 496;
    static final int FIRST_PAGE = 0x04;
    static final int LAST_NDEF_PAGE = 0x7F;
    static final int MAX_URL_BYTES = 200;
    // NXP factory NTAG213 Lock Control TLV. Preserve it in rewritten records.
    private static final byte[] LOCK_TLV = {0x01, 0x03, (byte) 0xA0, 0x0C, 0x34};

    private Ndef() {
    }

    /** One four-byte page write. */
    static final class Step {
        final int page;
        final byte[] data;

        Step(int page, byte[] data) {
            this.page = page;
            this.data = data;
        }
    }

    /**
     * Returns a human-readable problem, or null when the URL is acceptable.
     * Mirrors validate_https() without the production-domain checks, which
     * belong to the per-card provisioning flow rather than a rewrite tool.
     */
    static String validate(String url) {
        if (url == null || url.isEmpty()) {
            return "Enter an HTTPS destination.";
        }
        for (int i = 0; i < url.length(); i++) {
            char c = url.charAt(i);
            if (c > 127 || c < 33 || c == 127) {
                return "Use an ASCII HTTPS URL; encode Unicode with IDNA or percent escapes.";
            }
        }
        if (url.length() > MAX_URL_BYTES) {
            return "URL is too long (maximum " + MAX_URL_BYTES + " bytes).";
        }
        if (url.indexOf('\\') >= 0) {
            return "URL contains a backslash.";
        }
        if (!url.startsWith("https://")) {
            return "An HTTPS URL is required.";
        }
        if (url.indexOf('#') >= 0) {
            return "An HTTPS URL without a fragment is required.";
        }
        String rest = url.substring(8);
        int cut = rest.length();
        for (int i = 0; i < rest.length(); i++) {
            char c = rest.charAt(i);
            if (c == '/' || c == '?') {
                cut = i;
                break;
            }
        }
        String authority = rest.substring(0, cut);
        if (authority.indexOf('@') >= 0) {
            return "An HTTPS URL without credentials is required.";
        }
        String host = authority;
        int colon = authority.lastIndexOf(':');
        if (colon >= 0) {
            host = authority.substring(0, colon);
            String port = authority.substring(colon + 1);
            if (port.isEmpty()) {
                return "Malformed port.";
            }
            for (int i = 0; i < port.length(); i++) {
                if (port.charAt(i) < '0' || port.charAt(i) > '9') {
                    return "Malformed port.";
                }
            }
        }
        host = host.toLowerCase(Locale.ROOT);
        if (host.isEmpty() || host.length() > 253) {
            return "Use a valid ASCII DNS hostname.";
        }
        for (String label : host.split("\\.", -1)) {
            if (!isDnsLabel(label)) {
                return "Use a valid ASCII DNS hostname.";
            }
        }
        return null;
    }

    private static boolean isDnsLabel(String label) {
        int n = label.length();
        if (n < 1 || n > 63) {
            return false;
        }
        for (int i = 0; i < n; i++) {
            char c = label.charAt(i);
            boolean alnum = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9');
            if (!alnum && !(c == '-' && i > 0 && i < n - 1)) {
                return false;
            }
        }
        return true;
    }

    /** A single short URI record using NFC URI prefix code 0x04 (https://). */
    static byte[] uriRecord(String url) {
        byte[] rest = ascii(url.substring(8));
        byte[] record = new byte[4 + 1 + rest.length];
        record[0] = (byte) 0xD1;
        record[1] = 0x01;
        record[2] = (byte) (1 + rest.length);
        record[3] = 0x55;
        record[4] = 0x04;
        System.arraycopy(rest, 0, record, 5, rest.length);
        return record;
    }

    /** The exact bytes the NDEF area should hold, padded to whole pages. */
    static byte[] encodeArea(String url) {
        byte[] record = uriRecord(url);
        if (record.length >= 255) {
            throw new IllegalArgumentException("Only short NDEF TLVs are supported.");
        }
        int areaLength = 1 + 1 + record.length + 1;
        int padded = areaLength + ((4 - (areaLength % 4)) % 4);
        if (padded > NDEF_CAPACITY) {
            throw new IllegalArgumentException("Payload exceeds the NTAG215 CC-advertised area.");
        }
        byte[] area = new byte[padded];
        area[0] = 0x03;
        area[1] = (byte) record.length;
        System.arraycopy(record, 0, area, 2, record.length);
        area[2 + record.length] = (byte) 0xFE;
        return area;
    }

    static byte[] encodeArea(String url, TagProfile profile) {
        return encodeArea(url, profile, profile == TagProfile.NTAG213);
    }

    static byte[] encodeArea(String url, TagProfile profile, byte[] current) {
        return encodeArea(url, profile, messageOffset(current) == 5);
    }

    private static byte[] encodeArea(String url, TagProfile profile, boolean keepLockTlv) {
        byte[] area = encodeArea(url);
        if (keepLockTlv) {
            byte[] record = uriRecord(url);
            int size = LOCK_TLV.length + record.length + 3;
            area = new byte[(size + 3) / 4 * 4];
            System.arraycopy(LOCK_TLV, 0, area, 0, LOCK_TLV.length);
            area[5] = 0x03;
            area[6] = (byte) record.length;
            System.arraycopy(record, 0, area, 7, record.length);
            area[7 + record.length] = (byte) 0xFE;
        }
        profile.requireFits(area);
        return area;
    }

    private static int messageOffset(byte[] area) {
        if (area != null && area.length >= 8
                && Arrays.equals(Arrays.copyOf(area, LOCK_TLV.length), LOCK_TLV)) return 5;
        return 0;
    }

    /**
     * Strictly decode our own canonical record, or null. Arbitrary tag data is
     * deliberately not interpreted: anything this does not recognise is treated
     * as unfamiliar content, not as something safe to replace.
     */
    static String decodeArea(byte[] area) {
        if (messageOffset(area) == 5) area = Arrays.copyOfRange(area, 5, area.length);
        if (area == null || area.length < 8 || area[0] != 0x03 || area[1] == 0) {
            return null;
        }
        int n = area[1] & 0xFF;
        if (area.length < n + 3 || n < 5) {
            return null;
        }
        byte[] r = new byte[n];
        System.arraycopy(area, 2, r, 0, n);
        if (r[0] != (byte) 0xD1 || r[1] != 0x01 || r[3] != 0x55 || r[4] != 0x04) {
            return null;
        }
        if ((r[2] & 0xFF) != r.length - 4) {
            return null;
        }
        if (area[n + 2] != (byte) 0xFE) {
            return null;
        }
        String url;
        try {
            url = "https://" + new String(r, 5, n - 5, "US-ASCII");
        } catch (UnsupportedEncodingException e) {
            return null;
        }
        return validate(url) == null ? url : null;
    }

    /** Factory-initialised empty TLV, or an all-zero unpopulated user area. */
    static boolean isEmpty(byte[] area) {
        return isEmpty(area, NDEF_CAPACITY);
    }

    static boolean isEmpty(byte[] area, int capacity) {
        if (area.length != capacity) {
            return false;
        }
        int offset = messageOffset(area);
        if (area[offset] == 0x03 && area[offset + 1] == 0x00 && area[offset + 2] == (byte) 0xFE) {
            return true;
        }
        for (byte b : area) {
            if (b != 0) {
                return false;
            }
        }
        return true;
    }

    /** True when an empty TLV is hiding data inside the region about to be written. */
    static boolean hidesDataUnderEmptyTlv(byte[] area, int plannedLength) {
        if (messageOffset(area) == 5) {
            return hidesDataUnderEmptyTlv(Arrays.copyOfRange(area, 5, area.length), plannedLength - 5);
        }
        if (area.length < 3 || area[0] != 0x03 || area[1] != 0x00 || area[2] != (byte) 0xFE) {
            return false;
        }
        int end = Math.min(plannedLength, area.length);
        for (int i = 3; i < end; i++) {
            if (area[i] != 0) {
                return true;
            }
        }
        return false;
    }

    /**
     * True when the card holds the staged first page this tool writes before
     * the body — `03 00` followed by the target's own record header.
     *
     * writePlan deliberately commits a zero-length TLV first, so a card that
     * leaves the field mid-plan is left advertising `03 00 D1 01`. That is
     * neither a decodable record nor the factory empty TLV, so without this
     * classifier the retry is refused as unfamiliar content — the one card the
     * operator is most certain about. The Python engine covers the same case
     * through recovery_matches(); this is the single-destination equivalent.
     */
    static boolean isOurStagedWrite(byte[] area, byte[] target) {
        if (messageOffset(area) == 5 && messageOffset(target) == 5) {
            // Length and D1 share page 05; byte 01 starts the next body page.
            return area[5] == 0x03 && area[6] == 0 && area[7] == target[7];
        }
        return area.length >= 4 && target.length >= 4
                && area[0] == 0x03 && area[1] == 0x00
                && area[2] == target[2] && area[3] == target[3];
    }

    /**
     * Expose an empty message first; make the message length visible only after
     * the body is in place. This reduces partially advertised records. It does
     * NOT make EEPROM writes atomic.
     */
    static List<Step> writePlan(String url) {
        byte[] target = encodeArea(url);
        List<Step> steps = new ArrayList<Step>();
        steps.add(new Step(FIRST_PAGE, new byte[]{target[0], 0x00, target[2], target[3]}));
        for (int i = 4; i < target.length; i += 4) {
            byte[] page = new byte[4];
            System.arraycopy(target, i, page, 0, 4);
            steps.add(new Step(FIRST_PAGE + i / 4, page));
        }
        steps.add(new Step(FIRST_PAGE, new byte[]{target[0], target[1], target[2], target[3]}));
        return steps;
    }

    /**
     * The same plan with the pages the card already holds left out.
     *
     * A card that tore mid-plan, or one being rewritten to a destination it
     * partly shares with the old one, does not need every page sent again. The
     * bytes that end up on the card are identical either way — this only
     * decides which of them travel — and on a weak link the pages not sent are
     * the ones that cannot fail.
     *
     * The commit step is always kept: it is what makes the message readable,
     * and it must be the last thing written whatever else was skipped. The
     * staged step is dropped only when the card already advertises a
     * zero-length message, so the rule it exists to enforce — no length visible
     * while the body is in flight — holds in every case.
     */
    static List<Step> writePlan(String url, byte[] current) {
        return writePlan(url, current, NDEF_CAPACITY);
    }

    static List<Step> writePlan(String url, byte[] current, TagProfile profile) {
        if (current == null || current.length != profile.capacity) {
            throw new IllegalArgumentException("A complete original NDEF area is required.");
        }
        byte[] target = encodeArea(url, profile, current);
        int commitOffset = (messageOffset(target) + 1) / 4 * 4;
        byte[] staged = Arrays.copyOfRange(target, commitOffset, commitOffset + 4);
        staged[messageOffset(target) + 1 - commitOffset] = 0;
        List<Step> steps = new ArrayList<Step>();
        Step stage = new Step(FIRST_PAGE + commitOffset / 4, staged);
        if (!alreadyHolds(current, stage)) steps.add(stage);
        for (int i = 0; i < target.length; i += 4) {
            if (i == commitOffset) continue;
            Step step = new Step(FIRST_PAGE + i / 4, Arrays.copyOfRange(target, i, i + 4));
            if (!alreadyHolds(current, step)) steps.add(step);
        }
        steps.add(new Step(FIRST_PAGE + commitOffset / 4,
                Arrays.copyOfRange(target, commitOffset, commitOffset + 4)));
        return steps;
    }

    private static List<Step> writePlan(String url, byte[] current, int capacity) {
        List<Step> full = writePlan(url);
        if (current == null || current.length != capacity) {
            return full;
        }
        List<Step> pruned = new ArrayList<Step>();
        for (int i = 0; i < full.size(); i++) {
            Step step = full.get(i);
            if (i < full.size() - 1 && alreadyHolds(current, step)) {
                continue;
            }
            pruned.add(step);
        }
        return pruned;
    }

    private static boolean alreadyHolds(byte[] area, Step step) {
        int offset = (step.page - FIRST_PAGE) * 4;
        if (offset < 0 || offset + 4 > area.length) {
            return false;
        }
        for (int i = 0; i < 4; i++) {
            if (area[offset + i] != step.data[i]) {
                return false;
            }
        }
        return true;
    }

    static void assertSafePage(int page, byte[] data) {
        if (page < FIRST_PAGE || page > LAST_NDEF_PAGE || data.length != 4) {
            throw new IllegalArgumentException(
                    "Writes are restricted to four-byte NDEF pages 0x04..0x7F.");
        }
    }

    static byte[] ascii(String s) {
        byte[] out = new byte[s.length()];
        for (int i = 0; i < s.length(); i++) {
            out[i] = (byte) s.charAt(i);
        }
        return out;
    }

    static String hex(byte[] b, int from, int to) {
        StringBuilder sb = new StringBuilder();
        for (int i = from; i < to; i++) {
            sb.append(String.format("%02X", b[i] & 0xFF));
        }
        return sb.toString();
    }

    static String hex(byte[] b) {
        return hex(b, 0, b.length);
    }
}
