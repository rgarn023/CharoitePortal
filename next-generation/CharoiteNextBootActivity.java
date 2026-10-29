package com.charoitegames.core;

import android.app.Activity;
import android.app.Application;
import android.app.Dialog;
import android.animation.ObjectAnimator;
import android.graphics.drawable.ClipDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.graphics.drawable.Drawable;
import android.view.animation.LinearInterpolator;
import android.widget.ProgressBar;
import android.view.WindowManager;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import android.content.Intent;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Charoite Next-only launch screen: original approved app artwork, exactly five
 * seconds before the main Portal activity is shown. No Wine/prefix work occurs
 * here and no audio plays while the boot image is onscreen.
 */
public final class CharoiteNextBootActivity extends Activity {
    public static final long BOOT_DURATION_MS = 5000L;
    private static final String EXTRA_PLAY_CHIME =
            "com.charoitegames.core.NEXT_PLAY_CRYSTAL_CHIME";
    private static final AtomicBoolean REENTRY_NEEDED = new AtomicBoolean(false);
    private static final AtomicBoolean TRACKER_INSTALLED = new AtomicBoolean(false);
    private static Dialog activeReentryDialog;

    /**
     * Memory trim notifications are NOT a reliable way of detecting Home /
     * task-switching on Android 17. ActivityLifecycleCallbacks report each
     * Activity stop/start regardless of process caching or memory pressure.
     *
     * Register once from the Portal's onCreate. When all app activities have
     * stopped, the process has actually gone into the background. On a warm
     * return to the Portal we present the same five-second splash, without
     * recreating the Portal or touching installed games and Wine prefixes.
     * Navigation into Charoite's in-app game/setup activities is deliberately
     * excluded because they count as app-visible activities.
     */
    public static void installReentryTracker(Activity portal) {
        if (!TRACKER_INSTALLED.compareAndSet(false, true)) return;
        portal.getApplication().registerActivityLifecycleCallbacks(
                new Application.ActivityLifecycleCallbacks() {
            private final Set<Activity> started =
                    Collections.newSetFromMap(new WeakHashMap<Activity, Boolean>());
            private boolean wentBackground;

            @Override public void onActivityCreated(Activity a, Bundle state) {}
            @Override public void onActivityStarted(Activity a) {
                if (wentBackground && a instanceof com.winlator.TouhouEntryActivity)
                    REENTRY_NEEDED.set(true);
                started.add(a);
                wentBackground = false;
            }
            @Override public void onActivityResumed(Activity a) {}
            @Override public void onActivityPaused(Activity a) {}
            @Override public void onActivityStopped(Activity a) {
                if (started.remove(a) && started.isEmpty() && !a.isChangingConfigurations())
                    wentBackground = true;
                if (a instanceof com.winlator.TouhouEntryActivity
                        && activeReentryDialog != null) {
                    if (activeReentryDialog.isShowing()) activeReentryDialog.dismiss();
                    activeReentryDialog = null;
                }
            }
            @Override public void onActivitySaveInstanceState(Activity a, Bundle state) {}
            @Override public void onActivityDestroyed(Activity a) {
                started.remove(a);
            }
        });
    }

