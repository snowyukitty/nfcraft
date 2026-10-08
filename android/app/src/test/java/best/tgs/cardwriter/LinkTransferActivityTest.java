package best.tgs.cardwriter;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;
import android.widget.EditText;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 36})
public class LinkTransferActivityTest {
    private SharedPreferences prefs;
    @Before public void fixture() {
        prefs = RuntimeEnvironment.getApplication().getSharedPreferences("card-writer", Context.MODE_PRIVATE);
        prefs.edit().clear().putString("url", "https://example.com/current")
                .putString("recent_urls_v1", "[\"https://example.com/old\"]").commit();
    }
    private void click(int button) {
        ShadowAlertDialog.getLatestAlertDialog().getButton(button).performClick();
        shadowOf(Looper.getMainLooper()).idle();
    }
    private EditText openImport(MainActivity activity) {
        activity.findViewById(R.id.recentUrls).performClick();
        click(AlertDialog.BUTTON_POSITIVE);
        click(AlertDialog.BUTTON_POSITIVE);
        return ShadowAlertDialog.getLatestAlertDialog().getWindow().getDecorView()
                .findViewWithTag("link-transfer-input");
    }
    private ScanGate gate(MainActivity activity) throws Exception {
        java.lang.reflect.Field field = MainActivity.class.getDeclaredField("scanGate");
        field.setAccessible(true);
        return (ScanGate) field.get(activity);
    }

    @Test public void previewCancellationValidationAndConfirmedImport() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity activity = controller.get();
            String before = prefs.getString("recent_urls_v1", "");
            EditText input = openImport(activity);
            assertFalse(gate(activity).beginScan());
            input.setText("https://example.com/new\nhttp://example.com/bad");
            click(AlertDialog.BUTTON_POSITIVE);
            assertNotNull(input.getError());
            assertEquals(before, prefs.getString("recent_urls_v1", ""));
            input.setText("https://example.com/new");
            click(AlertDialog.BUTTON_POSITIVE);
            assertFalse(gate(activity).beginScan());
            assertEquals(before, prefs.getString("recent_urls_v1", ""));
            click(AlertDialog.BUTTON_NEGATIVE);
            assertEquals(before, prefs.getString("recent_urls_v1", ""));
            assertTrue(gate(activity).beginScan());
            gate(activity).finishScan();
            input = openImport(activity);
            input.setText("https://example.com/new");
            click(AlertDialog.BUTTON_POSITIVE);
            click(AlertDialog.BUTTON_POSITIVE);
            org.json.JSONArray stored = new org.json.JSONArray(prefs.getString("recent_urls_v1", ""));
            assertEquals(2, stored.length());
            assertEquals("https://example.com/old", stored.getString(0));
            assertEquals("https://example.com/new", stored.getString(1));
            assertEquals("https://example.com/current", prefs.getString("url", ""));
            assertTrue(prefs.getBoolean("inspect_only", false));
        }
        try (ActivityController<MainActivity> next = Robolectric.buildActivity(MainActivity.class).setup()) {
            assertTrue(prefs.getString("recent_urls_v1", "").contains("/new"));
            assertTrue(prefs.getBoolean("inspect_only", false));
        }
    }

    @Test public void recreationDoesNotCommitUnconfirmedPreview() {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            String before = prefs.getString("recent_urls_v1", "");
            openImport(controller.get()).setText("https://example.com/new");
            click(AlertDialog.BUTTON_POSITIVE);
            controller.recreate();
            assertEquals(before, prefs.getString("recent_urls_v1", ""));
        }
    }

    @Test public void exportShowsSavedLinksWithoutCopyingOrChangingDestination() {
        android.content.ClipboardManager clipboard = (android.content.ClipboardManager)
                RuntimeEnvironment.getApplication().getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(android.content.ClipData.newPlainText("fixture", "unchanged"));
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity activity = controller.get();
            activity.findViewById(R.id.recentUrls).performClick();
            click(AlertDialog.BUTTON_POSITIVE);
            click(AlertDialog.BUTTON_NEUTRAL);
            android.widget.TextView output = ShadowAlertDialog.getLatestAlertDialog()
                    .getWindow().getDecorView().findViewWithTag("link-transfer-output");
            assertEquals("https://example.com/old", output.getText().toString());
            assertTrue(output.isTextSelectable());
            assertEquals("unchanged", clipboard.getPrimaryClip().getItemAt(0).getText().toString());
            assertEquals("https://example.com/current", prefs.getString("url", ""));
        }
    }

    @Test
    @Config(sdk = 36, qualifiers = "w360dp-h800dp-xxhdpi")
    @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.NATIVE)
    public void rendersTransferPreview() throws Exception {
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup().visible()) {
            openImport(controller.get()).setText("https://example.com/portfolio\nhttps://example.com/contact");
            click(AlertDialog.BUTTON_POSITIVE);
            RecentUrlsActivityTest.capture(ShadowAlertDialog.getLatestAlertDialog()
                    .getWindow().getDecorView(), "transfer-preview");
        }
    }
}
