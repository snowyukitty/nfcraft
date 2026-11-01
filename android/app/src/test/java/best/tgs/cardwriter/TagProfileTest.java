package best.tgs.cardwriter;

import org.junit.Test;
import java.util.Arrays;
import static org.junit.Assert.*;

public class TagProfileTest {
    @Test public void exactProfilesAndUnknownVariants() {
        int[] sizes = {15,17,19};
        TagProfile[] profiles = {TagProfile.NTAG213,TagProfile.NTAG215,TagProfile.NTAG216};
        for (int i = 0; i < sizes.length; i++) {
            byte[] v = {0,4,4,2,1,0,(byte)sizes[i],3};
            assertSame(profiles[i],TagProfile.identify(v));
            for (int j = 0; j < v.length; j++) {
                byte[] changed = v.clone(); changed[j] ^= 0x40;
                assertNull(TagProfile.identify(changed));
            }
        }
        assertNull(TagProfile.identify(new byte[0]));
    }

    @Test public void smallerCardKeepsLockControlTlvAndFitsExactly() {
        String url = "https://example.com/" + "x".repeat(119);
        byte[] target = Ndef.encodeArea(url,TagProfile.NTAG213);
        assertEquals(144,target.length);
        assertArrayEquals(new byte[]{1,3,(byte)0xA0,12,52},Arrays.copyOf(target,5));
        assertEquals(url,Ndef.decodeArea(target));
        try { Ndef.encodeArea(url + "x",TagProfile.NTAG213); fail("Oversize accepted"); }
        catch (IllegalArgumentException expected) { assertTrue(expected.getMessage().contains("NTAG213")); }
    }

    @Test public void legacyBytesAndPlansStayIdentical() {
        String url = "https://example.com/legacy";
        assertArrayEquals(Ndef.encodeArea(url),Ndef.encodeArea(url,TagProfile.NTAG215));
        assertArrayEquals(Ndef.encodeArea(url),Ndef.encodeArea(url,TagProfile.NTAG216));
        byte[] current = new byte[496];
        java.util.List<Ndef.Step> old = Ndef.writePlan(url,current);
        java.util.List<Ndef.Step> updated = Ndef.writePlan(url,current,TagProfile.NTAG215);
        assertEquals(old.size(),updated.size());
        for (int i = 0; i < old.size(); i++) {
            assertEquals(old.get(i).page,updated.get(i).page);
            assertArrayEquals(old.get(i).data,updated.get(i).data);
        }
    }

    @Test public void profileFencesDoNotReachLocksOrSpareUserMemory() {
        assertEquals(0x27,TagProfile.NTAG213.lastPage);
        assertEquals(0x7F,TagProfile.NTAG215.lastPage);
        assertEquals(0xDD,TagProfile.NTAG216.lastPage);
        for (TagProfile p : new TagProfile[]{TagProfile.NTAG213,TagProfile.NTAG215,TagProfile.NTAG216}) {
            p.assertSafePage(p.lastPage,new byte[4]);
            for (int page : new int[]{3,p.lastPage+1,p.dynamicLockPage,p.dynamicLockPage+4}) {
                try { p.assertSafePage(page,new byte[4]); fail("Protected page accepted"); }
                catch (IllegalArgumentException expected) { /* refused before transport */ }
            }
        }
    }

    @Test public void rewritingKeepsExistingLayoutAndHidesLengthBeforeBody() {
        for (TagProfile p : new TagProfile[]{TagProfile.NTAG213,TagProfile.NTAG215,TagProfile.NTAG216}) {
            String oldUrl = "https://example.com/old";
            String newUrl = "https://example.com/new";
            for (boolean factoryLayout : new boolean[]{false,true}) {
                byte[] original = new byte[p.capacity];
                byte[] old = factoryLayout ? Ndef.encodeArea(oldUrl,TagProfile.NTAG213) : Ndef.encodeArea(oldUrl);
                System.arraycopy(old,0,original,0,old.length);
                int lengthIndex = factoryLayout ? 6 : 1;
                java.util.List<Ndef.Step> plan = Ndef.writePlan(newUrl,original,p);
                byte[] current = original.clone();
                for (int i = 0; i < plan.size(); i++) {
                    Ndef.Step step = plan.get(i);
                    System.arraycopy(step.data,0,current,(step.page-4)*4,4);
                    if (i < plan.size()-1) assertEquals(0,current[lengthIndex]);
                }
                assertEquals(newUrl,Ndef.decodeArea(current));
                if (factoryLayout) assertArrayEquals(Arrays.copyOf(original,5),Arrays.copyOf(current,5));
            }
        }
    }
}