    /** Some launchers deliver an explicit warm ACTION_MAIN/LAUNCHER intent
     * rather than stopping/starting the visible task (notably multi-window).
     * Avoid treating internal game or installer intents as launcher openings. */
    public static void noteLauncherIntent(Intent intent) {
        if (intent != null
                && Intent.ACTION_MAIN.equals(intent.getAction())
                && intent.hasCategory(Intent.CATEGORY_LAUNCHER))
            REENTRY_NEEDED.set(true);
    }
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable openMain;
    private boolean completed;

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }


    /** A high-resolution original crystal portal, crisp text, and a real
     * five-second presentation progress bar. Same view for cold/re-entry. */
    private static FrameLayout createBootView(Activity activity) {
        FrameLayout boot = new FrameLayout(activity);
        boot.setBackgroundColor(Color.rgb(13, 8, 30));
        boot.setContentDescription("Charoite Core starting");
        LinearLayout emblem = new LinearLayout(activity);
        emblem.setOrientation(LinearLayout.VERTICAL);
        emblem.setGravity(Gravity.CENTER);
        emblem.setPadding(density(activity, 20), density(activity, 24),
                density(activity, 20), density(activity, 24));

        ImageView icon = new ImageView(activity);
        // Unlike the tiny launcher JPEG, the splash-only original is generated
        // at 768 x 768 pixels. Keep the approved launcher image as fallback.
        try {
            icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_art);
        } catch (RuntimeException error) {
            icon.setImageResource(com.winlator.R.drawable.charoite_portal_icon);
        }
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setContentDescription("Charoite crystal portal");
        emblem.addView(icon, new LinearLayout.LayoutParams(
                density(activity, 248), density(activity, 248)));

        TextView title = new TextView(activity);
        title.setText("CHAROITE CORE");
        title.setGravity(Gravity.CENTER);
        title.setTextColor(Color.WHITE);
        title.setTextSize(23);
        title.setLetterSpacing(0.13f);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams titleParams =
                new LinearLayout.LayoutParams(-2, -2);
        titleParams.topMargin = density(activity, 20);
        emblem.addView(title, titleParams);

        TextView subtitle = new TextView(activity);
        subtitle.setText("NEXT");
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setTextColor(Color.rgb(198, 180, 240));
        subtitle.setTextSize(12);
        subtitle.setLetterSpacing(0.34f);
        LinearLayout.LayoutParams subtitleParams =
                new LinearLayout.LayoutParams(-2, -2);
        subtitleParams.topMargin = density(activity, 6);
        emblem.addView(subtitle, subtitleParams);

        ProgressBar progress = new ProgressBar(activity, null,
                android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(false);
        progress.setMax(1000);
        progress.setProgress(0);
        GradientDrawable track = new GradientDrawable();
        track.setColor(Color.rgb(31, 19, 55));
        track.setCornerRadius(density(activity, 8));
        track.setStroke(density(activity, 1), Color.rgb(126, 77, 198));
        GradientDrawable fill = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                new int[]{0xff6332C3, 0xffA45DF4, 0xffF5DDFF});
        fill.setCornerRadius(density(activity, 8));
        LayerDrawable layers = new LayerDrawable(new Drawable[]{
                track, new ClipDrawable(fill, Gravity.LEFT, ClipDrawable.HORIZONTAL)});
        layers.setId(0, android.R.id.background);
        layers.setId(1, android.R.id.progress);
        progress.setProgressDrawable(layers);
        LinearLayout.LayoutParams barParams = new LinearLayout.LayoutParams(
                density(activity, 250), density(activity, 9));
        barParams.topMargin = density(activity, 29);
        emblem.addView(progress, barParams);
        ObjectAnimator animation = ObjectAnimator.ofInt(progress, "progress", 0, 1000);
        animation.setDuration(BOOT_DURATION_MS);
        animation.setInterpolator(new LinearInterpolator());
        animation.start();

        TextView hint = new TextView(activity);
        hint.setText("STARTING CHAROITE CORE");
        hint.setTextSize(10);
        hint.setTextColor(0xffCAB4ED);
        hint.setLetterSpacing(.16f);
        hint.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hintParams = new LinearLayout.LayoutParams(-2, -2);
        hintParams.topMargin = density(activity, 14);
        emblem.addView(hint, hintParams);

        FrameLayout.LayoutParams emblemParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        boot.addView(emblem, emblemParams);
        return boot;
    }

    private static int density(Activity activity, int size) {
        return Math.round(size * activity.getResources().getDisplayMetrics().density);
    }

    /** If Android resumes an existing Portal task rather than launching the
     * LAUNCHER Activity again, show the same boot presentation as a modal
     * overlay. Preserve the live Portal Activity and its UI/process state. */
    public static void showOnBackgroundReentryIfNeeded(Activity activity) {
        if (!REENTRY_NEEDED.getAndSet(false)
                || activity.isFinishing() || activity.isDestroyed()) return;
        if (activeReentryDialog != null && activeReentryDialog.isShowing())
            activeReentryDialog.dismiss();
        Dialog splash = new Dialog(activity,
                android.R.style.Theme_Black_NoTitleBar_Fullscreen);
        splash.setCancelable(false);
        splash.setContentView(createBootView(activity));
        splash.show();
        activeReentryDialog = splash;
        if (splash.getWindow() != null) {
            splash.getWindow().setStatusBarColor(Color.rgb(13, 8, 30));
            splash.getWindow().setNavigationBarColor(Color.rgb(13, 8, 30));
            splash.getWindow().setLayout(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT);
        }
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (splash.isShowing()) splash.dismiss();
            if (activeReentryDialog == splash) activeReentryDialog = null;
            if (!activity.isFinishing() && !activity.isDestroyed())
                playCrystalChime(activity);
        }, BOOT_DURATION_MS);
    }

    @Override public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        getWindow().setStatusBarColor(Color.rgb(13, 8, 30));
        getWindow().setNavigationBarColor(Color.rgb(13, 8, 30));
        setContentView(createBootView(this));

        // Single cold-launch delay, not a blocking sleep or a Wine startup delay.
        openMain = () -> {
            if (completed || isFinishing() || isDestroyed()) return;
            completed = true;
            Intent main = new Intent(this, com.winlator.TouhouEntryActivity.class);
            main.putExtra(EXTRA_PLAY_CHIME, true);
            startActivity(main);
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            finish();
        };
        handler.postDelayed(openMain, BOOT_DURATION_MS);
    }

    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    /** Called only after Next's actual main Portal view has been rendered. */
    public static void playArrivalChimeIfRequested(Activity activity) {
        Intent intent = activity.getIntent();
        if (intent == null || !intent.getBooleanExtra(EXTRA_PLAY_CHIME, false))
            return;
        intent.removeExtra(EXTRA_PLAY_CHIME); // never repeat after rotation
        playCrystalChime(activity);
    }

    private static void playCrystalChime(Activity activity) {
        activity.getWindow().getDecorView().postDelayed(() -> {
            if (activity.isFinishing() || activity.isDestroyed() || !activity.hasWindowFocus())
                return;
            AudioManager audio = (AudioManager)
                    activity.getSystemService(Activity.AUDIO_SERVICE);
            if (audio != null && audio.getRingerMode() == AudioManager.RINGER_MODE_SILENT)
                return;
            try {
                AudioAttributes attributes = new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build();
                MediaPlayer player = MediaPlayer.create(activity,
                        com.winlator.R.raw.charoite_crystal_startup, attributes, 0);
                if (player == null) return;
                player.setOnCompletionListener(MediaPlayer::release);
                player.setOnErrorListener((mp, what, extra) -> {
                    mp.release();
                    return true;
                });
                player.start();
            } catch (RuntimeException ignored) {
                // No startup-audio error should crash the app.
            }
        }, 220L);
    }
}
