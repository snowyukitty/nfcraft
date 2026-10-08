package best.tgs.cardwriter;

import org.junit.Test;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

public class ScanGateTest {
    @Test public void foregroundAndNestedModalsControlAdmission() {
        ScanGate gate = new ScanGate();
        assertFalse(gate.beginScan());
        assertTrue(gate.beginModal());
        gate.resume();
        assertFalse(gate.beginScan());
        assertTrue(gate.beginModal());
        gate.endModal();
        assertFalse(gate.beginScan());
        gate.endModal();
        assertTrue(gate.beginScan());
        assertFalse(gate.beginScan());
        assertFalse(gate.beginModal());
        gate.pause();
        gate.resume();
        assertFalse(gate.beginScan()); // foreground transitions do not cancel an admitted write
        gate.finishScan();
        assertTrue(gate.beginScan());
        gate.finishScan();
        gate.pause();
        assertFalse(gate.beginScan());
    }

    @Test public void dialogAndScanCannotBothWinTheSameAdmissionRace() throws Exception {
        for (int i = 0; i < 100; i++) {
            ScanGate gate = new ScanGate();
            gate.resume();
            CountDownLatch start = new CountDownLatch(1);
            AtomicInteger admitted = new AtomicInteger();
            Thread scan = new Thread(() -> {
                await(start);
                if (gate.beginScan()) admitted.incrementAndGet();
            });
            Thread modal = new Thread(() -> {
                await(start);
                if (gate.beginModal()) admitted.incrementAndGet();
            });
            scan.start(); modal.start(); start.countDown();
            scan.join(); modal.join();
            assertEquals(1, admitted.get());
            gate.finishScan();
            gate.endModal();
        }
    }

    @Test public void replacementActivityWaitsForThePreviousOperationToClose() {
        ScanGate previous = new ScanGate();
        ScanGate replacement = new ScanGate();
        previous.resume();
        assertTrue(previous.beginScan());
        previous.pause();
        replacement.resume();
        assertFalse(replacement.beginScan());
        assertFalse(replacement.beginModal());
        replacement.finishScan(); // cannot release an operation owned by the old Activity
        assertFalse(replacement.beginScan());
        previous.finishScan();
        assertTrue(replacement.beginScan());
        previous.finishScan(); // a duplicate finish cannot release the replacement's operation
        assertFalse(replacement.beginModal());
        replacement.finishScan();
        assertTrue(replacement.beginModal());
        replacement.endModal();
    }

    private static void await(CountDownLatch latch) {
        try { latch.await(); } catch (InterruptedException e) { throw new AssertionError(e); }
    }
}
