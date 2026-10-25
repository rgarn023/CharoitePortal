package com.charoitegames.core;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

/**
 * Touch controls for TPDP's native keyboard layout; not a Windows gamepad.
 *
 * Winlator's XServer keyboard remains the source of truth for key injection.
 * Each button releases its key when touch ends, moves out, or is cancelled.
 * Separate view-level listeners permit multi-touch (e.g. X + arrow to run).
 * The visual overlay is transient and never modifies an installed game.
 */
public final class CharoiteTpdpTouchControls {
    @FunctionalInterface
    public interface KeySink { void send(int androidKeyCode, boolean pressed); }

    private CharoiteTpdpTouchControls() {}

    private static int dp(Activity host, int value) {
        return Math.round(host.getResources().getDisplayMetrics().density * value);
    }

    private static GradientDrawable background(int fill, int stroke) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setStroke(2, stroke);
        drawable.setCornerRadius(17);
        return drawable;
    }

    private static Button key(Activity host, String caption, int code, int width,
                              int height, KeySink sink) {
        Button button = new Button(host);
        button.setAllCaps(false);
        button.setText(caption);
        button.setTextSize(14);
        button.setTextColor(Color.WHITE);
        button.setTypeface(null, Typeface.BOLD);
        button.setPadding(0,0,0,0);
        button.setMinHeight(0);
        button.setMinimumHeight(0);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setBackground(background(0xB02B2247, 0x99D7CEFA));
        button.setLayoutParams(new LinearLayout.LayoutParams(dp(host,width),dp(host,height)));
        button.setContentDescription(caption + " keyboard control");
        button.setOnTouchListener(new View.OnTouchListener() {
            boolean down = false;
            @Override public boolean onTouch(View view, MotionEvent event) {
                switch(event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        if (!down) {
                            down=true;
                            view.setAlpha(.66f);
                            sink.send(code,true);
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        if (down) {
                            down=false;
                            view.setAlpha(1f);
                            sink.send(code,false);
                        }
                        return true;
                    default:
                        return true;
                }
            }
        });
        return button;
    }

    private static LinearLayout row(Activity host) {
        LinearLayout panel = new LinearLayout(host);
        panel.setOrientation(LinearLayout.HORIZONTAL);
        panel.setGravity(Gravity.CENTER);
        return panel;
    }

    private static void addSpacer(Activity host, LinearLayout row, int width, int height) {
        View spacer = new View(host);
        row.addView(spacer,new LinearLayout.LayoutParams(dp(host,width),dp(host,height)));
    }

    /** Adds non-fullscreen button panels; uncovered game area remains touchable. */
    public static void attach(Activity host, FrameLayout root, KeySink sink) {
        final int control=49;
        final int gap=4;

        LinearLayout pad = new LinearLayout(host);
        pad.setOrientation(LinearLayout.VERTICAL);
        LinearLayout top=row(host);
        addSpacer(host,top,control+gap,control);
        top.addView(key(host,"↑",KeyEvent.KEYCODE_DPAD_UP,control,control,sink));
        addSpacer(host,top,control+gap,control);
        pad.addView(top);
        LinearLayout middle=row(host);
        middle.addView(key(host,"←",KeyEvent.KEYCODE_DPAD_LEFT,control,control,sink));
        addSpacer(host,middle,gap,control);
        middle.addView(key(host,"↓",KeyEvent.KEYCODE_DPAD_DOWN,control,control,sink));
        addSpacer(host,middle,gap,control);
        middle.addView(key(host,"→",KeyEvent.KEYCODE_DPAD_RIGHT,control,control,sink));
        pad.addView(middle);
        FrameLayout.LayoutParams padParams=new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM|Gravity.LEFT);
        padParams.leftMargin=dp(host,11);
        padParams.bottomMargin=dp(host,23);
        root.addView(pad,padParams);

        LinearLayout actions = new LinearLayout(host);
        actions.setOrientation(LinearLayout.VERTICAL);
        LinearLayout first=row(host);
        first.addView(key(host,"S",KeyEvent.KEYCODE_S,47,control,sink));
        addSpacer(host,first,gap,control);
        first.addView(key(host,"C",KeyEvent.KEYCODE_C,47,control,sink));
        actions.addView(first);
        LinearLayout second=row(host);
        second.addView(key(host,"X Run",KeyEvent.KEYCODE_X,47,control,sink));
        addSpacer(host,second,gap,control);
        second.addView(key(host,"Z OK",KeyEvent.KEYCODE_Z,47,control,sink));
        actions.addView(second);
        LinearLayout third=row(host);
        third.addView(key(host,"L",KeyEvent.KEYCODE_A,47,35,sink));
        addSpacer(host,third,gap,35);
        third.addView(key(host,"Start",KeyEvent.KEYCODE_SPACE,47,35,sink));
        addSpacer(host,third,gap,35);
        third.addView(key(host,"R",KeyEvent.KEYCODE_D,47,35,sink));
        actions.addView(third);
        FrameLayout.LayoutParams actionParams=new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM|Gravity.RIGHT);
        actionParams.rightMargin=dp(host,11);
        actionParams.bottomMargin=dp(host,23);
        root.addView(actions,actionParams);
    }
}
