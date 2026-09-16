package best.tgs.cardwriter;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.NfcA;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.TextView;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * One screen that rewrites one card at a time.
 *
 * Reader mode is the whole reason this is a native app: while this activity is
 * in the foreground it owns the NFC field, so the system tag viewer never sees
 * a card and cannot steal the scan the way it does from a browser tab.
 *
 * The result is carried by the hero card's fill, not by a line of text. From
 * arm's length, on a bench, that colour is the whole message.
 */
public final class MainActivity extends Activity implements NfcAdapter.ReaderCallback {

    private static final String PREFS = "card-writer";
    private static final String KEY_URL = "url";
    private static final String KEY_INSPECT = "inspect_only";
    private static final String KEY_ALLOW = "allow_unknown";

    /**
     * Where the current batch of cards points. This is only the starting value:
     * whatever is in the field is what gets written, and an edit is saved and
     * restored on the next launch. A blank field falls back here rather than
     * being remembered, because an empty destination is never writable anyway.
     */
    private static final String DEFAULT_URL = "https://tgs.best";

    /**
     * Wooden cards couple weakly and a whole plan — inspect, full read, up to
     * fifty page writes, full readback, re-inspect — runs while the platform
     * keeps polling the tag. At the old 250 ms the poll lands in the middle of
     * that and the write tears; the operator sees "card moved" for a card that
     * never left the phone.
     */
    private static final int PRESENCE_CHECK_MS = 2000;

    /** A blank slip, so the receipt card keeps its place between cards. */
    private static final String RESTING_RECEIPT = "uid    —\nheld   —";

    private static final int SOUND_NONE = 0;
    private static final int SOUND_WRITTEN = 1;
    private static final int SOUND_VERIFIED = 2;
    private static final int SOUND_FAIL = 3;

    /** How far into the write plan a card got, for honest failure copy. */
    private static final int STAGE_UNTOUCHED = 0;
    private static final int STAGE_WRITING = 1;
    private static final int STAGE_COMMITTED = 2;

    private final Handler ui = new Handler(Looper.getMainLooper());
    private final AtomicBoolean busy = new AtomicBoolean(false);

    private EditText url;
    private TextView urlProblem;
    private TextView headline;
    private TextView detail;
    private TextView counter;
    private TextView evidence;
    private View destinationCard;
    private View stage;
    private View inspectOnly;
    private View allowUnknown;
    private TextView inspectOnlyState;
    private TextView allowUnknownState;
    private TextView inspectOnlyTitle;
    private TextView allowUnknownTitle;

    private SharedPreferences prefs;
    private ToneGenerator tones;
    private Vibrator vibrator;

    // Views may only be read on the UI thread, and onTagDiscovered is a binder
    // callback. These are the snapshot the NFC path is allowed to see.
    private volatile String targetUrl = "";
    private volatile boolean inspectOnlyNow;
    private volatile boolean allowUnknownNow;

    private volatile int writeStage = STAGE_UNTOUCHED;
    private int written;

    /** What one card presentation produced. */
    private static final class Outcome {
        final int fill;
        final String headline;
        final String detail;
        final String evidence;
        final int sound;

        Outcome(int fill, String headline, String detail, String evidence, int sound) {
            this.fill = fill;
            this.headline = headline;
            this.detail = detail;
            this.evidence = evidence;
            this.sound = sound;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        url = findViewById(R.id.url);
        urlProblem = findViewById(R.id.urlProblem);
        headline = findViewById(R.id.headline);
        detail = findViewById(R.id.detail);
        counter = findViewById(R.id.counter);
        evidence = findViewById(R.id.evidence);
        destinationCard = findViewById(R.id.destinationCard);
        stage = findViewById(R.id.stage);
        inspectOnly = findViewById(R.id.inspectOnly);
        allowUnknown = findViewById(R.id.allowUnknown);
        inspectOnlyState = findViewById(R.id.inspectOnlyState);
        allowUnknownState = findViewById(R.id.allowUnknownState);
        inspectOnlyTitle = findViewById(R.id.inspectOnlyTitle);
        allowUnknownTitle = findViewById(R.id.allowUnknownTitle);

        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        dress();

        String saved = prefs.getString(KEY_URL, DEFAULT_URL);
        url.setText(saved.isEmpty() ? DEFAULT_URL : saved);
        setToggle(inspectOnly, inspectOnlyState, prefs.getBoolean(KEY_INSPECT, false), Nb.SKY);
        setToggle(allowUnknown, allowUnknownState, prefs.getBoolean(KEY_ALLOW, false),
                Nb.TERRACOTTA);
        snapshot();

        url.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b, int c) {
            }

