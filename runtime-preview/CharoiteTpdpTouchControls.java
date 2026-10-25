package com.winlator;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

import com.winlator.xserver.XKeycode;
import com.winlator.xserver.XServer;

import java.util.EnumSet;

/**
 * Touch-only keyboard for TPDP 1.34 and Shard of Dreams.
 * The official TPDP key map uses arrow keys for movement, Z to confirm,
 * X to cancel/run, S for menu, C for display, A/D to turn menu pages,
 * Space for action and Left Shift for sorting.
 *
 * No remapping, Wine registry edits, or saved user input profile changes.
 * Each touch sends actual X key-down/up, allowing held movement and running.
 * Only added for gn_enbu.exe and enbu_ap.exe in XServerDisplayActivity.
 */
public final class CharoiteTpdpTouchControls extends FrameLayout {
    private final XServer xServer;
    private final EnumSet<XKeycode> active = EnumSet.noneOf(XKeycode.class);
    private final LinearLayout arrows;
    private final LinearLayout actions;
    private final Button toggle;
    private boolean showing = true;

    private CharoiteTpdpTouchControls(Activity activity, XServer xServer) {
        super(activity);
        this.xServer = xServer;
        setClipChildren(false);
        setClipToPadding(false);
        setFocusable(false);
        setClickable(false);

        // An always-visible small toggle restores an unobstructed Windows
        // touchpad/mouse area without stopping the game.
        toggle = new Button(activity);
        toggle.setText("HIDE KEYS");
        toggle.setTextColor(Color.WHITE);
        toggle.setTextSize(10);
        toggle.setAllCaps(false);
        toggle.setMinHeight(0);
        toggle.setMinimumHeight(0);
        toggle.setPadding(dp(7), 0, dp(7), 0);
        toggle.setBackground(backdrop());
        toggle.setOnClickListener(v -> {
            showing = !showing;
            arrows.setVisibility(showing ? VISIBLE : GONE);
            actions.setVisibility(showing ? VISIBLE : GONE);
            toggle.setText(showing ? "HIDE KEYS" : "SHOW KEYS");
            if (!showing) releaseAll();
        });
        LayoutParams show = new LayoutParams(dp(104), dp(36),
                Gravity.TOP | Gravity.END);
        show.topMargin=dp(10);
        show.rightMargin=dp(10);
        addView(toggle,show);

        arrows = new LinearLayout(activity);
        arrows.setOrientation(LinearLayout.VERTICAL);
        arrows.setFocusable(false);
        String[][] arrowLabels={{"", "▲", ""},{"◀", "", "▶"},{"", "▼", ""}};
        XKeycode[][] arrowKeys={{null,XKeycode.KEY_UP,null},
                {XKeycode.KEY_LEFT,null,XKeycode.KEY_RIGHT},
                {null,XKeycode.KEY_DOWN,null}};
        for(int row=0;row<3;row++) {
            LinearLayout line = new LinearLayout(activity);
            for(int column=0;column<3;column++) {
                View key=arrowKeys[row][column]==null
                        ? new View(activity)
                        : makeKey(activity,arrowLabels[row][column],arrowKeys[row][column]);
                line.addView(key,new LinearLayout.LayoutParams(dp(46),dp(46)));
            }
            arrows.addView(line);
        }
        LayoutParams left=new LayoutParams(dp(138),dp(138),
                Gravity.START|Gravity.BOTTOM);
        left.leftMargin=dp(7);
        left.bottomMargin=dp(9);
        addView(arrows,left);

        actions=new LinearLayout(activity);
        actions.setOrientation(LinearLayout.VERTICAL);
        addActionRow(activity,"Z","X",XKeycode.KEY_Z,XKeycode.KEY_X);
        addActionRow(activity,"S","C",XKeycode.KEY_S,XKeycode.KEY_C);
        addActionRow(activity,"A","D",XKeycode.KEY_A,XKeycode.KEY_D);
        addActionRow(activity,"SPACE","SHIFT",XKeycode.KEY_SPACE,XKeycode.KEY_SHIFT_L);
        addActionRow(activity,"ENTER","ESC",XKeycode.KEY_ENTER,XKeycode.KEY_ESC);
        LayoutParams right=new LayoutParams(dp(116),dp(210),
                Gravity.END|Gravity.BOTTOM);
        right.rightMargin=dp(7);
        right.bottomMargin=dp(9);
        addView(actions,right);
    }

    public static void attach(Activity activity, FrameLayout screen, XServer xServer) {
        CharoiteTpdpTouchControls overlay=new CharoiteTpdpTouchControls(activity,xServer);
        screen.addView(overlay,new FrameLayout.LayoutParams(
                LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT));
    }

    private void addActionRow(Activity activity,String leftLabel,String rightLabel,
                              XKeycode leftKey,XKeycode rightKey) {
        LinearLayout row=new LinearLayout(activity);
        row.addView(makeKey(activity,leftLabel,leftKey),
                new LinearLayout.LayoutParams(dp(58),dp(42)));
        row.addView(makeKey(activity,rightLabel,rightKey),
                new LinearLayout.LayoutParams(dp(58),dp(42)));
        actions.addView(row);
    }

    private Button makeKey(Activity activity,String label,XKeycode key) {
        Button button=new Button(activity);
        button.setText(label);
        button.setTextColor(Color.WHITE);
        button.setTextSize(label.length()>3?10:17);
        button.setAllCaps(false);
        button.setMinHeight(0);
        button.setMinimumHeight(0);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setPadding(0,0,0,0);
        button.setBackground(backdrop());
        button.setContentDescription("TPDP keyboard " + label);
        final boolean[] held={false};
        button.setOnTouchListener((view,event) -> {
            switch(event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    held[0]=true;
                    press(key);
                    return true;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    if(held[0]) {
                        held[0]=false;
                        release(key);
                    }
                    return true;
                default:
                    return true;
            }
        });
        // Accessible click for assistive input; ordinary touch uses the
        // held-key path above, so this never causes a duplicate press.
        button.setOnClickListener(v -> {
            press(key);
            v.postDelayed(() -> release(key),60);
        });
        return button;
    }

    private GradientDrawable backdrop() {
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(0xBB242B47);
        bg.setCornerRadius(dp(9));
        bg.setStroke(dp(1),0xBBD4DEF9);
        return bg;
    }

    private void press(XKeycode key) {
        if(active.add(key)) xServer.injectKeyPress(key);
    }

    private void release(XKeycode key) {
        if(active.remove(key)) xServer.injectKeyRelease(key);
    }

    private void releaseAll() {
        for(XKeycode key:EnumSet.copyOf(active)) release(key);
    }

    @Override protected void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if(!hasFocus) releaseAll();
    }

    @Override protected void onDetachedFromWindow() {
        releaseAll();
        super.onDetachedFromWindow();
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
