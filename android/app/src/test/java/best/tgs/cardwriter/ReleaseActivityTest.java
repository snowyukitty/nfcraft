package best.tgs.cardwriter;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Looper;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.EditText;
import android.widget.TextView;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

/** Exercises exported input and UI lifecycle without a physical NFC adapter. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 36})
public class ReleaseActivityTest {
    private SharedPreferences prefs;

    @Before public void fixture() {
        prefs = RuntimeEnvironment.getApplication().getSharedPreferences("card-writer", Context.MODE_PRIVATE);
        prefs.edit().clear().putString("url", "https://example.com/original").commit();
    }

    private Intent share(String value) {
        return new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, value);
    }

    private void click(int button) {
        ShadowAlertDialog.getLatestAlertDialog().getButton(button).performClick();
        shadowOf(Looper.getMainLooper()).idle();
    }

    private ScanGate gate(MainActivity activity) throws Exception {
        java.lang.reflect.Field field = MainActivity.class.getDeclaredField("scanGate");
        field.setAccessible(true);
        return (ScanGate) field.get(activity);
    }

    @Test public void shareRequiresConsentAndEntersReadOnlyMode() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class,
                share(" https://example.com/new?x=1 ")).setup()) {
            MainActivity activity = controller.get();
            assertEquals("https://example.com/original", prefs.getString("url", ""));
            assertFalse(gate(activity).beginScan());
            click(AlertDialog.BUTTON_NEGATIVE);
            assertEquals("https://example.com/original", prefs.getString("url", ""));
            assertTrue(gate(activity).beginScan());
            gate(activity).finishScan();
            controller.newIntent(share("https://example.com/new?x=1"));
            click(AlertDialog.BUTTON_POSITIVE);
            assertEquals("https://example.com/new?x=1", prefs.getString("url", ""));
            assertTrue(prefs.getBoolean("inspect_only", false));
            assertTrue(prefs.getString("recent_urls_v1", "").contains("new?x=1"));
            assertEquals("ON", ((TextView) activity.findViewById(R.id.inspectOnlyState)).getText().toString());
        }
    }

    @Test public void rejectsUntrustedSharesWithoutChangingData() {
        String[] bad = {"http://example.com", "https://a.example https://b.example",
                "Look: https://example.com", "https://user:secret@example.com", "https://example.com/#secret",
                "javascript:alert(1)", "https://example.com/" + new String(new char[2050]).replace('\0', 'x')};
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            for (String value : bad) {
                controller.newIntent(share(value));
                assertTrue(ShadowAlertDialog.getLatestAlertDialog().isShowing());
                click(AlertDialog.BUTTON_POSITIVE);
                assertEquals("https://example.com/original", prefs.getString("url", ""));
            }
        }
    }

    @Test public void supportOpensAnUnsentComposerWithoutPrivateCardData() {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            controller.get().findViewById(R.id.help).performClick();
            click(AlertDialog.BUTTON_NEUTRAL);
            Intent mail = shadowOf(controller.get()).getNextStartedActivity();
            assertNotNull(mail);
            assertEquals(Intent.ACTION_SENDTO, mail.getAction());
            assertEquals("mailto:dokoii@proton.me", mail.getDataString());
            assertEquals("nfcraft feedback", mail.getStringExtra(Intent.EXTRA_SUBJECT));
            assertFalse(mail.hasExtra(Intent.EXTRA_TEXT));
            assertFalse(mail.hasExtra(Intent.EXTRA_STREAM));
        }
    }

    @Test public void dialogsPauseScansAndAnActiveScanDefersDialogs() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity activity = controller.get();
            ScanGate gate = gate(activity);
            for (int id : new int[]{R.id.help, R.id.privacy, R.id.recentUrls}) {
                activity.findViewById(id).performClick();
                assertFalse(gate.beginScan());
                activity.onTagDiscovered(null); // must return before accessing even a tag object
                ShadowAlertDialog.getLatestAlertDialog().dismiss();
                shadowOf(Looper.getMainLooper()).idle();
                assertTrue(gate.beginScan());
                activity.findViewById(R.id.help).performClick();
                assertFalse(ShadowAlertDialog.getLatestAlertDialog().isShowing());
                gate.finishScan();
            }
            controller.pause();
            assertFalse(gate.beginScan());
        }
    }

    @Test public void overwriteNeedsConfirmationAndNeverSurvivesBackgrounding() {
        prefs.edit().putBoolean("allow_unknown", true).commit();
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity activity = controller.get();
            TextView state = activity.findViewById(R.id.allowUnknownState);
            assertEquals("OFF", state.getText().toString());
            activity.findViewById(R.id.allowUnknown).performClick();
            click(AlertDialog.BUTTON_NEGATIVE);
            assertEquals("OFF", state.getText().toString());
            activity.findViewById(R.id.allowUnknown).performClick();
            click(AlertDialog.BUTTON_POSITIVE);
            assertEquals("ON", state.getText().toString());
            AccessibilityNodeInfo info = activity.findViewById(R.id.allowUnknown).createAccessibilityNodeInfo();
            assertTrue(info.isCheckable());
            assertTrue(info.isChecked());
            controller.pause().resume();
            assertEquals("OFF", state.getText().toString());
            assertFalse(prefs.contains("allow_unknown"));
        }
    }

    @Test public void recreationKeepsUnacceptedShareUnaccepted() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class,
                share("https://example.com/shared")).setup()) {
            controller.recreate();
            assertFalse(gate(controller.get()).beginScan());
            assertEquals("https://example.com/original", prefs.getString("url", ""));
            click(AlertDialog.BUTTON_POSITIVE);
            assertEquals("https://example.com/shared", prefs.getString("url", ""));
            controller.recreate();
            assertTrue(gate(controller.get()).beginScan());
            gate(controller.get()).finishScan();
        }
    }

    @Test
    @Config(sdk = 36, qualifiers = "w360dp-h800dp-xxhdpi")
    @GraphicsMode(GraphicsMode.Mode.NATIVE)
    public void rendersImportAndGuideForReview() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class,
                share("https://example.com/portfolio")).setup().visible()) {
            RecentUrlsActivityTest.capture(ShadowAlertDialog.getLatestAlertDialog().getWindow().getDecorView(),
                    "share-confirmation");
            click(AlertDialog.BUTTON_NEGATIVE);
            controller.get().findViewById(R.id.help).performClick();
            RecentUrlsActivityTest.capture(ShadowAlertDialog.getLatestAlertDialog().getWindow().getDecorView(),
                    "quick-guide");
        }
    }

    @Test
    @Config(sdk = 36, qualifiers = "w320dp-h640dp-mdpi")
    @GraphicsMode(GraphicsMode.Mode.NATIVE)
    public void largeTextKeepsActionsReachableByScrolling() throws Exception {
        RuntimeEnvironment.setFontScale(1.6f);
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup().visible()) {
            MainActivity activity = controller.get();
            View root = activity.getWindow().getDecorView();
            root.measure(View.MeasureSpec.makeMeasureSpec(320, View.MeasureSpec.EXACTLY),
                    View.MeasureSpec.makeMeasureSpec(640, View.MeasureSpec.EXACTLY));
            root.layout(0, 0, 320, 640);
            android.widget.ScrollView scroll = (android.widget.ScrollView)
                    ((android.view.ViewGroup) activity.findViewById(android.R.id.content)).getChildAt(0);
            assertTrue(scroll.getChildAt(0).getHeight() > scroll.getHeight());
            View privacy = activity.findViewById(R.id.privacy);
            scroll.scrollTo(0, scroll.getChildAt(0).getHeight());
            assertTrue(privacy.getBottom() - scroll.getScrollY() <= scroll.getHeight());
            assertTrue(privacy.getHeight() >= 48);
            assertEquals(android.widget.LinearLayout.VERTICAL,
                    ((android.widget.LinearLayout) activity.findViewById(R.id.modeControls)).getOrientation());
            TextView overwrite = activity.findViewById(R.id.allowUnknownTitle);
            assertTrue(overwrite.getLayout().getLineEnd(overwrite.getLineCount() - 1)
                    >= overwrite.getText().length());
            assertFalse(((TextView) activity.findViewById(R.id.help)).getLayout().getEllipsisCount(0) > 0);
            android.graphics.Bitmap bitmap = android.graphics.Bitmap.createBitmap(320, 640,
                    android.graphics.Bitmap.Config.ARGB_8888);
            root.draw(new android.graphics.Canvas(bitmap));
            java.io.File directory = new java.io.File("build/reports/visual");
            directory.mkdirs();
            try (java.io.FileOutputStream out = new java.io.FileOutputStream(new java.io.File(directory,
                    "large-text-scrolled.png"))) {
                bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
            }
        } finally {
            RuntimeEnvironment.setFontScale(1.0f);
        }
    }
}
