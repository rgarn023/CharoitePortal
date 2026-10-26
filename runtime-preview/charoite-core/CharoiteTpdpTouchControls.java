package com.charoitegames.core;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.LinearGradient;
import android.graphics.Shader;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;
import com.winlator.XServerDisplayActivity;
import com.winlator.widget.XServerView;
import com.winlator.renderer.ViewTransformation;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * Shared pocket-handheld layout for Charoite Core game sessions.
 *
 * Visual controls match the user's sketch: game above, Select/Start below,
 * shoulder L/Keyboard/R below those, D-pad bottom-left and ABXY bottom-right.
 * Esc/Select/Start/Enter share a row; an always-visible Portal button
 * requests a confirmed exit via the host\u0027s normal session teardown.
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
        // Smoked translucent purple plastic, not solid black/grey buttons.
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR, secondary
                ? new int[]{0xE3523777, 0xE1271A43}
                : new int[]{0xE0553489, 0xE12A174B});
        drawable.setStroke(dpStroke(), secondary ? 0xB6BFA9E9 : 0xB8D6B8FF);
        drawable.setCornerRadius(18);
        return drawable;
    }

    private static GradientDrawable clusterPlate() {
        GradientDrawable plate = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{0x694F3677, 0x88402A62});
        plate.setStroke(2, 0x8DAE98D4);
        plate.setCornerRadius(28);
        return plate;
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
            // Track this button independently. Two buttons may map to Shift,
            // and repeated ACTION_MOVE events must never count as new presses.
            final boolean[] down = {false};
            button.setOnTouchListener((view, event) -> {
                boolean pressed;
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        pressed = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        float x = event.getX();
                        float y = event.getY();
                        pressed = x >= 0 && y >= 0 &&
                                x < view.getWidth() && y < view.getHeight();
                        break;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        pressed = false;
                        break;
                    default:
                        return true;
                }
                view.setAlpha(pressed ? 0.7f : 1f);
                if (down[0] != pressed) {
                    down[0] = pressed;
                    sink.send(keyCode, pressed);
                }
                return true;
            });
        }
        return button;
    }

    private static void position(View button, int x, int y, int width, int height) {
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
        private final Paint shell = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF bounds = new RectF();

        ScreenOutline(Activity host, XServerView server) {
            super(host);
            xServerView = server;
            setClickable(false);
            setFocusable(false);
            shadow.setColor(0xD01B102C);
            shadow.setStyle(Paint.Style.STROKE);
            shadow.setStrokeWidth(dp(host, 12));
            rim.setColor(0xFFCBB4F2);
            rim.setStyle(Paint.Style.STROKE);
            rim.setStrokeWidth(dp(host, 3));
        }

        /** The opaque white rectangle is Wine's 4:3 desktop background.
         * Draw Charoite's translucent shell OUTSIDE the game client only.
         * Never recolor or obscure the real game pixels or its touch target.
         */
        private void drawShell(Canvas canvas, RectF screen) {
            float w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0) return;
            shell.setShader(new LinearGradient(0, 0, w * .85f, h,
                    new int[]{0xF0271643, 0xE84D3074, 0xF01A102E},
                    null, Shader.TileMode.CLAMP));
            if (screen == null) {
                canvas.drawRect(0, 0, w, h, shell);
            } else {
                float top = Math.max(0, Math.min(h, screen.top));
                float bottom = Math.max(top, Math.min(h, screen.bottom));
                float left = Math.max(0, Math.min(w, screen.left));
                float right = Math.max(left, Math.min(w, screen.right));
                canvas.drawRect(0, 0, w, top, shell);
                canvas.drawRect(0, bottom, w, h, shell);
                canvas.drawRect(0, top, left, bottom, shell);
                canvas.drawRect(right, top, w, bottom, shell);
            }
            shell.setShader(null);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            int[] area = CharoiteWindowPolicy.handheldScreenBounds();
            if (area == null || xServerView == null) {
                drawShell(canvas, null);
                return;
            }
            ViewTransformation view = xServerView.getRenderer().viewTransformation;
            if (view.aspect <= 0) {
                drawShell(canvas, null);
                return;
            }
            float left = xServerView.getLeft() + view.viewOffsetX + area[0] * view.aspect;
            // GL viewport Y uses a bottom origin; Canvas coordinates are
            // top-down. Convert using the complete projected guest scene so
            // the bezel aligns after either phone rotation direction.
            float projectedTop = xServerView.getHeight() -
                    view.viewOffsetY - view.viewHeight;
            float top = xServerView.getTop() + projectedTop +
                    area[1] * view.aspect;
            float right = left + area[2] * view.aspect;
            float bottom = top + area[3] * view.aspect;
            bounds.set(left - dp((Activity)getContext(), 3),
                    top - dp((Activity)getContext(), 3),
                    right + dp((Activity)getContext(), 3),
                    bottom + dp((Activity)getContext(), 3));
            drawShell(canvas, bounds);
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 5),
                    dp((Activity)getContext(), 5), shadow);
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 5),
                    dp((Activity)getContext(), 5), rim);
        }
    }

    /** The XServer display remains visible and touchable between controls. */
    public static void attach(Activity host, FrameLayout root, KeySink sink,
                              Runnable returnToPortal, boolean tpdpMapping,
                              String executable) {
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
        final Map<Integer, Integer> held = new HashMap<>();
        final KeySink guarded = (code, pressed) -> {
            // Reference-count simultaneous buttons mapped to the same X key.
            // Releasing Shoot must not release Focus; releasing one of two
            // mapped Shift buttons must not release the other one's Shift.
            int count = held.containsKey(code) ? held.get(code) : 0;
            if (pressed) {
                held.put(code, count + 1);
                if (count == 0) sink.send(code, true);
            } else if (count > 0) {
                if (count == 1) {
                    held.remove(code);
                    sink.send(code, false);
                } else held.put(code, count - 1);
            }
        };
        final Runnable releaseAll = () -> {
            for (Integer code : new ArrayList<>(held.keySet())) sink.send(code, false);
            held.clear();
        };
        final java.util.function.IntUnaryOperator mapped = index ->
                CharoiteGameControlProfiles.keyFor(host, executable, index);
        final java.util.function.IntFunction<String> binding = index ->
                CharoiteGameControlProfiles.label(mapped.applyAsInt(index));
        root.getViewTreeObserver().addOnWindowFocusChangeListener(hasFocus -> {
            if (!hasFocus) releaseAll.run();
        });

        // All games get the same buttons, with Core-selected (and optionally
        // user-overridden) keyboard keys for their individual executable.
        final Button esc = button(host, "Esc", binding.apply(0),
                mapped.applyAsInt(0), true, guarded);
        final Button select = button(host, "Select", binding.apply(1),
                mapped.applyAsInt(1), true, guarded);
        final Button start = button(host, "Start", binding.apply(2),
                mapped.applyAsInt(2), true, guarded);
        final Button enter = button(host, "Enter", binding.apply(3),
                mapped.applyAsInt(3), true, guarded);
        final Button leftShoulder = button(host, "L", binding.apply(4),
                mapped.applyAsInt(4), true, guarded);
        final Button rightShoulder = button(host, "R", binding.apply(5),
                mapped.applyAsInt(5), true, guarded);
        final Button up = button(host, "↑", binding.apply(6),
                mapped.applyAsInt(6), false, guarded);
        final Button left = button(host, "←", binding.apply(7),
                mapped.applyAsInt(7), false, guarded);
        final Button right = button(host, "→", binding.apply(8),
                mapped.applyAsInt(8), false, guarded);
        final Button down = button(host, "↓", binding.apply(9),
                mapped.applyAsInt(9), false, guarded);
        final Button yButton = button(host, "Y", binding.apply(10),
                mapped.applyAsInt(10), false, guarded);
        final Button xButton = button(host, "X", binding.apply(11),
                mapped.applyAsInt(11), false, guarded);
        final Button aButton = button(host, "A", binding.apply(12),
                mapped.applyAsInt(12), false, guarded);
        final Button bButton = button(host, "B", binding.apply(13),
                mapped.applyAsInt(13), false, guarded);

        final Button[] main = {
                esc, select, start, enter, leftShoulder, rightShoulder,
                up, left, right, down, yButton, xButton, aButton, bButton
        };
        for (Button button : main) root.addView(button);

        // Only the infrequent F11 and screenshot keys remain under More.
        final Button f11 = button(host, "F11 Full", "F11",
                KeyEvent.KEYCODE_F11, true, guarded);
        final Button screenshot = button(host, "P Shot", "P",
                KeyEvent.KEYCODE_P, true, guarded);
        final Button[] extras = {f11, screenshot};
        for (Button button : extras) {
            root.addView(button);
            button.setVisibility(View.GONE);
        }

        // A separate, always-visible route back to Portal.
        final Button portal = button(host, "PORTAL", "Exit game to Charoite Portal",
                -1, true, guarded);
        final Button more = button(host, "MORE", "Extra keyboard controls",
                -1, true, guarded);
        // The keyboard belongs to the handheld controls and follows Hide/Show Keys.
        // Uses Android's system IME; visually positioned between L and R.
        final Button keyboard = button(host, "KEYBOARD", "Open system keyboard",
                -1, true, guarded);
        final Button toggle = button(host, "HIDE KEYS", "Hide handheld controls",
                -1, true, guarded);
        root.addView(portal);
        root.addView(more);
        root.addView(keyboard);
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
            // Four compact buttons in one row directly below the game.
            final int centerGap = dp(host, 6);
            final int centerWidth = Math.min(dp(host, portrait ? 76 : 64),
                    Math.max(dp(host, 36), (width - margin * 2 - 3 * centerGap) / 4));
            final int centerX = (width - 4 * centerWidth - 3 * centerGap) / 2;
            position(esc, centerX, topControls, centerWidth, barHeight);
            position(select, centerX + centerWidth + centerGap,
                    topControls, centerWidth, barHeight);
            position(start, centerX + 2 * (centerWidth + centerGap),
                    topControls, centerWidth, barHeight);
            position(enter, centerX + 3 * (centerWidth + centerGap),
                    topControls, centerWidth, barHeight);

            final int shoulderY = portrait ?
                    clamp(topControls + dp(host, 75),
                            topControls + barHeight + dp(host, 8),
                            clusterY - barHeight - dp(host, 12)) :
                    topControls + dp(host, 36);
            final int shoulderInset = margin + dp(host, 12);
            // Reserve space for the centered keyboard even in a narrower
            // multi-window view. Keep the game image and D-pad positions fixed.
            final int shoulderW = Math.min(dp(host, portrait ? 88 : 65),
                    Math.max(dp(host, 36), (width - 2 * shoulderInset -
                            dp(host, 60) - 2 * gap) / 2));
            final int leftShoulderX = shoulderInset;
            final int rightShoulderX = width - shoulderInset - shoulderW;
            position(leftShoulder, leftShoulderX,
                    shoulderY, shoulderW, barHeight);
            position(rightShoulder, rightShoulderX,
                    shoulderY, shoulderW, barHeight);
            final int keyboardSpace = Math.max(0,
                    rightShoulderX - leftShoulderX - shoulderW - 2 * gap);
            final int keyboardW = Math.min(dp(host, 100), keyboardSpace);
            keyboard.setText(keyboardW < dp(host, 78) ? "⌨" : "KEYBOARD");
            position(keyboard, (width - keyboardW) / 2,
                    shoulderY, keyboardW, barHeight);

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
            final int portalW = dp(host, 88);
            position(portal, margin, margin, portalW, topButtonH);
            position(more, margin + portalW + gap, margin,
                    dp(host, 68), topButtonH);
            position(toggle, width - margin - dp(host, 93),
                    margin, dp(host, 93), topButtonH);

            int extraW = Math.min(dp(host, 76),
                    (width - margin * 2 - gap * (extras.length - 1))
                            / extras.length);
            int extrasWidth = extraW * extras.length + gap * (extras.length - 1);
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

        // Return remains available even while handheld keys are hidden.
        portal.setOnClickListener(v -> {
            releaseAll.run();
            if (returnToPortal != null) returnToPortal.run();
        });
        keyboard.setOnClickListener(v -> {
            releaseAll.run();
            CharoiteSoftKeyboard.show(host);
        });
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
            keyboard.setVisibility(show ? View.VISIBLE : View.GONE);
            for (Button button : extras) button.setVisibility(View.GONE);
            more.setVisibility(show ? View.VISIBLE : View.GONE);
            more.setText("MORE");
            toggle.setText(show ? "HIDE KEYS" : "SHOW KEYS");
        });
    }
}