            public void onTextChanged(CharSequence s, int a, int b, int c) {
            }

            public void afterTextChanged(Editable s) {
                String value = s.toString().trim();
                prefs.edit().putString(KEY_URL, value).apply();
                snapshot();
                showUrlProblem(value);
            }
        });

        inspectOnly.setOnClickListener(v -> {
            boolean next = !inspectOnlyNow;
            prefs.edit().putBoolean(KEY_INSPECT, next).apply();
            setToggle(inspectOnly, inspectOnlyState, next, Nb.SKY);
            snapshot();
        });
        allowUnknown.setOnClickListener(v -> {
            boolean next = !allowUnknownNow;
            prefs.edit().putBoolean(KEY_ALLOW, next).apply();
            setToggle(allowUnknown, allowUnknownState, next, Nb.TERRACOTTA);
            snapshot();
        });

        showUrlProblem(targetUrl);
        paint(Nb.PAPER, "Starting", "", null);
    }

    /** Apply the paper surface, the ink outlines and the two typefaces. */
    private void dress() {
        View root = findViewById(android.R.id.content);
        Nb.skin(root, Nb.paper(this));

        Nb.skin(destinationCard, Nb.card(this, Nb.PAPER));
        Nb.skin(stage, Nb.card(this, Nb.PAPER));
        Nb.skin(evidence, Nb.card(this, Nb.BEIGE));

        // A sticker, not a label: small radius, shallow drop, and off the grid
        // by a couple of degrees so the count reads as something stuck on.
        Nb.skin(counter, Nb.card(this, Nb.YELLOW, 13, 4));
        counter.setRotation(-2.2f);

        Nb.pressable(inspectOnly, Nb.PAPER, 18);
        Nb.pressable(allowUnknown, Nb.PAPER, 18);

        Nb.label(findViewById(R.id.destinationLabel));
        Nb.label(inspectOnlyTitle);
        Nb.label(allowUnknownTitle);

        TextView footnote = findViewById(R.id.footnote);
        Nb.label(footnote);
        footnote.setTextColor(Nb.withAlpha(Nb.INK, 0.45f));

        url.setTypeface(Nb.display(this, false));
        url.setTextColor(Nb.INK);
        url.setHintTextColor(Nb.withAlpha(Nb.INK, 0.3f));

        urlProblem.setTypeface(Nb.mono(this, false));
        urlProblem.setTextColor(0xFFA8371A);

        headline.setTypeface(Nb.display(this, true));
        headline.setTextColor(Nb.INK);

        detail.setTypeface(Nb.display(this, false));
        detail.setTextColor(Nb.withAlpha(Nb.INK, 0.8f));

        counter.setTypeface(Nb.mono(this, true));
        counter.setLetterSpacing(0.12f);
        counter.setTextColor(Nb.INK);

        evidence.setTypeface(Nb.mono(this, false));
        evidence.setTextColor(Nb.withAlpha(Nb.INK, 0.78f));

        inspectOnlyState.setTypeface(Nb.display(this, true));
        inspectOnlyState.setTextColor(Nb.INK);
        allowUnknownState.setTypeface(Nb.display(this, true));
        allowUnknownState.setTextColor(Nb.INK);
    }

    private void setToggle(View chip, TextView state, boolean on, int onFill) {
        Nb.refill(chip, on ? onFill : Nb.PAPER);
        chip.invalidate();
        state.setText(on ? "ON" : "OFF");
        // A saturated fill eats the softened label, so the title goes to full
        // ink whenever the chip is lit.
        TextView title = chip == inspectOnly ? inspectOnlyTitle : allowUnknownTitle;
        title.setTextColor(on ? Nb.INK : Nb.withAlpha(Nb.INK, 0.62f));
        if (chip == inspectOnly) {
            inspectOnlyNow = on;
        } else {
            allowUnknownNow = on;
        }
    }

    /** Copy every value the NFC thread needs. Call only on the UI thread. */
    private void snapshot() {
        targetUrl = url.getText().toString().trim();
    }

    @Override
    protected void onResume() {
        super.onResume();
        snapshot();
        NfcAdapter adapter = NfcAdapter.getDefaultAdapter(this);
        if (adapter == null) {
            paint(Nb.TERRACOTTA, "No NFC", "This device has no NFC hardware.", null);
            return;
        }
        if (!adapter.isEnabled()) {
            paint(Nb.TERRACOTTA, "NFC is off", "Turn NFC on in Settings, then return here.", null);
            return;
        }
        Bundle extras = new Bundle();
        extras.putInt(NfcAdapter.EXTRA_READER_PRESENCE_CHECK_DELAY, PRESENCE_CHECK_MS);
        adapter.enableReaderMode(this, this,
                NfcAdapter.FLAG_READER_NFC_A
                        | NfcAdapter.FLAG_READER_SKIP_NDEF_CHECK
                        | NfcAdapter.FLAG_READER_NO_PLATFORM_SOUNDS,
                extras);
        paint(Nb.PAPER, "Ready", "Hold a card against the back of the phone.", null);
    }

    @Override
    protected void onPause() {
        super.onPause();
        NfcAdapter adapter = NfcAdapter.getDefaultAdapter(this);
        if (adapter != null) {
            adapter.disableReaderMode(this);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (tones != null) {
            tones.release();
            tones = null;
        }
    }

    /** Called on a binder thread, never on the UI thread. */
    @Override
    public void onTagDiscovered(Tag tag) {
        // Reader mode can rediscover a tag while the previous pass is still
        // closing. Only one NFC technology may be connected at a time, so this
        // has to be a compare-and-set, not a check followed by a set.
        if (!busy.compareAndSet(false, true)) {
            return;
        }
        writeStage = STAGE_UNTOUCHED;
        try {
            post(new Outcome(Nb.YELLOW, "Working", "Hold the card still.", null, SOUND_NONE));
            Outcome outcome;
            NfcA nfcA = NfcA.get(tag);
            if (nfcA == null) {
                outcome = new Outcome(Nb.TERRACOTTA, "Not NTAG215",
                        "This tag does not speak NFC-A. Nothing was attempted.", null, SOUND_FAIL);
            } else {
                // Declared outside the try so the failure copy can still report
                // what the link cost before it gave out.
                Tag215 card = null;
                try {
                    card = Tag215.open(nfcA);
                    // The operator is holding the card right now, and the only
                    // thing they can do about a weak link is stop moving. Say
                    // so while it still helps, not in the receipt afterwards.
                    card.watch(() -> post(new Outcome(Nb.TERRACOTTA, "Weak contact",
                            "Hold the card still against the back of the phone."
                                    + " Still trying.", null, SOUND_NONE)));
                    outcome = handle(card);
                } catch (Tag215.Refusal refusal) {
                    outcome = new Outcome(Nb.TERRACOTTA, refusal.headline, refusal.getMessage(),
                            receipt(card, null), SOUND_FAIL);
                } catch (IOException e) {
                    outcome = lostContact(card, e);
                } catch (RuntimeException e) {
                    outcome = new Outcome(Nb.TERRACOTTA, "Failed", describe(e),
                            receipt(card, null), SOUND_FAIL);
                } finally {
                    try {
                        nfcA.close();
                    } catch (IOException ignored) {
                        // Closing a card that already left the field is not a failure.
                    }
                }
            }
            post(outcome);
        } finally {
            busy.set(false);
        }
    }

    /**
     * Losing the card means different things at different points in the plan,
     * and the operator has to be told which one happened. "Tap it again" is
     * only honest before the first page write.
     */
    private Outcome lostContact(Tag215 card, IOException e) {
        // Every exchange has already been retried and the link re-established
        // where it could be, so reaching here means the card really is gone,
        // not that one command was unlucky.
        String because = " (" + describe(e) + ")";
        String facts = receipt(card, null);
        switch (writeStage) {
            case STAGE_COMMITTED:
                return new Outcome(Nb.PINK, "Not confirmed",
                        "The message was committed but the verifying readback did not finish"
                                + because + " Tap the same card again to confirm it.",
                        facts, SOUND_FAIL);
            case STAGE_WRITING:
                return new Outcome(Nb.PINK, "Write interrupted",
                        "The card left the field part-way through" + because
                                + " It now holds an incomplete message. Hold it still and tap"
                                + " again — this app recognises its own interrupted write and"
                                + " finishes it without repeating the pages that already took.",
                        facts, SOUND_FAIL);
            default:
                return new Outcome(Nb.PINK, "Card moved",
                        "Lost contact before anything was written" + because
                                + " The card is unchanged. Tap it again.",
                        facts, SOUND_FAIL);
        }
    }

    /**
     * The receipt card. What the link cost is on it whenever it cost anything,
     * because a card that needed four reconnects to succeed is a warning about
     * the next hundred, not a success to be filed away silently.
     */
    private String receipt(Tag215 card, String facts) {
        String body = facts == null ? RESTING_RECEIPT : facts;
        if (card == null || !card.struggled()) {
            return body;
        }
        String path = card.readPath();
        return body + "\nlink   " + card.effort() + (path.isEmpty() ? "" : " · " + path);
    }

    private Outcome handle(Tag215 card) throws IOException, Tag215.Refusal {
        Tag215.Inspection before = card.inspect();
        String identity = "uid    " + before.uidHex();
        String problem = before.unsafe();
        if (problem != null) {
            return new Outcome(Nb.TERRACOTTA, "Refused", problem, receipt(card, identity), SOUND_FAIL);
        }

        byte[] original = card.readArea();
        if (original.length != Ndef.NDEF_CAPACITY) {
            return new Outcome(Nb.TERRACOTTA, "Unexpected geometry",
                    "Read " + original.length + " bytes where " + Ndef.NDEF_CAPACITY
                            + " were expected. Nothing was written.", receipt(card, identity), SOUND_FAIL);
        }
        String held = Ndef.decodeArea(original);

        if (inspectOnlyNow) {
            String label = held != null
                    ? held
                    : (Ndef.isEmpty(original) ? "(blank)" : "(content this app does not recognise)");
            return new Outcome(Nb.SKY, "Inspected",
                    held != null ? "This card points at " + held
                            : "No recognisable URL record on this card.",
                    receipt(card, identity + "\nheld   " + label), SOUND_VERIFIED);
        }

        String target = targetUrl;
        String invalid = Ndef.validate(target);
        if (invalid != null) {
            return new Outcome(Nb.TERRACOTTA, "No destination", invalid, receipt(card, identity), SOUND_FAIL);
        }

        byte[] area;
        try {
            area = Ndef.encodeArea(target);
        } catch (IllegalArgumentException e) {
            return new Outcome(Nb.TERRACOTTA, "No destination", e.getMessage(), receipt(card, identity), SOUND_FAIL);
        }

        boolean resumable = Ndef.isOurStagedWrite(original, area);
        String heldLabel = held != null
                ? held
                : resumable
                ? "(an interrupted write by this app)"
                : Ndef.isEmpty(original) ? "(blank)" : "(content this app does not recognise)";
        String facts = identity + "\nheld   " + heldLabel;

        if (target.equals(held)) {
            return new Outcome(Nb.SKY, "Already done",
                    "This card already carries the destination. The readback matched.",
                    receipt(card, facts), SOUND_VERIFIED);
        }

        if (!allowUnknownNow && !resumable) {
            if (held == null && !Ndef.isEmpty(original)) {
                return new Outcome(Nb.TERRACOTTA, "Unfamiliar content",
                        "This card holds data this app does not recognise. Nothing was written."
                                + " Turn on OVERWRITE UNKNOWN if you are sure it is yours.",
                        receipt(card, facts), SOUND_FAIL);
            }
            if (Ndef.hidesDataUnderEmptyTlv(original, area.length)) {
                return new Outcome(Nb.TERRACOTTA, "Occupied write region",
                        "The NDEF message is empty but the region to be written holds data."
                                + " Nothing was written.",
                        receipt(card, facts), SOUND_FAIL);
            }
        }

        // Only the pages that would actually change are sent. A card that tore
        // part-way through its last presentation keeps everything that already
        // took, so the second tap is short — which is the point, because the
        // link that failed the long way round is the same one being asked
        // again.
        //
        // The stage moves before each attempt, not after it: a write that
        // threw may still have reached the tag, so the failure copy must never
        // claim the card is untouched once a page has been sent.
        List<Ndef.Step> plan = Ndef.writePlan(target, original);
        for (int i = 0; i < plan.size(); i++) {
            writeStage = STAGE_WRITING;
            Ndef.Step step = plan.get(i);
            card.writePage(step.page, step.data);
            if (i == plan.size() - 1) {
                writeStage = STAGE_COMMITTED;
            }
        }

        // The write is not the evidence. The readback of the whole advertised
        // area is, together with the preserved tail beyond what we wrote and an
        // unchanged identity and configuration.
        byte[] observed = card.readArea();
        byte[] expected = Arrays.copyOf(original, original.length);
        System.arraycopy(area, 0, expected, 0, area.length);
        if (!Arrays.equals(observed, expected)) {
            return new Outcome(Nb.TERRACOTTA, "Readback differs",
                    "The full user-area readback does not match the intended write and the"
                            + " preserved tail. Set this card aside.", receipt(card, facts), SOUND_FAIL);
        }
        Tag215.Inspection after = card.inspect();
        if (!after.sameAs(before)) {
            return new Outcome(Nb.TERRACOTTA, "Identity changed",
                    "Tag identity or protected configuration changed during the write."
                            + " Set this card aside.", receipt(card, facts), SOUND_FAIL);
        }

        written++;
        return new Outcome(Nb.SAGE, resumable ? "Finished" : "Written",
                "Verified by full readback. Remove the card.",
                receipt(card, identity + "\nnow    " + target + "\nbefore " + heldLabel),
                SOUND_WRITTEN);
    }

    private void showUrlProblem(String value) {
        String problem = value.isEmpty() ? null : Ndef.validate(value);
        urlProblem.setText(problem == null ? "" : problem);
        urlProblem.setVisibility(problem == null ? View.GONE : View.VISIBLE);
    }

    private void post(final Outcome outcome) {
        ui.post(() -> {
            paint(outcome.fill, outcome.headline, outcome.detail, outcome.evidence);
            signal(outcome.sound);
        });
    }

    private void paint(int fill, String title, String message, String facts) {
        Nb.refill(stage, fill);
        stage.invalidate();
        headline.setText(title);
        detail.setText(message == null ? "" : message);
        detail.setVisibility(message == null || message.isEmpty() ? View.GONE : View.VISIBLE);
        // The receipt keeps its place when there is nothing on it, so the
        // page never reflows under the operator between one card and the next.
        evidence.setText(facts == null || facts.isEmpty() ? RESTING_RECEIPT : facts);
        counter.setText(written == 1 ? "1 CARD WRITTEN" : written + " CARDS WRITTEN");
    }

    private void signal(int sound) {
        if (sound == SOUND_NONE) {
            return;
        }
        if (tones == null) {
            try {
                tones = new ToneGenerator(AudioManager.STREAM_MUSIC, 90);
            } catch (RuntimeException e) {
                tones = null;
            }
        }
        if (tones != null) {
            if (sound == SOUND_WRITTEN) {
                tones.startTone(ToneGenerator.TONE_PROP_BEEP, 120);
            } else if (sound == SOUND_VERIFIED) {
                tones.startTone(ToneGenerator.TONE_PROP_ACK, 180);
            } else {
                tones.startTone(ToneGenerator.TONE_PROP_NACK, 400);
            }
        }
        long[] pattern = sound == SOUND_WRITTEN
                ? new long[]{0, 60}
                : sound == SOUND_VERIFIED
                ? new long[]{0, 40, 60, 40}
                : new long[]{0, 200, 100, 200};
        vibrate(pattern);
    }

    private void vibrate(long[] pattern) {
        if (vibrator == null || !vibrator.hasVibrator()) {
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
        } else {
            vibrator.vibrate(pattern, -1);
        }
    }

    private static String describe(Throwable e) {
        String message = e.getMessage();
        if (message == null || message.isEmpty()) {
            message = e.getClass().getSimpleName();
        }
        return message.endsWith(".") ? message.substring(0, message.length() - 1) : message;
    }
}
