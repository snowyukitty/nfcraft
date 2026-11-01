package best.tgs.cardwriter;

import android.nfc.tech.NfcA;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

/** Simulated command-level geometry, protection, capacity and interrupted-write checks. */
public final class ProfileTest {
    private static int checks;

    public static void main(String[] args) throws Exception {
        for (TagProfile p : new TagProfile[]{TagProfile.NTAG213, TagProfile.NTAG215, TagProfile.NTAG216}) {
            for (boolean fallback : new boolean[]{false, true}) roundTrip(p, fallback);
            protections(p);
            tornPlans(p);
        }
        Card unknown = new Card(TagProfile.NTAG213);
        unknown.version[4] = 2;
        try { Tag21x.open(unknown).inspect(); throw new AssertionError("Unknown version accepted"); }
        catch (Tag21x.Refusal expected) { check(unknown.reads == 0, "Unknown chip was probed"); }
        Card c = new Card(TagProfile.NTAG213);
        Tag21x tag = Tag21x.open(c);
        try { tag.writePage(4, new byte[4]); throw new AssertionError("Uninspected write"); }
        catch (IOException expected) { check(c.writes == 0, "Write preceded inspection"); }
        for (byte[] ack : new byte[][]{{0x1A}, {0x0A, 0x00}, {0x02}}) {
            c = new Card(TagProfile.NTAG213); c.ack = ack; tag = Tag21x.open(c); tag.inspect();
            try { tag.writePage(4, new byte[4]); throw new AssertionError("Malformed ACK accepted"); }
            catch (IOException expected) { check(c.writes == 1, "Malformed response retried"); }
        }
        System.out.println("PASS: " + checks + " multi-model safety assertions.");
    }

    private static void roundTrip(TagProfile p, boolean fallback) throws Exception {
        Card c = new Card(p); c.fallback = fallback;
        Tag21x tag = Tag21x.open(c);
        Tag21x.Inspection before = tag.inspect();
        check(before.profile == p && before.unsafe() == null, "Factory inspection");
        byte[] original = tag.readArea();
        check(original.length == p.capacity, "Exact advertised area");
        check(Ndef.isEmpty(original, p.capacity), "Factory blank incl. NTAG213 Lock Control TLV");
        String url = "https://example.com/new";
        byte[] target = Ndef.encodeArea(url, p);
        byte[] saved = c.memory.clone();
        for (Ndef.Step step : Ndef.writePlan(url, original, p)) tag.writePage(step.page, step.data);
        byte[] expected = original.clone();
        System.arraycopy(target, 0, expected, 0, target.length);
        check(Arrays.equals(expected, tag.readArea()), "Full target and preserved tail");
        check(url.equals(Ndef.decodeArea(tag.readArea())), "URL round trip");
        check(before.sameAs(tag.inspect()), "Identity/configuration unchanged");
        check(Arrays.equals(Arrays.copyOf(saved, 16), Arrays.copyOf(c.memory, 16)), "Head preserved");
        check(Arrays.equals(Arrays.copyOfRange(saved, (p.lastPage + 1) * 4, saved.length),
                Arrays.copyOfRange(c.memory, (p.lastPage + 1) * 4, c.memory.length)), "All outside pages preserved");
        for (int page : new int[]{0, 2, 3, p.lastPage + 1, p.dynamicLockPage, p.dynamicLockPage + 1,
                p.dynamicLockPage + 3, p.dynamicLockPage + 4}) {
            int writes = c.writes;
            try { tag.writePage(page, new byte[4]); throw new AssertionError("Fence failed"); }
            catch (IllegalArgumentException expectedRefusal) { check(writes == c.writes, "Fence before I/O"); }
        }
        String longest = "https://example.com/" + "x".repeat(p == TagProfile.NTAG213 ? 119 : 180);
        check(Ndef.validate(longest) == null, "Valid boundary URL");
        check(Ndef.encodeArea(longest, p).length <= p.capacity, "Boundary fits");
        if (p == TagProfile.NTAG213) {
            check(longest.length() == 139, "NTAG213 capacity includes Lock Control TLV");
            try { Ndef.writePlan(longest + "x", original, p); throw new AssertionError("Oversize plan"); }
            catch (IllegalArgumentException expectedRefusal) { check(true, "Reject before mutation"); }
        }
    }

