package com.charoitegames.core;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

/**
 * Reusable connected page-tab navigation for Charoite Games Android launchers.
 *
 * The host supplies page names, colors and a selection callback; Charoite Core
 * supplies the entire connected visual style, touch targets, selection state,
 * and clearance above Android's system navigation bar. It does not own or
 * modify any launcher page content, Wine runtime, game files or wallpaper.
 */
public final class CharoitePageTabs extends LinearLayout {
    public interface OnTabSelected {
        void onTabSelected(int index);
    }

    private final Button[] tabs;
    private final OnTabSelected selectionListener;
    private int currentIndex = 0;
    private int accent = 0xff5667D8;
    private int secondary = 0xff626877;
    private int selectedBackground = 0xffE8EBFD;
    private int surface = 0xffffffff;
    private int line = 0xffE7E9F0;
    private boolean darkMode = false;

    public CharoitePageTabs(Context context, String[] titles, OnTabSelected listener) {
        super(context);
        if (titles == null || titles.length < 2 || listener == null)
            throw new IllegalArgumentException("Page tabs require at least two titles and a listener");
        selectionListener = listener;
        tabs = new Button[titles.length];
        setOrientation(HORIZONTAL);
        setGravity(Gravity.BOTTOM);
        setPadding(dp(16), dp(7), dp(16), dp(21));
        setMinimumHeight(dp(88));
        for (int i = 0; i < titles.length; i++) {
            final int index = i;
            final String title = titles[i];
            if (title == null || title.trim().isEmpty())
                throw new IllegalArgumentException("Page title must not be empty");
            Button button = new Button(context);
            button.setText(title);
            button.setAllCaps(false);
            button.setTextSize(14);
            button.setGravity(Gravity.CENTER);
            button.setMinimumHeight(dp(48));
            button.setPadding(dp(6), dp(9), dp(6), dp(7));
            button.setContentDescription(title + " page");
            button.setStateListAnimator(null);
            button.setElevation(0);
            button.setOnClickListener(v -> {
                if (currentIndex != index) setSelectedIndex(index);
                selectionListener.onTabSelected(index);
            });
            LayoutParams params = new LayoutParams(0, LayoutParams.MATCH_PARENT, 1f);
            params.setMargins(0, 0, 0, 0);
            addView(button, params);
            tabs[i] = button;
        }
        setSelectedIndex(0);
    }

    /** Theme colors are supplied by the host. Works with light and dark One UI. */
    public void setPalette(int surfaceColor, int accentColor, int secondaryColor,
                           int selectedColor, int lineColor, boolean dark) {
        surface = surfaceColor;
        accent = accentColor;
        secondary = secondaryColor;
        selectedBackground = selectedColor;
        line = lineColor;
        darkMode = dark;
        setBackgroundColor(surface);
        updateStyles();
    }

    public void setSelectedIndex(int index) {
        if (index < 0 || index >= tabs.length)
            throw new IllegalArgumentException("Invalid page tab index");
        currentIndex = index;
        updateStyles();
    }

    public int getSelectedIndex() {
        return currentIndex;
    }

    public static int preferredHeight(Context context) {
        return Math.round(88 * context.getResources().getDisplayMetrics().density);
    }

    private int dp(int units) {
        return Math.round(units * getResources().getDisplayMetrics().density);
    }

    private void updateStyles() {
        for (int index = 0; index < tabs.length; index++) {
            boolean selected = index == currentIndex;
            Button tab = tabs[index];
            tab.setBackgroundTintList((ColorStateList) null);
            tab.setTextColor(selected ? accent : secondary);
            tab.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL),
                    selected ? Typeface.BOLD : Typeface.NORMAL);
            GradientDrawable page = new GradientDrawable();
            page.setColor(selected ? selectedBackground : (darkMode ? 0xff282930 : 0xffECEEF4));
            page.setCornerRadii(new float[]{
                    dp(17), dp(17), dp(17), dp(17),
                    0, 0, 0, 0
            });
            page.setStroke(dp(1), selected ? accent : line);
            tab.setBackground(page);
            LayoutParams params = (LayoutParams) tab.getLayoutParams();
            if (params != null) {
                params.topMargin = selected ? 0 : dp(8);
                params.bottomMargin = 0;
                tab.setLayoutParams(params);
            }
            tab.setSelected(selected);
            tab.setContentDescription(tab.getText() + " page" +
                    (selected ? ", selected" : ""));
        }
    }
}
