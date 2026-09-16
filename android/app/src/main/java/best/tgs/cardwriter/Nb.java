package best.tgs.cardwriter;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Build;
import android.util.TypedValue;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;

/**
 * The warm-paper neo-brutalist surface: flat pastel fills, dark ink outlines,
 * and a crisp offset shadow with no blur.
 *
 * Android's own elevation cannot express this — it draws a soft, spread shadow.
 * A card here is two rounded rectangles in one LayerDrawable: the ink slab
 * pushed down and right, and the fill inset back up and left by the same
 * amount. Pressing a card moves the fill onto its own shadow, which is what
 * makes it feel like something that physically travels.
 */
final class Nb {

    static final int INK = 0xFF262019;
    static final int CREAM = 0xFFFFF4DE;
    static final int PAPER = 0xFFFFFDF7;
    static final int BEIGE = 0xFFEFE2C3;

    static final int YELLOW = 0xFFFFD64A;
    static final int PINK = 0xFFF6B6CA;
    static final int SKY = 0xFFA9DCFA;
    static final int TERRACOTTA = 0xFFEB5B32;
    static final int SAGE = 0xFFBED7A6;

    static final int RADIUS_DP = 22;
    static final int BORDER_DP = 3;
    static final int DROP_DP = 7;
    static final int PRESS_DP = 3;

    private static Typeface display;
    private static Typeface displayBold;
    private static Typeface mono;
    private static Typeface monoBold;

    private Nb() {
    }

    static int dp(Context context, float value) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, value,
                context.getResources().getDisplayMetrics()));
    }

    /** A card: ink slab behind, pastel fill in front, both hard-edged. */
    static LayerDrawable card(Context context, int fill, int radiusDp, int dropDp) {
        GradientDrawable slab = new GradientDrawable();
        slab.setShape(GradientDrawable.RECTANGLE);
        slab.setCornerRadius(dp(context, radiusDp));
        slab.setColor(INK);

        GradientDrawable face = new GradientDrawable();
        face.setShape(GradientDrawable.RECTANGLE);
        face.setCornerRadius(dp(context, radiusDp));
        face.setColor(fill);
        face.setStroke(dp(context, BORDER_DP), INK);

        int drop = dp(context, dropDp);
        LayerDrawable card = new LayerDrawable(new Drawable[]{slab, face});
        card.setLayerInset(0, drop, drop, 0, 0);
        card.setLayerInset(1, 0, 0, drop, drop);
        return card;
    }

    static LayerDrawable card(Context context, int fill) {
        return card(context, fill, RADIUS_DP, DROP_DP);
    }

    /**
     * Install a background without losing the view's padding. LayerDrawable
     * reports padding of its own, and View.setBackground adopts it, which would
     * silently collapse every card's inner spacing.
     */
    static void skin(View view, Drawable background) {
        int left = view.getPaddingLeft();
        int top = view.getPaddingTop();
        int right = view.getPaddingRight();
        int bottom = view.getPaddingBottom();
        view.setBackground(background);
        view.setPadding(left, top, right, bottom);
    }

    /** Recolour a card already installed on a view, keeping its geometry. */
    static void refill(View view, int fill) {
        Drawable background = view.getBackground();
        if (background instanceof LayerDrawable) {
            Drawable face = ((LayerDrawable) background).getDrawable(1);
            if (face instanceof GradientDrawable) {
                ((GradientDrawable) face).setColor(fill);
            }
        }
    }

    /**
     * Give a view the travel of a real button: on press the fill slides onto
     * its shadow and the remaining shadow shrinks by the same amount, so the
     * card looks pushed in rather than merely moved.
     */
    static void pressable(final View view, final int fill, final int radiusDp) {
        final Context context = view.getContext();
        skin(view, card(context, fill, radiusDp, DROP_DP));
        final int travel = dp(context, PRESS_DP);
        view.setOnTouchListener((v, event) -> {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    v.setTranslationX(travel);
                    v.setTranslationY(travel);
                    skin(v, card(context, currentFill(v, fill), radiusDp,
                            DROP_DP - PRESS_DP));
                    break;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    v.setTranslationX(0);
                    v.setTranslationY(0);
                    skin(v, card(context, currentFill(v, fill), radiusDp, DROP_DP));
                    if (event.getActionMasked() == MotionEvent.ACTION_UP) {
                        v.performClick();
                    }
                    break;
                default:
                    break;
            }
            return true;
        });
    }

    private static int currentFill(View view, int fallback) {
        Drawable background = view.getBackground();
        if (background instanceof LayerDrawable) {
            Drawable face = ((LayerDrawable) background).getDrawable(1);
            if (face instanceof GradientDrawable) {
                android.content.res.ColorStateList tint = ((GradientDrawable) face).getColor();
                if (tint != null) {
                    return tint.getDefaultColor();
                }
            }
        }
        return fallback;
    }

    /** Warm cream page with the dot grid tiled over it. */
    static Drawable paper(Context context) {
        Resources resources = context.getResources();
        BitmapDrawable dots = new BitmapDrawable(resources,
                android.graphics.BitmapFactory.decodeResource(resources, R.drawable.paper_dot));
        dots.setTileModeXY(Shader.TileMode.REPEAT, Shader.TileMode.REPEAT);
        return new LayerDrawable(new Drawable[]{new ColorDrawable(CREAM), dots});
    }

    // Bricolage Grotesque ships as a variable font. Naming a weight on the axis
    // gives real heavy letterforms; older releases fall back to the synthetic
    // bold, which is heavier-looking but coarser.
    static Typeface display(Context context, boolean bold) {
        if (bold) {
            if (displayBold == null) {
                displayBold = variable(context, "fonts/BricolageGrotesque.ttf", 800);
            }
            return displayBold;
        }
        if (display == null) {
            display = variable(context, "fonts/BricolageGrotesque.ttf", 500);
        }
        return display;
    }

    static Typeface mono(Context context, boolean bold) {
        if (bold) {
            if (monoBold == null) {
                monoBold = Typeface.createFromAsset(context.getAssets(), "fonts/SpaceMono-Bold.ttf");
            }
            return monoBold;
        }
        if (mono == null) {
            mono = Typeface.createFromAsset(context.getAssets(), "fonts/SpaceMono-Regular.ttf");
        }
        return mono;
    }

    private static Typeface variable(Context context, String asset, int weight) {
        Typeface base = Typeface.createFromAsset(context.getAssets(), asset);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                return new Typeface.Builder(context.getAssets(), asset)
                        .setFontVariationSettings("'wght' " + weight)
                        .build();
            } catch (RuntimeException ignored) {
                // Fall through to the synthetic weight below.
            }
        }
        return weight >= 700 ? Typeface.create(base, Typeface.BOLD) : base;
    }

    /** Tiny uppercase monospace label, the metadata voice of the system. */
    static void label(TextView view) {
        view.setTypeface(mono(view.getContext(), true));
        view.setLetterSpacing(0.16f);
        view.setTextColor(withAlpha(INK, 0.62f));
    }

    static int withAlpha(int colour, float alpha) {
        return Color.argb(Math.round(255 * alpha), Color.red(colour), Color.green(colour),
                Color.blue(colour));
    }
}
