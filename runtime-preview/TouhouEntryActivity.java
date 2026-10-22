package com.winlator;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Branded entrypoint for a Winlator-based standalone runtime preview.
 * Actual Wine/Box64 execution is delegated to unmodified upstream MainActivity.
 * No game content is shipped.
 */
public final class TouhouEntryActivity extends Activity {
    private final int background = Color.rgb(14, 15, 31);
    private final int accent = Color.rgb(132, 93, 213);

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(background);
        getWindow().setNavigationBarColor(background);
        ScrollView scrolling = new ScrollView(this);
        scrolling.setFillViewport(true);
        scrolling.setBackgroundColor(background);
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(24), dp(40), dp(24), dp(25));
        scrolling.addView(main);
        setContentView(scrolling);
        main.addView(label("CHAROITE GAMES", 13f, 0xffad93f9, true));
        main.addView(label("Touhou Pocket Launcher", 27f, Color.WHITE, true));
        main.addView(label("Embedded Windows runtime preview", 15f, 0xffbfc8e3, false));
        main.addView(spacer(20));
        main.addView(label("This experimental build includes the Winlator runtime for testing Touhou Project Windows games. " +
            "It does not bundle games, apply patches automatically, or guarantee that Shard of Dreams launches.", 14f, 0xffdae1f1, false));
        main.addView(spacer(20));
        Button open = new Button(this);
        open.setText("OPEN WINDOWS RUNTIME");
        open.setAllCaps(false);
        open.setTextColor(Color.WHITE);
        open.setBackgroundTintList(android.content.res.ColorStateList.valueOf(accent));
        open.setMinHeight(dp(58));
        open.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        main.addView(open);
        main.addView(spacer(24));
        main.addView(label("FIRST TEST ON YOUR GALAXY", 15f, Color.WHITE, true));
        main.addView(label(
            "1. Open the Windows runtime. Allow first-launch setup to finish.\n" +
            "2. Create a container with appropriate graphics settings.\n" +
            "3. Copy your legally obtained TPDP files to a folder visible to the Windows environment.\n" +
            "4. Install and test the base game, then Shard of Dreams.\n" +
            "5. English patches and the optional notkey workaround will be integrated into the dedicated launcher next.",
            14f, 0xffc9d3ea, false));
        main.addView(spacer(24));
        main.addView(label(
            "Runtime derived from Winlator by brunodev85 (LGPL-2.1), Wine, Box64 and other third-party projects. " +
            "See LICENSE and upstream source at github.com/brunodev85/winlator-app. " +
            "This is a development preview and is not affiliated with FocasLens.",
            12f, 0xffa8b0cc, false));
    }

    private TextView label(String value, float sp, int color, boolean bold) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextColor(color);
        text.setTextSize(sp);
        text.setLineSpacing(dp(4), 1f);
        if (bold) text.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return text;
    }

    private View spacer(int size) {
        View v = new View(this);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, dp(size)));
        return v;
    }

    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }
}
