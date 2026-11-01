package best.tgs.cardwriter;

import java.util.Arrays;

/** Exact NXP NTAG21x profiles; never infer geometry from a UID or CC alone. */
final class TagProfile {
    static final TagProfile NTAG213 = new TagProfile("NTAG213", 0x0F, 0x12, 0x28);
    static final TagProfile NTAG215 = new TagProfile("NTAG215", 0x11, 0x3E, 0x82);
    static final TagProfile NTAG216 = new TagProfile("NTAG216", 0x13, 0x6D, 0xE2);

    final String name;
    final int capacity;
    final int lastPage;
    final int dynamicLockPage;
    private final byte[] version;
    private final byte[] cc;

    private TagProfile(String name, int storage, int ccSize, int dynamicLockPage) {
        this.name = name;
        this.capacity = ccSize * 8;
        this.lastPage = Ndef.FIRST_PAGE + capacity / 4 - 1;
        this.dynamicLockPage = dynamicLockPage;
        version = new byte[]{0, 4, 4, 2, 1, 0, (byte) storage, 3};
        cc = new byte[]{(byte) 0xE1, 0x10, (byte) ccSize, 0};
    }

    static TagProfile identify(byte[] version) {
        for (TagProfile profile : new TagProfile[]{NTAG213, NTAG215, NTAG216}) {
            if (Arrays.equals(profile.version, version)) return profile;
        }
        return null;
    }

    boolean matchesCc(byte[] value) {
        return Arrays.equals(cc, value);
    }

    void requireFits(byte[] area) {
        if (area.length > capacity) {
            throw new IllegalArgumentException("Link needs " + area.length + " NDEF bytes; "
                    + name + " has " + capacity + ". Use a shorter HTTPS link.");
        }
    }

    void assertSafePage(int page, byte[] data) {
        if (page < Ndef.FIRST_PAGE || page > lastPage || data == null || data.length != 4) {
            throw new IllegalArgumentException("Writes require four-byte " + name
                    + " NDEF pages 04.." + Integer.toHexString(lastPage).toUpperCase(java.util.Locale.ROOT) + ".");
        }
    }
}