    private static void protections(TagProfile p) throws Exception {
        for (int address : new int[]{12, 10, p.dynamicLockPage * 4,
                (p.dynamicLockPage + 1) * 4 + 3, (p.dynamicLockPage + 1) * 4,
                (p.dynamicLockPage + 2) * 4, 3, 8}) {
            Card c = new Card(p); c.memory[address] ^= address == (p.dynamicLockPage + 1) * 4 ? 0x40 : 1;
            Tag21x tag = Tag21x.open(c);
            check(tag.inspect().unsafe() != null, "Refuse CC/locks/protection/BCC mismatch");
            try { tag.writePage(4, new byte[4]); throw new AssertionError("Unsafe write"); }
            catch (IOException expected) { check(c.writes == 0, "Unsafe tag never written"); }
        }
    }

    private static void tornPlans(TagProfile p) {
        String url = "https://example.com/resume";
        byte[] target = Ndef.encodeArea(url, p);
        byte[] original = new Card(p).area();
        List<Ndef.Step> full = Ndef.writePlan(url, original, p);
        for (int cut = 0; cut <= full.size(); cut++) {
            byte[] partial = original.clone();
            for (int i = 0; i < cut; i++) apply(partial, full.get(i));
            if (cut > 0 && cut < full.size()) check(Ndef.isOurStagedWrite(partial, target), "Staged recovery");
            for (Ndef.Step step : Ndef.writePlan(url, partial, p)) {
                p.assertSafePage(step.page, step.data);
                apply(partial, step);
            }
            byte[] expected = original.clone(); System.arraycopy(target, 0, expected, 0, target.length);
            check(Arrays.equals(expected, partial), "Every torn prefix converges");
        }
        byte[] hidden = original.clone(); hidden[20] = 42;
        check(Ndef.hidesDataUnderEmptyTlv(hidden, target.length), "Hidden bytes detected");
    }

    private static void apply(byte[] area, Ndef.Step step) {
        System.arraycopy(step.data, 0, area, (step.page - 4) * 4, 4);
    }

    private static void check(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
        checks++;
    }

    private static final class Card extends NfcA {
        final TagProfile p;
        final byte[] memory;
        final byte[] version;
        int reads, writes;
        boolean fallback;
        byte[] ack = {0x0A};
        Card(TagProfile p) {
            this.p = p;
            memory = new byte[(p.dynamicLockPage + 5) * 4];
            version = new byte[]{0,4,4,2,1,0,(byte)(p == TagProfile.NTAG213 ? 15 : p == TagProfile.NTAG215 ? 17 : 19),3};
            byte[] head = {4,17,34,0,51,68,85,102,0,0,0,0,(byte)0xE1,16,(byte)(p.capacity / 8),0};
            head[3] = (byte)(0x88 ^ head[0] ^ head[1] ^ head[2]);
            head[8] = (byte)(head[4] ^ head[5] ^ head[6] ^ head[7]);
            System.arraycopy(head,0,memory,0,16);
            byte[] blank = p == TagProfile.NTAG213 ? new byte[]{1,3,(byte)0xA0,12,52,3,0,(byte)0xFE}
                    : new byte[]{3,0,(byte)0xFE,0};
            System.arraycopy(blank,0,memory,16,blank.length);
            memory[(p.dynamicLockPage + 1) * 4 + 3] = (byte)0xFF;
            memory[(p.lastPage + 1) * 4 - 1] = 77; // Tail marker within advertised memory.
        }
        byte[] area() { return Arrays.copyOfRange(memory,16,16+p.capacity); }
        @Override public byte[] transceive(byte[] command) throws IOException {
            int op = command[0] & 255;
            if (op == 0x60) return version.clone();
            int page = command[1] & 255;
            if (op == 0x30) {
                reads++;
                if (page >= 4 && page < p.dynamicLockPage) check(page + 3 <= p.lastPage, "READ crossed NDEF boundary");
                return Arrays.copyOfRange(memory,page*4,(page+4)*4);
            }
            if (op == 0x3A) {
                if (fallback) return new byte[]{0};
                int end = command[2] & 255;
                check(page >= 4 && end <= p.lastPage, "FAST_READ crossed boundary");
                return Arrays.copyOfRange(memory,page*4,(end+1)*4);
            }
            if (op == 0xA2) {
                check(page >= 4 && page <= p.lastPage, "WRITE crossed boundary");
                writes++;
                if (Arrays.equals(ack,new byte[]{0x0A})) System.arraycopy(command,2,memory,page*4,4);
                return ack;
            }
            throw new AssertionError("Unexpected command");
        }
    }
}
