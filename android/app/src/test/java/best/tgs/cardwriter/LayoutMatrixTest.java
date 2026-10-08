package best.tgs.cardwriter;

import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 36}, qualifiers = "mdpi")
public class LayoutMatrixTest {
    @Test public void controlsRemainReadableInPortraitLandscapeAndLargeText() {
        int[][] sizes = {{320, 640}, {360, 800}, {640, 360}, {800, 600}};
        float[] scales = {1f, 1.6f, 2f};
        try {
            for (int[] size : sizes) for (float scale : scales) {
                RuntimeEnvironment.setQualifiers("w" + size[0] + "dp-h" + size[1] + "dp-mdpi");
                RuntimeEnvironment.setFontScale(scale);
                try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
                    View root = controller.get().getWindow().getDecorView();
                    root.measure(View.MeasureSpec.makeMeasureSpec(size[0], View.MeasureSpec.EXACTLY),
                            View.MeasureSpec.makeMeasureSpec(size[1], View.MeasureSpec.EXACTLY));
                    root.layout(0, 0, size[0], size[1]);
                    checkControls(controller.get().findViewById(android.R.id.content),
                            size[0] + "x" + size[1] + " @ " + scale);
                    assertEquals(View.GONE, controller.get().findViewById(R.id.evidence).getVisibility());
                }
            }
        } finally {
            RuntimeEnvironment.setFontScale(1f);
        }
    }

    private void checkControls(View view, String context) {
        if (view.getVisibility() != View.VISIBLE) return;
        if (view instanceof Button) {
            Button button = (Button) view;
            assertTrue(context + " button too short", button.getHeight() >= 48);
            assertNotNull(button.getLayout());
            int last = button.getLayout().getLineCount() - 1;
            assertEquals(context + " truncated button " + button.getText(), 0,
                    button.getLayout().getEllipsisCount(last));
            assertTrue(context + " clipped button text " + button.getText(),
                    button.getLayout().getHeight() <= button.getHeight()
                            - button.getCompoundPaddingTop() - button.getCompoundPaddingBottom());
        }
        if (view.getId() == R.id.inspectOnlyTitle || view.getId() == R.id.allowUnknownTitle) {
            TextView label = (TextView) view;
            assertTrue(context + " clipped mode label", label.getLayout().getHeight()
                    <= label.getHeight() - label.getCompoundPaddingTop() - label.getCompoundPaddingBottom());
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                View child = group.getChildAt(i);
                if (child.getVisibility() == View.VISIBLE) {
                    assertTrue(context + " horizontal overflow", child.getRight() <= group.getWidth());
                    checkControls(child, context);
                }
            }
        }
    }
}
