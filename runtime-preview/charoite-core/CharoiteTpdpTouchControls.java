package com.charoitegames.core;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import com.winlator.XServerDisplayActivity;
import com.winlator.widget.XServerView;
import com.winlator.renderer.ViewTransformation;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

/**
 * TPDP pocket-handheld layout, owned by Charoite Core.
 *
 * Visual controls match the user's sketch: game above, Select/Start below,
 * shoulder L/R below those, D-pad bottom-left and ABXY bottom-right.
 * Inputs send the game's ORIGINAL keyboard bindings, not XInput buttons.
 * No Wine mappings, graphics, installed data, or saves are modified.
 */
public final class CharoiteTpdpTouchControls {
    @FunctionalInterface
    public interface KeySink { void send(int androidKeyCode, boolean pressed); }

    private CharoiteTpdpTouchControls() {}

    private static int dp(Activity activity, float value) {
        return Math.round(activity.getResources().getDisplayMetrics().density * value);
    }

    private static GradientDrawable background(boolean secondary) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(secondary ? 0xD122293F : 0xD12B2247);
        drawable.setStroke(dpStroke(), secondary ? 0xB099B6CC : 0xB0D7CEFA);
        drawable.setCornerRadius(20);
        return drawable;
    }

    private static int dpStroke() { return 2; }

    private static Button button(Activity host, String title, String mapping,
                                 int keyCode, boolean secondary, KeySink sink) {
        Button button = new Button(host);
        button.setText(title);
        button.setAllCaps(false);
        button.setTextSize(secondary ? 12f : 18f);
        button.setTypeface(null, Typeface.BOLD);
        button.setTextColor(Color.WHITE);
        button.setGravity(Gravity.CENTER);
        button.setPadding(0, 0, 0, 0);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setMinHeight(0);
        button.setMinimumHeight(0);
        GradientDrawable drawable = background(secondary);
        // Traditional A/B/X/Y gamepad buttons are round in the sketch.
        if (!secondary && title.length() == 1 &&
                "ABXY".contains(title)) drawable.setShape(GradientDrawable.OVAL);
        button.setBackground(drawable);
        button.setContentDescription(title + ", keyboard " + mapping);
        if (keyCode >= 0) {
            button.setOnTouchListener((view, event) -> {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        view.setAlpha(0.7f);
                        sink.send(keyCode, true);
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        // A held touch dragged away must release its key.
                        float x = event.getX();
                        float y = event.getY();
                        boolean inside = x >= 0 && y >= 0 &&
                                x < view.getWidth() && y < view.getHeight();
                        view.setAlpha(inside ? 0.7f : 1f);
                        sink.send(keyCode, inside);
                        return true;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        view.setAlpha(1f);
                        sink.send(keyCode, false);
                        return true;
                    default:
                        return true;
                }
            });
        }
        return button;
    }

    private static void position(Button button, int x, int y, int width, int height) {
        FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                width, height, Gravity.TOP | Gravity.LEFT);
        params.leftMargin = Math.max(0, x);
        params.topMargin = Math.max(0, y);
        button.setLayoutParams(params);
    }

    private static int clamp(int n, int minimum, int maximum) {
        return Math.max(minimum, Math.min(n, maximum));
    }

    /**
     * A single bezel around the actual compositor-scaled TPDP client.
     * Unlike Wine's title/border, these coordinates share the renderer's
     * viewport and therefore cannot drift away from the game surface.
     * Drawing only the outline preserves full touch input to the game.
     */
    private static final class ScreenOutline extends View {
        private final XServerView xServerView;
        private final Paint shadow = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint rim = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF bounds = new RectF();

        ScreenOutline(Activity host, XServerView server) {
            super(host);
            xServerView = server;
            setClickable(false);
            setFocusable(false);
            shadow.setColor(0xCC171B2D);
            shadow.setStyle(Paint.Style.STROKE);
            shadow.setStrokeWidth(dp(host, 12));
            rim.setColor(0xFFDADEEC);
            rim.setStyle(Paint.Style.STROKE);
            rim.setStrokeWidth(dp(host, 3));
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            int[] area = CharoiteWindowPolicy.handheldScreenBounds();
            if (area == null || xServerView == null) return;
            ViewTransformation view = xServerView.getRenderer().viewTransformation;
            if (view.aspect <= 0) return;
            float left = xServerView.getLeft() + view.viewOffsetX + area[0] * view.aspect;
            float top = xServerView.getTop() + view.viewOffsetY + area[1] * view.aspect;
            float right = left + area[2] * view.aspect;
            float bottom = top + area[3] * view.aspect;
            bounds.set(left - dp((Activity)getContext(), 3),
                    top - dp((Activity)getContext(), 3),
                    right + dp((Activity)getContext(), 3),
                    bottom + dp((Activity)getContext(), 3));
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 5),
                    dp((Activity)getContext(), 5), shadow);
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 5),
                    dp((Activity)getContext(), 5), rim);
        }
    }

    /** The XServer display remains visible and touchable between controls. */
    public static void attach(Activity host, FrameLayout root, KeySink sink) {
        if (host instanceof XServerDisplayActivity) {
            XServerView display = ((XServerDisplayActivity)host).getXServerView();
            if (display != null) {
                ScreenOutline outline = new ScreenOutline(host, display);
                root.addView(outline, new FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT));
                CharoiteWindowPolicy.setHandheldOutline(outline);
            }
        }
        final Set<Integer> held = new HashSet<>();
        final KeySink guarded = (code, pressed) -> {
            // Deduplicate repeated ACTION_MOVE updates and release on focus loss.
            if (pressed ? held.add(code) : held.remove(code)) sink.send(code, pressed);
        };
        final Runnable releaseAll = () -> {
            for (Integer code : new ArrayList<>(held)) guarded.send(code, false);
        };
        root.getViewTreeObserver().addOnWindowFocusChangeListener(hasFocus -> {
            if (!hasFocus) releaseAll.run();
        });

        // Gamepad mapping: A=Z, B=X, X=C, Y=S, L=A, R=D,
        // Select=Shift, Start=Space. Arrow keys implement the D-pad.
        final Button select = button(host, "Select", "Left Shift",
                KeyEvent.KEYCODE_SHIFT_LEFT, true, guarded);
        final Button start = button(host, "Start", "Space",
                KeyEvent.KEYCODE_SPACE, true, guarded);
        final Button leftShoulder = button(host, "L", "A",
                KeyEvent.KEYCODE_A, true, guarded);
        final Button rightShoulder = button(host, "R", "D",
                KeyEvent.KEYCODE_D, true, guarded);

        final Button up = button(host, "↑", "Up arrow",
                KeyEvent.KEYCODE_DPAD_UP, false, guarded);
        final Button left = button(host, "←", "Left arrow",
                KeyEvent.KEYCODE_DPAD_LEFT, false, guarded);
        final Button right = button(host, "→", "Right arrow",
                KeyEvent.KEYCODE_DPAD_RIGHT, false, guarded);
        final Button down = button(host, "↓", "Down arrow",
                KeyEvent.KEYCODE_DPAD_DOWN, false, guarded);

        final Button yButton = button(host, "Y", "S",
                KeyEvent.KEYCODE_S, false, guarded);
        final Button xButton = button(host, "X", "C",
                KeyEvent.KEYCODE_C, false, guarded);
        final Button aButton = button(host, "A", "Z",
                KeyEvent.KEYCODE_Z, false, guarded);
        final Button bButton = button(host, "B", "X",
                KeyEvent.KEYCODE_X, false, guarded);

        final Button[] main = {
                select, start, leftShoulder, rightShoulder,
                up, left, right, down, yButton, xButton, aButton, bButton
        };
        for (Button button : main) root.addView(button);

        // Keep F11/Enter/Esc/screenshot P available without cluttering
        // the handheld layout. These are secondary, initially hidden.
        final Button f11 = button(host, "F11 Full", "F11",
                KeyEvent.KEYCODE_F11, true, guarded);
        final Button enter = button(host, "Enter", "Enter",
                KeyEvent.KEYCODE_ENTER, true, guarded);
        final Button esc = button(host, "Esc", "Escape",
                KeyEvent.KEYCODE_ESCAPE, true, guarded);
        final Button screenshot = button(host, "P Shot", "P",
                KeyEvent.KEYCODE_P, true, guarded);
        final Button[] extras = {f11, enter, esc, screenshot};
        for (Button button : extras) {
            root.addView(button);
            button.setVisibility(View.GONE);
        }

        final Button more = button(host, "MORE", "Extra keyboard controls",
                -1, true, guarded);
        final Button toggle = button(host, "HIDE KEYS", "Hide handheld controls",
                -1, true, guarded);
        root.addView(more);
        root.addView(toggle);

        // Recalculate the layout on rotation, DeX size changes or cutouts.
        // Pixel positions are computed from the actual Android root view,
        // never from an assumed Galaxy screen size.
        final Runnable relayout = () -> {
            final int width = root.getWidth(), height = root.getHeight();
            if (width <= 0 || height <= 0) return;
            boolean portrait = height >= width;
            final int margin = dp(host, 9);
            final int gap = dp(host, 5);
            final int size = clamp((width - margin * 2 - gap * 8) / 7,
                    dp(host, 34), dp(host, portrait ? 52 : 43));
            final int clusterWidth = size * 3 + gap * 2;
            final int clusterHeight = size * 3 + gap * 2;
            final int dpadX = margin;
            final int diamondX = width - margin - clusterWidth;
            // Keep both input clusters below the game in portrait mode.
            final int clusterY = portrait ?
                    height - margin - clusterHeight :
                    height - margin - clusterHeight;
            final int topControls = portrait ?
                    Math.min((int)(height * .55f), clusterY - dp(host, 110)) :
                    Math.max(dp(host, 44), (int)(height * .53f));
            final int barHeight = dp(host, portrait ? 34 : 30);
            final int centerWidth = dp(host, portrait ? 76 : 64);
            final int centerGap = dp(host, 10);
            final int centerX = (width - 2 * centerWidth - centerGap) / 2;
            position(select, centerX, topControls, centerWidth, barHeight);
            position(start, centerX + centerWidth + centerGap,
                    topControls, centerWidth, barHeight);

            final int shoulderY = portrait ?
                    clamp(topControls + dp(host, 75),
                            topControls + barHeight + dp(host, 8),
                            clusterY - barHeight - dp(host, 12)) :
                    topControls + dp(host, 36);
            final int shoulderW = dp(host, portrait ? 88 : 65);
            position(leftShoulder, margin + dp(host, 12),
                    shoulderY, shoulderW, barHeight);
            position(rightShoulder, width - margin - dp(host, 12) - shoulderW,
                    shoulderY, shoulderW, barHeight);

            position(up, dpadX + size + gap, clusterY, size, size);
            position(left, dpadX, clusterY + size + gap, size, size);
            position(right, dpadX + (size + gap) * 2,
                    clusterY + size + gap, size, size);
            position(down, dpadX + size + gap,
                    clusterY + (size + gap) * 2, size, size);

            position(yButton, diamondX + size + gap, clusterY, size, size);
            position(xButton, diamondX, clusterY + size + gap, size, size);
            position(aButton, diamondX + (size + gap) * 2,
                    clusterY + size + gap, size, size);
            position(bButton, diamondX + size + gap,
                    clusterY + (size + gap) * 2, size, size);

            int topButtonH = dp(host, 32);
            position(more, margin, margin, dp(host, 68), topButtonH);
            position(toggle, width - margin - dp(host, 93),
                    margin, dp(host, 93), topButtonH);

            int extraW = Math.min(dp(host, 76),
                    (width - margin * 2 - gap * 3) / 4);
            int extrasWidth = extraW * 4 + gap * 3;
            int extraX = (width - extrasWidth) / 2;
            int extraY = portrait ? topControls - dp(host, 53) :
                    margin + topButtonH + gap;
            for (int i = 0; i < extras.length; i++)
                position(extras[i], extraX + i * (extraW + gap),
                        extraY, extraW, dp(host, 34));
        };
        root.addOnLayoutChangeListener((v, l, t, r, b, oldL, oldT, oldR, oldB) -> {
            if (r - l != oldR - oldL || b - t != oldB - oldT) relayout.run();
        });
        root.post(relayout);

        more.setOnClickListener(v -> {
            boolean show = extras[0].getVisibility() != View.VISIBLE;
            if (!show) releaseAll.run();
            for (Button button : extras)
                button.setVisibility(show ? View.VISIBLE : View.GONE);
            more.setText(show ? "LESS" : "MORE");
        });
        toggle.setOnClickListener(v -> {
            boolean show = select.getVisibility() != View.VISIBLE;
            if (!show) releaseAll.run();
            for (Button button : main)
                button.setVisibility(show ? View.VISIBLE : View.GONE);
            for (Button button : extras) button.setVisibility(View.GONE);
            more.setVisibility(show ? View.VISIBLE : View.GONE);
            more.setText("MORE");
            toggle.setText(show ? "HIDE KEYS" : "SHOW KEYS");
        });
    }
}
