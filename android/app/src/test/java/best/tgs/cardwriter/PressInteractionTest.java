package best.tgs.cardwriter;

import android.app.Activity;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.widget.Button;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

/** Real View event dispatch: decoration must never invent a click. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 36})
public class PressInteractionTest {
    @Test public void nativeTapCancellationAndDisabledBehaviorArePreserved() {
        try (ActivityController<Activity> controller = Robolectric.buildActivity(Activity.class).setup()) {
            Button button = new Button(controller.get());
            controller.get().setContentView(button);
            button.layout(0, 0, 200, 100);
            AtomicInteger clicks = new AtomicInteger();
            button.setOnClickListener(v -> clicks.incrementAndGet());
            Nb.pressable(button, Nb.FOREST, 10);

            event(button, MotionEvent.ACTION_DOWN, 30, 30);
            event(button, MotionEvent.ACTION_UP, 30, 30);
            assertEquals(1, clicks.get());
            assertEquals(0f, button.getTranslationX(), 0f);

            event(button, MotionEvent.ACTION_DOWN, 30, 30);
            event(button, MotionEvent.ACTION_MOVE, 400, 30);
            event(button, MotionEvent.ACTION_UP, 400, 30);
            assertEquals("Dragging outside must not click", 1, clicks.get());

            event(button, MotionEvent.ACTION_DOWN, 30, 30);
            event(button, MotionEvent.ACTION_CANCEL, 30, 30);
            assertEquals(1, clicks.get());
            assertEquals(0f, button.getTranslationY(), 0f);

            event(button, MotionEvent.ACTION_UP, 30, 30);
            assertEquals("A release without a press must not click", 1, clicks.get());

            button.setEnabled(false);
            event(button, MotionEvent.ACTION_DOWN, 30, 30);
            event(button, MotionEvent.ACTION_UP, 30, 30);
            assertEquals(1, clicks.get());
            button.setEnabled(true);
            button.performClick();
            assertEquals("Accessibility clicks still work", 2, clicks.get());
        }
    }

    @Test public void draggingOffInspectControlCannotChangeWriteMode() {
        RuntimeFixtures.clearPreferences();
        try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
            android.view.View control = controller.get().findViewById(R.id.inspectOnly);
            control.layout(0, 0, 200, 100);
            android.widget.TextView state = controller.get().findViewById(R.id.inspectOnlyState);
            assertEquals("OFF", state.getText().toString());
            event(control, MotionEvent.ACTION_DOWN, 30, 30);
            event(control, MotionEvent.ACTION_UP, 30, 30);
            assertEquals("ON", state.getText().toString());
            event(control, MotionEvent.ACTION_DOWN, 30, 30);
            event(control, MotionEvent.ACTION_MOVE, 400, 30);
            event(control, MotionEvent.ACTION_UP, 400, 30);
            assertEquals("ON", state.getText().toString());
        }
    }

    private void event(android.view.View button, int action, float x, float y) {
        long time = SystemClock.uptimeMillis();
        MotionEvent event = MotionEvent.obtain(time, time, action, x, y, 0);
        button.dispatchTouchEvent(event);
        event.recycle();
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
    }

    private static class RuntimeFixtures {
        static void clearPreferences() {
            org.robolectric.RuntimeEnvironment.getApplication()
                    .getSharedPreferences("card-writer", android.content.Context.MODE_PRIVATE)
                    .edit().clear().commit();
        }
    }
}
