package android.nfc.tech;

import java.io.IOException;

/**
 * A desktop stand-in for the platform class, so the retry, reconnect and
 * acknowledgement logic in Tag215 can be exercised without a phone.
 *
 * This file is compiled only by tools/parity.sh, never by the app: the real
 * android.nfc.tech.NfcA always wins on a device, because android.jar is ahead
 * of this on the compile classpath and this directory is not in the app's
 * source set at all. It exists so that the part of the writer most likely to
 * be wrong — what happens when a card answers badly — has checks that run on
 * every commit rather than only when someone has a wooden card to hand.
 *
 * The method signatures mirror the platform's. Nothing here models the radio;
 * LinkTest supplies the behaviour by overriding transceive().
 */
public class NfcA {

    public void connect() throws IOException {
    }

    public void close() throws IOException {
    }

    public void setTimeout(int millis) {
    }

    public int getMaxTransceiveLength() {
        return 253;
    }

    public byte[] transceive(byte[] command) throws IOException {
        throw new IOException("No card.");
    }
}
