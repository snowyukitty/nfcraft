package best.tgs.cardwriter;

import java.util.concurrent.atomic.AtomicBoolean;

/** Serializes presentation admission with foreground and modal UI transitions.
 * An admitted operation finishes normally; hiding the UI never interrupts a page write.
 */
final class ScanGate {
    // Activity recreation must not admit a second operation while the old one closes.
    private static final AtomicBoolean PROCESS_OPERATION = new AtomicBoolean(false);
    private boolean foreground;
    private boolean running;
    private int modals;

    synchronized void resume() { foreground = true; }
    synchronized void pause() { foreground = false; }
    synchronized boolean ready() { return foreground && modals == 0; }
    synchronized boolean beginScan() {
        if (!ready() || running || !PROCESS_OPERATION.compareAndSet(false, true)) return false;
        running = true;
        return true;
    }
    synchronized void finishScan() {
        if (running) {
            running = false;
            PROCESS_OPERATION.set(false);
        }
    }
    synchronized boolean beginModal() {
        if (PROCESS_OPERATION.get()) return false;
        modals++;
        return true;
    }
    synchronized void endModal() {
        if (modals > 0) modals--;
    }
}
