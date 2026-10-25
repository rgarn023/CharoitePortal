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
            @Override public boolean onTouch(View view, MotionEvent event) {
                switch(event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        view.setAlpha(.66f);
                        // The shared guarded sink deduplicates key downs and
                        // handles releases caused by lost window focus.
                        sink.send(code,true);
                        return true;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        view.setAlpha(1f);
                        sink.send(code,false);
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
        final int control=46;
        final int gap=4;
        // Track held keys centrally, so hiding the panel or losing focus
        // never strands a movement key in the running Windows game.
        final java.util.Set<Integer> held=new java.util.HashSet<>();
        final KeySink guarded=(code,pressed) -> {
            if(pressed ? held.add(code) : held.remove(code))
                sink.send(code,pressed);
        };
        final Runnable releaseAll=() -> {
            for(Integer key : new java.util.ArrayList<>(held)) guarded.send(key,false);
        };
        root.getViewTreeObserver().addOnWindowFocusChangeListener(hasFocus -> {
            if(!hasFocus) releaseAll.run();
        });

        LinearLayout pad = new LinearLayout(host);
        pad.setOrientation(LinearLayout.VERTICAL);
        LinearLayout top=row(host);
        addSpacer(host,top,control+gap,control);
        top.addView(key(host,"↑",KeyEvent.KEYCODE_DPAD_UP,control,control,guarded));
        addSpacer(host,top,control+gap,control);
        pad.addView(top);
        LinearLayout middle=row(host);
        middle.addView(key(host,"←",KeyEvent.KEYCODE_DPAD_LEFT,control,control,guarded));
        addSpacer(host,middle,gap,control);
        middle.addView(key(host,"↓",KeyEvent.KEYCODE_DPAD_DOWN,control,control,guarded));
        addSpacer(host,middle,gap,control);
        middle.addView(key(host,"→",KeyEvent.KEYCODE_DPAD_RIGHT,control,control,guarded));
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
        first.addView(key(host,"S",KeyEvent.KEYCODE_S,47,control,guarded));
        addSpacer(host,first,gap,control);
        first.addView(key(host,"C",KeyEvent.KEYCODE_C,47,control,guarded));
        actions.addView(first);
        LinearLayout second=row(host);
        second.addView(key(host,"X Run",KeyEvent.KEYCODE_X,47,control,guarded));
        addSpacer(host,second,gap,control);
        second.addView(key(host,"Z OK",KeyEvent.KEYCODE_Z,47,control,guarded));
        actions.addView(second);
        LinearLayout third=row(host);
        third.addView(key(host,"L",KeyEvent.KEYCODE_A,47,35,guarded));
        addSpacer(host,third,gap,35);
        third.addView(key(host,"Start",KeyEvent.KEYCODE_SPACE,47,35,guarded));
        addSpacer(host,third,gap,35);
        third.addView(key(host,"R",KeyEvent.KEYCODE_D,47,35,guarded));
        actions.addView(third);
        FrameLayout.LayoutParams actionParams=new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM|Gravity.RIGHT);
        actionParams.rightMargin=dp(host,11);
        actionParams.bottomMargin=dp(host,23);
        LinearLayout fourth=row(host);
        fourth.addView(key(host,"Shift",KeyEvent.KEYCODE_SHIFT_LEFT,47,35,guarded));
        addSpacer(host,fourth,gap,35);
        fourth.addView(key(host,"Enter",KeyEvent.KEYCODE_ENTER,47,35,guarded));
        addSpacer(host,fourth,gap,35);
        fourth.addView(key(host,"Esc",KeyEvent.KEYCODE_ESCAPE,47,35,guarded));
        actions.addView(fourth);
        root.addView(actions,actionParams);

        // Keep the original mouse/touchpad accessible without restarting
        // the Windows game. This toggle is independent of Winlator profiles.
        Button toggle=new Button(host);
        toggle.setText("HIDE KEYS");
        toggle.setAllCaps(false);
        toggle.setTextSize(11);
        toggle.setTextColor(Color.WHITE);
        toggle.setMinHeight(0);
        toggle.setMinimumHeight(0);
        toggle.setPadding(0,0,0,0);
        toggle.setBackground(background(0xB02B2247,0x99D7CEFA));
        FrameLayout.LayoutParams toggleParams=new FrameLayout.LayoutParams(
            dp(host,105),dp(host,36),Gravity.TOP|Gravity.RIGHT);
        toggleParams.topMargin=dp(host,10);
        toggleParams.rightMargin=dp(host,10);
        root.addView(toggle,toggleParams);
        toggle.setOnClickListener(v -> {
            boolean shouldShow=pad.getVisibility()!=View.VISIBLE;
            if(!shouldShow) releaseAll.run();
            pad.setVisibility(shouldShow?View.VISIBLE:View.GONE);
            actions.setVisibility(shouldShow?View.VISIBLE:View.GONE);
            toggle.setText(shouldShow?"HIDE KEYS":"SHOW KEYS");
        });
    }
}
