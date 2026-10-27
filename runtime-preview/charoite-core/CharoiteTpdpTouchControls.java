package com.charoitegames.core;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Canvas;
import android.graphics.Path;
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
                ? new int[]{0xA85E4089, 0x99301C51}
                : new int[]{0xA65B3792, 0x92301A56});
        drawable.setStroke(dpStroke(), secondary ? 0xB6BFA9E9 : 0xB8D6B8FF);
        drawable.setCornerRadius(18);
        return drawable;
    }

    private static GradientDrawable clusterPlate() {
        GradientDrawable plate = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{0x484F3677, 0x60402A62});
        plate.setStroke(2, 0x8DAE98D4);
        plate.setCornerRadius(28);
        return plate;
    }

    private static int dpStroke() { return 2; }

    /**
     * A single vector arrow rotated into four directions. Unicode arrow
     * glyphs have inconsistent font metrics (left differs from right), and
     * made the old D-pad look lopsided despite equal button dimensions.
     */
    private static final class DpadButton extends Button {
        private final int quadrant;
        private final Paint arrow = new Paint(Paint.ANTI_ALIAS_FLAG);

        DpadButton(Activity context, int quadrant) {
            super(context);
            this.quadrant = quadrant;
            setText("");
            setGravity(Gravity.CENTER);
            setIncludeFontPadding(false);
            arrow.setColor(0xFFEADCFD);
            arrow.setStyle(Paint.Style.STROKE);
            arrow.setStrokeWidth(dp(context, 2.7f));
            arrow.setStrokeCap(Paint.Cap.ROUND);
            arrow.setStrokeJoin(Paint.Join.ROUND);
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float cx = getWidth() * .5f;
            float cy = getHeight() * .5f;
            float unit = Math.min(getWidth(), getHeight()) * .155f;
            canvas.save();
            canvas.translate(cx, cy);
            canvas.rotate(quadrant * 90f);
            Path icon = new Path();
            // Source arrow points UP. All four share these exact vertices.
            icon.moveTo(0, -unit * 1.35f);
            icon.lineTo(-unit, -unit * .24f);
            icon.moveTo(0, -unit * 1.35f);
            icon.lineTo(unit, -unit * .24f);
            icon.moveTo(0, -unit * 1.24f);
            icon.lineTo(0, unit * 1.3f);
            canvas.drawPath(icon, arrow);
            canvas.restore();
        }
    }

    private static Button button(Activity host, String title, String mapping,
                                 int keyCode, boolean secondary, KeySink sink) {
        final int direction = "↑".equals(title) ? 0 :
                "→".equals(title) ? 1 : "↓".equals(title) ? 2 :
                "←".equals(title) ? 3 : -1;
        Button button = direction >= 0 ? new DpadButton(host, direction) :
                new Button(host);
        if (direction < 0) button.setText(title);
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
     * Current physical game rectangle in the overlay coordinate space.
     * Landscape controls use its LEFT and RIGHT safe zones, rather than a
     * fixed percent which could cover the game after DeX or rotation.
     */
    private static int[] projectedGameBounds(Activity host) {
        if (!(host instanceof XServerDisplayActivity)) return null;
        XServerView display = ((XServerDisplayActivity)host).getXServerView();
        int[] game = CharoiteWindowPolicy.handheldScreenBounds();
        if (display == null || game == null || game.length < 4) return null;
        ViewTransformation view = display.getRenderer().viewTransformation;
        if (view == null || view.aspect <= 0f) return null;
        int x = Math.round(display.getLeft() + view.viewOffsetX +
                game[0] * view.aspect);
        float projectedTop = display.getHeight() -
                view.viewOffsetY - view.viewHeight;
        int y = Math.round(display.getTop() + projectedTop +
                game[1] * view.aspect);
        return new int[]{x, y, Math.round(game[2] * view.aspect),
                Math.round(game[3] * view.aspect)};
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
        private final Paint matte = new Paint(Paint.ANTI_ALIAS_FLAG);
        private Button[] dpadHardware;
        private Button[] faceHardware;

        void setHardwareButtons(Button[] dpad, Button[] face) {
            dpadHardware = dpad;
            faceHardware = face;
            invalidate();
        }

        ScreenOutline(Activity host, XServerView server) {
            super(host);
            xServerView = server;
            setClickable(false);
            setFocusable(false);
            shadow.setColor(0xD01B102C);
            shadow.setStyle(Paint.Style.STROKE);
            shadow.setStrokeWidth(dp(host, 8));
            rim.setColor(0xFFCBB4F2);
            rim.setStyle(Paint.Style.STROKE);
            rim.setStrokeWidth(dp(host, 2));
        }


        /**
         * Controller contacts are placed at the exact Android button bounds,
         * not fractions of the phone screen. They remain aligned when the
         * handset rotates, DeX resizes, or Android changes screen density.
         * This is the inside of an original handheld controller, not a
         * claimed Samsung phone teardown.
         */
        private void drawControllerInternals(Canvas canvas, float w, float h) {
            if (dpadHardware == null || faceHardware == null) return;
            final float chipX = w * .50f;
            final float chipY = h * .89f;
            Paint board = new Paint(Paint.ANTI_ALIAS_FLAG);
            board.setStyle(Paint.Style.STROKE);
            board.setStrokeWidth(dp((Activity)getContext(), 1.2f));
            board.setColor(0x855AABAC);

            for (Button[] group : new Button[][]{dpadHardware, faceHardware}) {
                boolean circular = group == faceHardware;
                for (Button button : group) {
                    if (button.getVisibility() != View.VISIBLE ||
                            button.getWidth() <= 0 || button.getHeight() <= 0) continue;
                    // Layout's button rectangle is the sole geometry source.
                    float left = button.getLeft(), top = button.getTop();
                    float right = button.getRight(), bottom = button.getBottom();
                    float cx = (left + right) * .5f, cy = (top + bottom) * .5f;
                    float inset = dp((Activity)getContext(), 1f);
                    RectF switchOutline = new RectF(left + inset, top + inset,
                            right - inset, bottom - inset);
                    if (circular) {
                        canvas.drawOval(switchOutline, board);
                    } else {
                        float corner = dp((Activity)getContext(), 7f);
                        canvas.drawRoundRect(switchOutline, corner, corner, board);
                    }
                    Path trace = new Path();
                    trace.moveTo(cx, cy);
                    trace.lineTo(cx, chipY - dp((Activity)getContext(), 21f));
                    trace.lineTo(chipX, chipY - dp((Activity)getContext(), 21f));
                    canvas.drawPath(trace, board);
                }
            }
            // Central PCB controller under the clear-purple casing.
            board.setStyle(Paint.Style.FILL);
            board.setColor(0xBD263F50);
            float halfW = dp((Activity)getContext(), 22);
            float halfH = dp((Activity)getContext(), 16);
            RectF chip = new RectF(chipX-halfW, chipY-halfH, chipX+halfW, chipY+halfH);
            canvas.drawRoundRect(chip, dp((Activity)getContext(), 4),
                    dp((Activity)getContext(), 4), board);
            board.setStyle(Paint.Style.STROKE);
            board.setColor(0xB55CBAB1);
            canvas.drawRoundRect(chip, dp((Activity)getContext(), 4),
                    dp((Activity)getContext(), 4), board);
        }

        /** Mask the white Wine desktop, then show phone-like circuitry under
         * a truly translucent purple acrylic coating. Clip OUT the game
         * rectangle, so game pixels remain fully visible and untouched.
         */
        private void drawShell(Canvas canvas, RectF screen) {
            float w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0) return;
            canvas.save();
            if (screen != null) canvas.clipOutRect(
                    screen.left, screen.top, screen.right, screen.bottom);
            shell.setShader(null);
            // An opaque dark undercoat hides the white Wine desktop while
            // translucent clear-purple layers reveal internal PCB contacts.
            // Alpha-only tint over a white X11 desktop looked pastel/white.
            shell.setColor(0xFF20122F);
            canvas.drawRect(0, 0, w, h, shell);
            drawControllerInternals(canvas, w, h);
            // A device-matched real interior photo is displayed only when
            // available; never show an invented diagram as exact hardware.
            CharoiteHardwareSkin.drawInterior(canvas, (Activity)getContext(), w, h);
            shell.setShader(new LinearGradient(0, 0, w * .85f, h,
                    new int[]{0x805F3D93, 0x503F2466, 0x894C2877},
                    null, Shader.TileMode.CLAMP));
            canvas.drawRect(0, 0, w, h, shell);
            shell.setShader(null);
            // Polished clear-plastic sheen and a subtle edge highlight.
            shell.setColor(0x50DBC8FD);
            shell.setStyle(Paint.Style.STROKE);
            shell.setStrokeWidth(dp((Activity)getContext(), 2));
            canvas.drawRoundRect(new RectF(4, 4, w - 4, h - 4),
                    dp((Activity)getContext(), 18),
                    dp((Activity)getContext(), 18), shell);
            shell.setStyle(Paint.Style.FILL);
            canvas.restore();
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            int[] area = CharoiteWindowPolicy.handheldScreenBounds();
            // Some Windows games never expose a compositor-tracked game
            // rectangle. Leave those windows visible rather than tinting
            // the entire Wine desktop on top of the actual game.
            if (area == null || xServerView == null) return;
            ViewTransformation view = xServerView.getRenderer().viewTransformation;
            if (view.aspect <= 0) return;
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
            // The X11 client rectangle contains ONLY game pixels. The
            // decorated parent exposes a white backing below the client.
            // Mask all the parent/letterbox pixels, not the actual client.
            RectF gamePixels = new RectF(left, top, right, bottom);
            bounds.set(left - dp((Activity)getContext(), 12),
                    top - dp((Activity)getContext(), 12),
                    right + dp((Activity)getContext(), 12),
                    bottom + dp((Activity)getContext(), 22));
            drawShell(canvas, gamePixels);
            canvas.save();
            canvas.clipRect(bounds);
            canvas.clipOutRect(gamePixels);
            matte.setColor(0xFF0C0917);
            matte.setStyle(Paint.Style.FILL);
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 6),
                    dp((Activity)getContext(), 6), matte);
            canvas.restore();
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 6),
                    dp((Activity)getContext(), 6), shadow);
            canvas.drawRoundRect(bounds, dp((Activity)getContext(), 6),
                    dp((Activity)getContext(), 6), rim);
        }
    }

    /** The XServer display remains visible and touchable between controls. */
    public static void attach(Activity host, FrameLayout root, KeySink sink,
                              Runnable returnToPortal, boolean tpdpMapping,
                              String executable) {
        ScreenOutline outline = null;
        if (host instanceof XServerDisplayActivity) {
            XServerView display = ((XServerDisplayActivity)host).getXServerView();
            if (display != null) {
                outline = new ScreenOutline(host, display);
                root.addView(outline, new FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT));
                CharoiteWindowPolicy.setHandheldOutline(outline);
            }
        }
        final boolean touhou8 = CharoiteLegacyKeyboard.requiresWindowsKeyboard(executable);
        if (touhou8) {
            CharoiteLegacyKeyboard.resetMode();
            if (host instanceof XServerDisplayActivity)
                CharoiteLegacyKeyboard.prepareScanBridge(host,
                        ((XServerDisplayActivity)host).getXServer());
        }
        final Map<Integer, Integer> held = new HashMap<>();
        // Short clicks from Android can be shorter than the next DirectInput
        // frame. Touhou 8 must see an actual held-down state for >= 100ms.
        final android.os.Handler keyTimer = new android.os.Handler(
                android.os.Looper.getMainLooper());
        final Map<Integer, Long> keyDownAt = new HashMap<>();
        final Map<Integer, Runnable> pendingKeyUp = new HashMap<>();
        final KeySink guarded = (code, pressed) -> {
            // Reference-count simultaneous buttons mapped to the same X key.
            // Releasing Shoot must not release Focus; releasing one of two
            // mapped Shift buttons must not release the other one's Shift.
            if (touhou8) android.util.Log.d("CharoiteInput",
                    CharoiteGameControlProfiles.label(code) +
                    (pressed ? " pressed" : " released"));
            int count = held.containsKey(code) ? held.get(code) : 0;
            if (pressed) {
                Runnable pending = pendingKeyUp.remove(code);
                if (pending != null) keyTimer.removeCallbacks(pending);
                held.put(code, count + 1);
                if (count == 0 && pending == null) {
                    keyDownAt.put(code, android.os.SystemClock.uptimeMillis());
                    sink.send(code, true);
                }
            } else if (count > 0) {
                if (count == 1) {
                    held.remove(code);
                    if (!touhou8) {
                        sink.send(code, false);
                    } else {
                        long started = keyDownAt.containsKey(code) ? keyDownAt.get(code) : 0;
                        long elapsed = android.os.SystemClock.uptimeMillis() - started;
                        Runnable release = () -> {
                            pendingKeyUp.remove(code);
                            keyDownAt.remove(code);
                            sink.send(code, false);
                        };
                        pendingKeyUp.put(code, release);
                        keyTimer.postDelayed(release, Math.max(0, 110 - elapsed));
                    }
                } else held.put(code, count - 1);
            }
        };
        final Runnable releaseAll = () -> {
            for (Runnable callback : new ArrayList<>(pendingKeyUp.values()))
                keyTimer.removeCallbacks(callback);
            for (Integer code : new ArrayList<>(pendingKeyUp.keySet()))
                sink.send(code, false);
            pendingKeyUp.clear();
            for (Integer code : new ArrayList<>(held.keySet())) sink.send(code, false);
            held.clear();
            keyDownAt.clear();
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

        if (outline != null) {
            outline.setHardwareButtons(new Button[]{up, left, right, down},
                    new Button[]{yButton, xButton, aButton, bButton});
        }

        final Button[] main = {
                esc, select, start, enter, leftShoulder, rightShoulder,
                up, left, right, down, yButton, xButton, aButton, bButton
        };
        // Acrylic purple plates are behind the actual touch buttons, and
        // never intercept presses on the underlying game window.
        final View dpadPlate = new View(host);
        dpadPlate.setBackground(clusterPlate());
        dpadPlate.setClickable(false);
        final View facePlate = new View(host);
        facePlate.setBackground(clusterPlate());
        facePlate.setClickable(false);
        root.addView(dpadPlate);
        root.addView(facePlate);
        for (Button button : main) root.addView(button);

        // Only the infrequent F11 and screenshot keys remain under More.
        final Button f11 = button(host, "F11 Full", "F11",
                KeyEvent.KEYCODE_F11, true, guarded);
        final Button screenshot = button(host, "P Shot", "P",
                KeyEvent.KEYCODE_P, true, guarded);
        final Button backend = touhou8 ? button(host, "INPUT: SCAN",
                "Select Touhou 8 keyboard backend: scan-code, window, dual, Win32 or X11",
                -1, true, guarded) : null;
        final Button diagnostics = touhou8 ? button(host, "INPUT INFO",
                "Show Touhou 8 keyboard backend and focus status",
                -1, true, guarded) : null;
        final Button interior = button(host, "INTERIOR",
                "Choose an authentic photo of this device's internal components",
                -1, true, guarded);
        final Button[] extras = touhou8 ?
                new Button[]{f11, screenshot, backend, diagnostics, interior} :
                new Button[]{f11, screenshot, interior};
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
            // All four direction buttons use precisely the same square
            // dimensions; every center lies on one symmetric cross.
            final int clusterY = height - margin - clusterHeight;
            final int dpadCenterX = dpadX + size + gap;
            final int dpadCenterY = clusterY + size + gap;
            position(dpadPlate, dpadX - dp(host, 3),
                    clusterY - dp(host, 3),
                    clusterWidth + dp(host, 6), clusterHeight + dp(host, 6));
            position(facePlate, diamondX - dp(host, 3),
                    clusterY - dp(host, 3),
                    clusterWidth + dp(host, 6), clusterHeight + dp(host, 6));
            if (portrait) {
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

            position(up, dpadCenterX, dpadCenterY - size - gap, size, size);
            position(left, dpadCenterX - size - gap, dpadCenterY, size, size);
            position(right, dpadCenterX + size + gap, dpadCenterY, size, size);
            position(down, dpadCenterX, dpadCenterY + size + gap, size, size);

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
            } else {
                // In landscape the upper *center* is the game surface.
                // Never place action keys, More buttons or keyboard on it.
                // On a phone/DeX resize, derive side columns from the live
                // compositor game quad; use centered fallback at startup.
                int[] game = projectedGameBounds(host);
                final int screenGap = dp(host, 12);
                final int gameLeft = game != null ?
                        game[0] - screenGap : Math.round(width * .27f);
                final int gameRight = game != null ?
                        game[0] + game[2] + screenGap : Math.round(width * .73f);
                final int leftX = margin;
                final int leftSideW = Math.max(0, gameLeft - margin * 2);
                final int rightX = Math.max(width / 2, gameRight + margin);
                final int rightSideW = Math.max(0, width - rightX - margin);
                final int leftPairW = Math.max(1, (leftSideW - gap) / 2);
                final int rightPairW = Math.max(1, (rightSideW - gap) / 2);
                final int landBarH = dp(host, 29);
                final int topButtonH = dp(host, 32);
                // Portal/More/Hide are the only buttons on the top header.
                final int portalW = dp(host, 88);
                position(portal, margin, margin, portalW, topButtonH);
                position(more, margin + portalW + gap, margin,
                        dp(host, 68), topButtonH);
                position(toggle, width - margin - dp(host, 93),
                        margin, dp(host, 93), topButtonH);

                // More expands into the LEFT/RIGHT gutters (not the game).
                final int menuY = margin + topButtonH + dp(host, 7);
                position(f11, leftX, menuY, leftPairW, landBarH);
                position(screenshot, leftX + leftPairW + gap, menuY,
                        leftPairW, landBarH);
                if (backend != null) position(backend, leftX,
                        menuY + landBarH + gap, leftSideW, landBarH);
                if (diagnostics != null) position(diagnostics, rightX,
                        menuY, rightPairW, landBarH);
                position(interior, rightX +
                        (diagnostics != null ? rightPairW + gap : 0),
                        menuY, diagnostics != null ? rightPairW : rightSideW,
                        landBarH);

                // Split Esc/Select and Start/Enter across both side gutters.
                // Nothing in these rows crosses the game rectangle.
                final int navY = menuY + 2 * (landBarH + gap) + gap;
                position(esc, leftX, navY, leftPairW, landBarH);
                position(select, leftX + leftPairW + gap, navY,
                        leftPairW, landBarH);
                position(start, rightX, navY, rightPairW, landBarH);
                position(enter, rightX + rightPairW + gap, navY,
                        rightPairW, landBarH);

                final int shoulderY = navY + landBarH + dp(host, 14);
                final int shoulderW = Math.min(dp(host, 88),
                        Math.max(1, leftSideW));
                final int rightShoulderW = Math.min(dp(host, 88),
                        Math.max(1, rightSideW));
                position(leftShoulder, leftX + (leftSideW - shoulderW) / 2,
                        shoulderY, shoulderW, landBarH);
                position(rightShoulder, rightX +
                        (rightSideW - rightShoulderW) / 2,
                        shoulderY, rightShoulderW, landBarH);

                // Keep the keyboard BELOW the game's visible bottom edge,
                // between the D-pad and the ABXY cluster.
                final int keyboardW = Math.min(dp(host, 104),
                        Math.max(dp(host, 44), rightX - gameLeft - 2 * gap));
                final int gameBottom = game != null ?
                        game[1] + game[3] : height - landBarH - margin * 2;
                final int keyboardY = clamp(gameBottom + dp(host, 32),
                        menuY + landBarH + gap,
                        height - landBarH - margin);
                keyboard.setText(keyboardW < dp(host, 78) ? "⌨" : "KEYBOARD");
                position(keyboard, (width - keyboardW) / 2,
                        keyboardY, keyboardW, landBarH);

                // Retain symmetric, equal-size gameplay clusters in their
                // bottom corners; moving them onto the game would break play.
                position(up, dpadCenterX, dpadCenterY - size - gap, size, size);
                position(left, dpadCenterX - size - gap, dpadCenterY, size, size);
                position(right, dpadCenterX + size + gap, dpadCenterY, size, size);
                position(down, dpadCenterX, dpadCenterY + size + gap, size, size);
                position(yButton, diamondX + size + gap, clusterY, size, size);
                position(xButton, diamondX, clusterY + size + gap, size, size);
                position(aButton, diamondX + (size + gap) * 2,
                        clusterY + size + gap, size, size);
                position(bButton, diamondX + size + gap,
                        clusterY + (size + gap) * 2, size, size);
            }
        };
        root.addOnLayoutChangeListener((v, l, t, r, b, oldL, oldT, oldR, oldB) -> {
            if (r - l != oldR - oldL || b - t != oldB - oldT) relayout.run();
        });
        root.post(relayout);
        // X11 windows can map AFTER Android lays out the overlay. Refresh
        // the gutter geometry once the game drawable and frame have appeared.
        // These are one-off reflows, not a perpetual polling loop.
        root.postDelayed(relayout, 550);
        root.postDelayed(relayout, 1800);

        // Return remains available even while handheld keys are hidden.
        portal.setOnClickListener(v -> {
            releaseAll.run();
            if (returnToPortal != null) returnToPortal.run();
        });
        keyboard.setOnClickListener(v -> {
            releaseAll.run();
            CharoiteSoftKeyboard.show(host);
        });
        if (backend != null) backend.setOnClickListener(v -> {
            releaseAll.run();
            CharoiteLegacyKeyboard.nextMode();
            backend.setText("INPUT: " + CharoiteLegacyKeyboard.modeLabel());
        });
        interior.setOnClickListener(v -> {
            releaseAll.run();
            CharoiteHardwareSkin.choosePicture(host);
        });
        if (diagnostics != null) diagnostics.setOnClickListener(v ->
                new androidx.appcompat.app.AlertDialog.Builder(host)
                        .setTitle("Touhou 8 input diagnostics")
                        .setMessage(CharoiteLegacyKeyboard.diagnosticReport(
                                host instanceof XServerDisplayActivity ?
                                ((XServerDisplayActivity)host).getXServer() : null))
                        .setPositiveButton("OK", null).show());
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
            dpadPlate.setVisibility(show ? View.VISIBLE : View.GONE);
            facePlate.setVisibility(show ? View.VISIBLE : View.GONE);
            keyboard.setVisibility(show ? View.VISIBLE : View.GONE);
            for (Button button : extras) button.setVisibility(View.GONE);
            more.setVisibility(show ? View.VISIBLE : View.GONE);
            more.setText("MORE");
            toggle.setText(show ? "HIDE KEYS" : "SHOW KEYS");
        });
    }
}
