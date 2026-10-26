package com.winlator;

import android.app.Activity;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.charoitegames.core.CharoiteEnvironments;
import com.charoitegames.core.CharoiteThemes;

/**
 * Portal-owned launch presentation only. The real Wine/XServer session is
 * created and torn down by the existing backend, not by this view.
 * Do not alter saved games, prefixes, containers or active window focus.
 */
public final class CharoiteStartupScreen {
    private CharoiteStartupScreen() {}

    private static int dp(Activity activity, float size) {
        return (int)(size * activity.getResources().getDisplayMetrics().density + 0.5f);
    }

    private static TextView text(Activity activity, String value, float size,
                                 int color, boolean bold) {
        TextView view = new TextView(activity);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private static GradientDrawable panelColor(int color, float radius,
                                                Activity activity) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(activity, radius));
        return drawable;
    }

    public static View create(Activity activity) {
        // PreloaderDialog is typed as Activity upstream; the real game
        // renderer is AppCompatActivity. Keep a safe fallback for other callers.
        androidx.appcompat.app.AppCompatActivity portalHost =
                activity instanceof androidx.appcompat.app.AppCompatActivity
                        ? (androidx.appcompat.app.AppCompatActivity) activity : null;
        // XServerDisplayActivity has a separate Activity.getPreferences()
        // namespace. The Core launcher supplies the exact selected realm for
        // this session. Fallbacks read the shared Portal registry, never the
        // renderer Activity's private preference file.
        String theme = activity.getIntent().getStringExtra("charoite_environment_theme");
        if (theme == null || theme.isEmpty())
            theme = portalHost == null ? "cosmic"
                    : CharoiteEnvironments.activeTheme(portalHost);
        boolean sakura = "sakura".equals(theme) || "touhou".equals(theme);
        int highlight = sakura ? 0xffffb6d6 : 0xffcfb0ff;
        int secondary = 0xffd7cfe4;
        FrameLayout root = new FrameLayout(activity);
        root.setBackground(CharoiteThemes.defaultWallpaper(theme, true));
        root.setContentDescription("Charoite Portal is preparing the Windows game environment");

        LinearLayout content = new LinearLayout(activity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setGravity(Gravity.CENTER_HORIZONTAL);
        content.setPadding(dp(activity, 25), dp(activity, 30),
                dp(activity, 25), dp(activity, 30));
        GradientDrawable card = panelColor(0xee21172f, 26, activity);
        card.setStroke(dp(activity, 1), sakura ? 0x77ef9bc4 : 0x778a76ce);
        content.setBackground(card);

        FrameLayout medallion = new FrameLayout(activity);
        GradientDrawable ring = panelColor(sakura ? 0xff58304d : 0xff39295b, 99, activity);
        ring.setStroke(dp(activity, 2), highlight);
        medallion.setBackground(ring);
        TextView monogram = text(activity, "CG", 33, 0xffffffff, true);
        medallion.addView(monogram, new FrameLayout.LayoutParams(-1, -1));
        LinearLayout.LayoutParams seal = new LinearLayout.LayoutParams(
                dp(activity, 86), dp(activity, 86));
        seal.bottomMargin = dp(activity, 20);
        content.addView(medallion, seal);

        TextView title = text(activity, "CHAROITE PORTAL", 23, Color.WHITE, true);
        title.setLetterSpacing(0.10f);
        content.addView(title);
        TextView core = text(activity, "C H A R O I T E   C O R E", 11,
                highlight, true);
        LinearLayout.LayoutParams coreParams = new LinearLayout.LayoutParams(-1, -2);
        coreParams.topMargin = dp(activity, 7);
        content.addView(core, coreParams);

        View rule = new View(activity);
        rule.setBackgroundColor(sakura ? 0x88e9a3c5 : 0x888a76ce);
        LinearLayout.LayoutParams ruleParams = new LinearLayout.LayoutParams(
                dp(activity, 148), dp(activity, 1));
        ruleParams.topMargin = dp(activity, 22);
        ruleParams.bottomMargin = dp(activity, 18);
        content.addView(rule, ruleParams);

        String realm = activity.getIntent().getStringExtra("charoite_environment_name");
        if (realm == null || realm.isEmpty())
            realm = portalHost == null ? "Gaming Environment"
                    : CharoiteEnvironments.activeName(portalHost);
        TextView environment = text(activity, realm, 19, Color.WHITE, true);
        environment.setMaxLines(2);
        content.addView(environment);

        // PreloaderDialog retains its standard status TextView id, so
        // existing "starting" and "updating system files" states still work.
        TextView status = text(activity, "Preparing Windows environment", 14, secondary, false);
        status.setId(com.winlator.R.id.TextView);
        LinearLayout.LayoutParams statusParams = new LinearLayout.LayoutParams(-1, -2);
        statusParams.topMargin = dp(activity, 12);
        content.addView(status, statusParams);

        ProgressBar progress = new ProgressBar(activity, null,
                android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        progress.setIndeterminateTintList(ColorStateList.valueOf(highlight));
        LinearLayout.LayoutParams progressParams = new LinearLayout.LayoutParams(
                -1, dp(activity, 4));
        progressParams.topMargin = dp(activity, 23);
        progressParams.bottomMargin = dp(activity, 13);
        content.addView(progress, progressParams);

        TextView footnote = text(activity,
                "Your Windows environment and game files remain in place",
                11, 0xffc2b9d0, false);
        footnote.setMaxLines(2);
        content.addView(footnote);

        int screenWidth = activity.getResources().getDisplayMetrics().widthPixels;
        int width = Math.max(dp(activity, 240),
                Math.min(dp(activity, 440), screenWidth - dp(activity, 28)));
        FrameLayout.LayoutParams center = new FrameLayout.LayoutParams(
                width, -2, Gravity.CENTER);
        center.leftMargin = dp(activity, 10);
        center.rightMargin = dp(activity, 10);
        root.addView(content, center);
        return root;
    }
}
