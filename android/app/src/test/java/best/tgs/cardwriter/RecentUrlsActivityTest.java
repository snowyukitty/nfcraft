package best.tgs.cardwriter;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.widget.EditText;
import android.widget.TextView;
import android.os.Looper;
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

/** Real activity/preferences/dialog wiring; never connects NFC or owner data. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 36})
public class RecentUrlsActivityTest {
    private SharedPreferences prefs;

    @Before public void cleanFixture() {
        prefs = RuntimeEnvironment.getApplication().getSharedPreferences("card-writer", Context.MODE_PRIVATE);
        prefs.edit().clear().commit();
    }

    private void save(MainActivity activity, String value) {
        ((EditText) activity.findViewById(R.id.url)).setText(value);
        activity.findViewById(R.id.saveUrl).performClick();
    }

    @Test public void savesSelectsRestartsAndClearsWithoutLosingCurrentDestination() {
        ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup();
        MainActivity activity = controller.get();
        for (int i = 0; i < 12; i++) save(activity, "https://example.com/" + i);
        assertEquals("Recent (10/10)", ((TextView) activity.findViewById(R.id.recentUrls)).getText().toString());
        activity.findViewById(R.id.recentUrls).performClick();
        AlertDialog list = ShadowAlertDialog.getLatestAlertDialog();
        assertEquals(10, list.getListView().getCount());
        assertEquals("https://example.com/11", list.getListView().getAdapter().getItem(0));
        list.getListView().performItemClick(null, 3, 3);
        assertEquals("https://example.com/8", ((EditText) activity.findViewById(R.id.url)).getText().toString());
        controller.pause().stop().destroy();
        controller = Robolectric.buildActivity(MainActivity.class).setup();
        activity = controller.get();
        activity.findViewById(R.id.recentUrls).performClick();
        list = ShadowAlertDialog.getLatestAlertDialog();
        assertEquals("https://example.com/8", list.getListView().getAdapter().getItem(0));
        list.getButton(AlertDialog.BUTTON_NEUTRAL).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_NEGATIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertFalse(prefs.getString("recent_urls_v1", "[]").equals("[]"));
        activity.findViewById(R.id.recentUrls).performClick();
        ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_NEUTRAL).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        ShadowAlertDialog.getLatestAlertDialog().getButton(AlertDialog.BUTTON_POSITIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals("[]", prefs.getString("recent_urls_v1", "missing"));
        assertEquals("https://example.com/8", prefs.getString("url", ""));
        controller.pause().stop().destroy();
        controller = Robolectric.buildActivity(MainActivity.class).setup();
        assertEquals("Recent (0/10)", ((TextView) controller.get().findViewById(R.id.recentUrls)).getText().toString());
        controller.pause().stop().destroy();
    }

    @Test public void migratesOnceAndRejectsInvalidDrafts() {
        prefs.edit().putString("url", "https://example.com/legacy").commit();
        ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup();
        MainActivity activity = controller.get();
        assertTrue(prefs.getString("recent_urls_v1", "").contains("legacy"));
        save(activity, "http://example.com/invalid");
        assertFalse(prefs.getString("recent_urls_v1", "").contains("invalid"));
        controller.pause().stop().destroy();
        prefs.edit().putString("recent_urls_v1", "not json").commit();
        controller = Robolectric.buildActivity(MainActivity.class).setup();
        assertEquals("[]", prefs.getString("recent_urls_v1", ""));
        controller.pause().stop().destroy();
    }

    @Test
    @Config(sdk = 36, qualifiers = "w360dp-h800dp-xxhdpi")
    @GraphicsMode(GraphicsMode.Mode.NATIVE)
    public void rendersPhoneLayoutForVisualReview() throws Exception {
        ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup().visible();
        MainActivity activity = controller.get();
        save(activity, "https://example.com/portfolio");
        save(activity, "https://example.com/contact");
        shadowOf(Looper.getMainLooper()).idle();
        capture(activity.getWindow().getDecorView(), "destination");
        activity.findViewById(R.id.recentUrls).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        capture(ShadowAlertDialog.getLatestAlertDialog().getWindow().getDecorView(), "recent-links");
        android.graphics.drawable.Drawable icon = activity.getDrawable(R.mipmap.ic_launcher);
        android.graphics.Bitmap image = android.graphics.Bitmap.createBitmap(192, 192,
                android.graphics.Bitmap.Config.ARGB_8888);
        icon.setBounds(0, 0, 192, 192);
        icon.draw(new android.graphics.Canvas(image));
        try (java.io.FileOutputStream out = new java.io.FileOutputStream("build/reports/visual/adaptive-icon.png")) {
            image.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
        }
        android.graphics.drawable.Drawable mono = ((android.graphics.drawable.AdaptiveIconDrawable) icon).getMonochrome();
        assertNotNull(mono);
        image.eraseColor(android.graphics.Color.WHITE);
        mono.setBounds(0, 0, 192, 192);
        mono.setTint(android.graphics.Color.BLACK);
        mono.draw(new android.graphics.Canvas(image));
        try (java.io.FileOutputStream out = new java.io.FileOutputStream("build/reports/visual/themed-icon.png")) {
            image.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
        }
        controller.pause().stop().destroy();
    }

    private void capture(android.view.View view, String name) throws Exception {
        int width = 1080, height = 2400;
        view.measure(android.view.View.MeasureSpec.makeMeasureSpec(width, android.view.View.MeasureSpec.EXACTLY),
                android.view.View.MeasureSpec.makeMeasureSpec(height, android.view.View.MeasureSpec.AT_MOST));
        view.layout(0, 0, width, view.getMeasuredHeight());
        assertTrue(view.getMeasuredHeight() > 0);
        android.graphics.Bitmap bitmap = android.graphics.Bitmap.createBitmap(width, view.getMeasuredHeight(),
                android.graphics.Bitmap.Config.ARGB_8888);
        view.draw(new android.graphics.Canvas(bitmap));
        java.io.File directory = new java.io.File("build/reports/visual");
        directory.mkdirs();
        try (java.io.FileOutputStream out = new java.io.FileOutputStream(new java.io.File(directory, name + ".png"))) {
            bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
        }
    }
}
