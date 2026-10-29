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
import android.content.Context;
import android.util.Log;
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

    private static final String STARTUP_PREFS = "charoite_next_startup_diagnostics";
    private static volatile String lastLifecycleEvent = "Not yet observed";
    private static volatile String lastAudioResult = "Not yet attempted";

    /**
     * Unlike unreliable memory-trim callbacks, onUserLeaveHint()/onPause()/onStop()
     * can detect a Home/recent-app transition on Samsung One UI.
     * Internal Charoite activity starts cancel pending replay; the game
     * process, prefixes, and installed software are never modified.
     */
    public static void installReentryTracker(Activity portal) {
        if (!TRACKER_INSTALLED.compareAndSet(false, true)) return;
        portal.getApplication().registerActivityLifecycleCallbacks(
                new Application.ActivityLifecycleCallbacks() {
            private final Set<Activity> started =
                    Collections.newSetFromMap(new WeakHashMap<Activity, Boolean>());

            @Override public void onActivityCreated(Activity a, Bundle state) {}
            @Override public void onActivityStarted(Activity a) {
                started.add(a);
                if (!(a instanceof com.winlator.TouhouEntryActivity)
                        && !(a instanceof CharoiteNextBootActivity)) {
                    // Internal game, file manager, or installer: do NOT replay.
                    REENTRY_NEEDED.set(false);
                    lastLifecycleEvent = "Internal Charoite activity started";
                }
            }
            @Override public void onActivityResumed(Activity a) {}
            @Override public void onActivityPaused(Activity a) {}
            @Override public void onActivityStopped(Activity a) {
                started.remove(a);
                if (a instanceof com.winlator.TouhouEntryActivity
                        && !a.isChangingConfigurations()) {
                    // Only treat the stop as app background if no other
                    // Charoite activity (game, installer, etc.) is visible.
                    boolean appBackground = started.isEmpty();
                    // IMPORTANT: Home can relaunch before Android dispatches
                    // onStop, or BootActivity can still be in the started set.
                    // Never overwrite the prior onUserLeaveHint/onPause signal
                    // with false. Internal navigation clears it in onStart.
                    if (appBackground) REENTRY_NEEDED.set(true);
                    lastLifecycleEvent = appBackground
                            ? "Portal stopped; app backgrounded"
                            : "Portal stopped; preserving pending user leave";
                    saveReport(a);
                }
                if (a instanceof com.winlator.TouhouEntryActivity
                        && activeReentryDialog != null) {
                    if (activeReentryDialog.isShowing())
                        activeReentryDialog.dismiss();
                    activeReentryDialog = null;
                }
            }
            @Override public void onActivitySaveInstanceState(Activity a, Bundle state) {}
            @Override public void onActivityDestroyed(Activity a) {
                started.remove(a);
            }
        });
    }

    /** A reliable signal on Home or user-selected app switching even when
     * Android chooses not to stop the existing task. */
    public static void noteUserLeaving(Activity portal) {
        REENTRY_NEEDED.set(true);
        lastLifecycleEvent = "User leave hint received";
        saveReport(portal);
    }

    /** Fallback for split-screen or launcher paths that only pause the Portal.
     * Internal navigation is excluded when its destination starts. */
    public static void notePortalPaused(Activity portal) {
        REENTRY_NEEDED.set(true);
        lastLifecycleEvent = "Portal paused; waiting for regained window focus";
        saveReport(portal);
    }

    /** The focus callback is the final gate for quick Home/Recents returns,
     * including when Android does not fully stop or destroy the activity.
     * Never consume replay during onResume's pre-focus transition.
     */
    public static void onPortalWindowFocusChanged(Activity portal, boolean focused) {
        if (focused) {
            lastLifecycleEvent = "Portal window focus regained";
            saveReport(portal);
            showOnBackgroundReentryIfNeeded(portal);
        } else if (activeReentryDialog == null) {
            lastLifecycleEvent = "Portal window lost focus";
            saveReport(portal);
        }
    }

    /** Document pickers are external activities, but returning from a picker
     * is NOT a new Portal launch. */
    public static void noteDocumentPickerReturn(Activity portal) {
        REENTRY_NEEDED.set(false);
        lastLifecycleEvent = "Document picker returned (startup suppressed)";
        saveReport(portal);
    }

    /** Samsung may deliver an explicit warm launcher intent instead of
     * stopping/starting the visible task. */
    public static void noteLauncherIntent(Intent intent) {
        if (intent != null
                && Intent.ACTION_MAIN.equals(intent.getAction())
                && intent.hasCategory(Intent.CATEGORY_LAUNCHER)) {
            REENTRY_NEEDED.set(true);
            lastLifecycleEvent = "New launcher intent received";
        }
    }

    private static void saveReport(Context ctx) {
        ctx.getSharedPreferences(STARTUP_PREFS, Context.MODE_PRIVATE).edit()
                .putString("last_event", lastLifecycleEvent)
                .putString("last_audio", lastAudioResult).apply();
        Log.i("CharoiteNextStartup", lastLifecycleEvent + "; " + lastAudioResult);
    }

    /** Read-only, copyable diagnostics if a Samsung build suppresses re-entry
     * or cannot produce audible media output. No private game data is read. */
    public static String startupReport(Context ctx) {
        android.content.SharedPreferences prefs =
                ctx.getSharedPreferences(STARTUP_PREFS, Context.MODE_PRIVATE);
        AudioManager audio = (AudioManager)
                ctx.getSystemService(Context.AUDIO_SERVICE);
        int current = audio == null ? -1
                : audio.getStreamVolume(AudioManager.STREAM_MUSIC);
        int maximum = audio == null ? -1
                : audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
        int mode = audio == null ? -1 : audio.getRingerMode();
        return "CHAROITE NEXT — STARTUP DIAGNOSTICS\n"
                + "Splash art: 768px enhanced copy of approved launcher artwork\n"
                + "Replay: pending until Portal window regains focus\n"
                + "Boot duration: 5000 ms\n"
                + "Last lifecycle: " + prefs.getString("last_event", lastLifecycleEvent) + "\n"
                + "Pending replay: " + REENTRY_NEEDED.get() + "\n"
                + "Last audio: " + prefs.getString("last_audio", lastAudioResult) + "\n"
                + "Media volume: " + current + " / " + maximum + "\n"
                + "Ringer mode: " + mode + " (does not mute media chime)\n"
                + "Games / prefixes / saves: untouched\n";
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
        // A sharper 768px presentation upscale of the *same* approved JPEG,
        // not the unrelated procedurally generated ring graphic.
        icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_icon_hd);
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setContentDescription("Charoite crystal portal");
        emblem.addView(icon, new LinearLayout.LayoutParams(
                density(activity, 228), density(activity, 228)));

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
        // onResume can occur while Samsung is still transitioning the task:
        // keep the request pending until onWindowFocusChanged(true).
        if (activity.isFinishing() || activity.isDestroyed()
                || !activity.hasWindowFocus()) return;
        if (!REENTRY_NEEDED.compareAndSet(true, false)) return;
        lastLifecycleEvent = "Warm foreground focus acquired; splash presented";
        saveReport(activity);
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
            // If Home was pressed again or a newer splash replaced this one,
            // do not play audio or dismiss a different window in background.
            if (activeReentryDialog != splash || !splash.isShowing()) return;
            splash.dismiss();
            activeReentryDialog = null;
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
            if (activity.isFinishing() || activity.isDestroyed()) {
                lastAudioResult = "Suppressed: Portal activity destroyed before audio";
                saveReport(activity);
                return;
            }
            // Media is the intended stream. The ringer being silent/vibrate
            // should not disable a user-requested startup sound. Respect
            // music-stream volume and avoid hard-coding elevated output.
            AudioManager audio = (AudioManager)
                    activity.getSystemService(Context.AUDIO_SERVICE);
            if (audio != null && audio.getStreamVolume(AudioManager.STREAM_MUSIC) <= 0) {
                lastAudioResult = "Muted: media volume is zero";
                saveReport(activity);
                return;
            }
            try {
                AudioAttributes attributes = new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build();
                final MediaPlayer player = MediaPlayer.create(activity,
                        com.winlator.R.raw.charoite_crystal_startup, attributes, 0);
                if (player == null) {
                    lastAudioResult = "FAILED: MediaPlayer.create returned null";
                    saveReport(activity);
                    return;
                }
                player.setOnCompletionListener(mp -> {
                    mp.release();
                    lastAudioResult = "PASS: startup crystal chime completed";
                    saveReport(activity);
                });
                player.setOnErrorListener((mp, what, extra) -> {
                    mp.release();
                    lastAudioResult = "FAILED: MediaPlayer code " + what + "/" + extra;
                    saveReport(activity);
                    return true;
                });
                player.start();
                lastAudioResult = "STARTED: crystal chime on media stream";
                saveReport(activity);
            } catch (RuntimeException error) {
                lastAudioResult = "FAILED: " + error.getClass().getSimpleName()
                        + ": " + error.getMessage();
                saveReport(activity);
            }
        }, 300L);
    }
}
