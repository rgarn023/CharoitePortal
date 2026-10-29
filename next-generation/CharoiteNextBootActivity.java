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
    private static final AtomicBoolean SUPPRESS_NEXT_RESTART = new AtomicBoolean(false);
    private static final AtomicBoolean COLD_ARRIVAL_SOUND_PENDING = new AtomicBoolean(false);
    private static final Handler OVERLAY_HANDLER = new Handler(Looper.getMainLooper());
    private static FrameLayout activeReentryOverlay;
    private static Activity activeOverlayOwner;
    private static Runnable activeOverlayTimeout;
    private static int previousStatusBarColor;
    private static int previousNavigationBarColor;

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
                    SUPPRESS_NEXT_RESTART.set(true);
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
                if (a instanceof com.winlator.TouhouEntryActivity)
                    removeWarmOverlay(a, false);
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
        SUPPRESS_NEXT_RESTART.set(false);
        REENTRY_NEEDED.set(true);
        lastLifecycleEvent = "User leave hint received";
        saveReport(portal);
    }

    /** Fallback for split-screen or launcher paths that only pause the Portal.
     * Internal navigation is excluded when its destination starts. */
    public static void notePortalPaused(Activity portal) {
        removeWarmOverlay(portal, false);
        if (portal.isChangingConfigurations()) {
            SUPPRESS_NEXT_RESTART.set(true);
            REENTRY_NEEDED.set(false);
            lastLifecycleEvent = "Configuration transition; suppress boot replay";
        } else {
            REENTRY_NEEDED.set(true);
            lastLifecycleEvent = "Portal paused; next foreground entry will play boot";
        }
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
            playPendingColdArrivalIfReady(portal);
        } else if (activeReentryOverlay == null) {
            lastLifecycleEvent = "Portal window lost focus";
            saveReport(portal);
        }
    }

    /** Android can restart an existing Portal task from the launcher without
     * sending a second ACTION_MAIN intent. The previous implementation only
     * listened for focus and an onPause flag, which missed this case. */
    public static void onPortalRestart(Activity portal) {
        // Lifecycle onRestart is informational. Never consume or clear a
        // pending Home-return request here: that previously suppressed boot
        // after the first launch on Samsung One UI.
        lastLifecycleEvent = "Portal onRestart; awaiting foreground onResume";
        saveReport(portal);
    }

    /** Every actual Portal resume is a potential user launch. Android may
     * bring an existing task to the front without sending ACTION_MAIN,
     * onRestart, or a new focus callback. The one-shot cold-start marker
     * prevents double boot on the first entry; internal Charoite windows and
     * configuration changes use a suppression token consumed here, exactly
     * once, rather than leaving it stuck for future Home launches. */
    public static void onPortalResumed(Activity portal) {
        Intent intent = portal.getIntent();
        if (intent != null && intent.getBooleanExtra(EXTRA_PLAY_CHIME, false)) {
            REENTRY_NEEDED.set(false);
            SUPPRESS_NEXT_RESTART.set(false);
            lastLifecycleEvent = "First Portal arrival after five-second cold boot";
            saveReport(portal);
            playArrivalChimeIfRequested(portal);
            return;
        }
        boolean internalReturn = SUPPRESS_NEXT_RESTART.getAndSet(false);
        boolean explicitHomeOrLauncher = REENTRY_NEEDED.get();
        if (internalReturn && !explicitHomeOrLauncher) {
            lastLifecycleEvent = "Internal activity/configuration return: boot not repeated";
            saveReport(portal);
            return;
        }
        // Last-resort onResume replay deliberately covers Samsung task
        // restoration even if onPause/onStop/onNewIntent did not signal it.
        REENTRY_NEEDED.set(true);
        lastLifecycleEvent = "Portal resumed from launcher/background; boot requested";
        saveReport(portal);
        showOnBackgroundReentryIfNeeded(portal);
    }

    /** Document pickers are external activities, but returning from a picker
     * is NOT a new Portal launch. */
    public static void noteDocumentPickerReturn(Activity portal) {
        SUPPRESS_NEXT_RESTART.set(true);
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
                + "Splash art: exact user-supplied 1536px crystalline gateway\n"
                + "Replay: foreground overlay on restart/resume or launcher intent\n"
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


    /** Icon-matched 1536px artwork and a real five-second progress bar.
     * Same presentation for cold launch and warm return from the launcher. */
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
        // Exact full-resolution user-supplied asset; also installed as the launcher icon.
        icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_scene);
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setContentDescription("Charoite crystal portal");
        emblem.addView(icon, new LinearLayout.LayoutParams(
                density(activity, 278), density(activity, 278)));

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

    /** Remove a previous warm overlay before internal navigation, Home, or
     * Activity teardown. The underlying Portal and Windows sessions survive. */
    private static void removeWarmOverlay(Activity activity, boolean playChime) {
        if (activeOverlayOwner != activity || activeReentryOverlay == null) return;
        if (activeOverlayTimeout != null)
            OVERLAY_HANDLER.removeCallbacks(activeOverlayTimeout);
        FrameLayout overlay = activeReentryOverlay;
        activeReentryOverlay = null;
        activeOverlayOwner = null;
        activeOverlayTimeout = null;
        if (overlay.getParent() instanceof ViewGroup)
            ((ViewGroup) overlay.getParent()).removeView(overlay);
        if (!activity.isFinishing() && !activity.isDestroyed()) {
            activity.getWindow().setStatusBarColor(previousStatusBarColor);
            activity.getWindow().setNavigationBarColor(previousNavigationBarColor);
            if (playChime) playCrystalChime(activity);
        }
    }

    /** Foreground reuse uses an ordinary content overlay, NOT a new Dialog
     * Window. Samsung may not give a Dialog a valid window token while
     * onResume() is executing; a decor overlay has no such race. */
    public static void showOnBackgroundReentryIfNeeded(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        activity.getWindow().getDecorView().post(() -> {
            if (activity.isFinishing() || activity.isDestroyed()) return;
            if (activeReentryOverlay != null && activeOverlayOwner == activity)
                return;
            if (!REENTRY_NEEDED.get()) return;
            FrameLayout content = activity.findViewById(android.R.id.content);
            if (content == null || !content.isAttachedToWindow()) {
                lastLifecycleEvent = "Portal content not attached; replay still pending";
                saveReport(activity);
                return;
            }
            if (!REENTRY_NEEDED.compareAndSet(true, false)) return;
            FrameLayout overlay = createBootView(activity);
            overlay.setClickable(true);
            overlay.setFocusable(true);
            overlay.setElevation(density(activity, 64));
            activeReentryOverlay = overlay;
            activeOverlayOwner = activity;
            previousStatusBarColor = activity.getWindow().getStatusBarColor();
            previousNavigationBarColor = activity.getWindow().getNavigationBarColor();
            activity.getWindow().setStatusBarColor(Color.rgb(13, 8, 30));
            activity.getWindow().setNavigationBarColor(Color.rgb(13, 8, 30));
            content.addView(overlay, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            overlay.bringToFront();
            lastLifecycleEvent = "Warm Portal launch; five-second overlay displayed";
            saveReport(activity);
            activeOverlayTimeout = () -> removeWarmOverlay(activity, true);
            OVERLAY_HANDLER.postDelayed(activeOverlayTimeout, BOOT_DURATION_MS);
        });
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

    /** The cold boot finishes before the Portal starts, but Android may not
     * grant the new Portal window audio playback immediately in onResume.
     * Queue the first crystal arrival until the window is visible. The
     * fallback post also handles Samsung builds which omit focus callbacks. */
    public static void playArrivalChimeIfRequested(Activity activity) {
        Intent intent = activity.getIntent();
        if (intent == null || !intent.getBooleanExtra(EXTRA_PLAY_CHIME, false))
            return;
        intent.removeExtra(EXTRA_PLAY_CHIME);
        COLD_ARRIVAL_SOUND_PENDING.set(true);
        lastAudioResult = "QUEUED: cold arrival sound waiting for visible Portal";
        saveReport(activity);
        activity.getWindow().getDecorView().postDelayed(
                () -> playPendingColdArrivalIfReady(activity), 900L);
    }

    private static void playPendingColdArrivalIfReady(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        if (!COLD_ARRIVAL_SOUND_PENDING.compareAndSet(true, false)) return;
        lastAudioResult = "Portal visible: starting first-launch crystal sound";
        saveReport(activity);
        playCrystalChime(activity);
    }

    /** Play directly using the generated PCM WAV. This avoids depending on
     * MediaPlayer's first-use decoder readiness after APK installation.
     * Existing MediaPlayer support is the fallback if AudioTrack fails. */
    private static android.media.AudioTrack activeCrystalAudioTrack;
    private static android.media.MediaPlayer activeCrystalMediaPlayer;

    private static void playCrystalChime(Activity activity) {
        activity.getWindow().getDecorView().postDelayed(() -> {
            if (activity.isFinishing() || activity.isDestroyed()) {
                lastAudioResult = "Suppressed: Portal destroyed before startup audio";
                saveReport(activity);
                return;
            }
            AudioManager audio = (AudioManager)
                    activity.getSystemService(Context.AUDIO_SERVICE);
            if (audio != null && audio.getStreamVolume(AudioManager.STREAM_MUSIC) <= 0) {
                lastAudioResult = "Muted: media volume is zero";
                saveReport(activity);
                return;
            }
            AudioAttributes attributes = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build();
            try {
                if (activeCrystalAudioTrack != null) {
                    activeCrystalAudioTrack.pause();
                    activeCrystalAudioTrack.flush();
                    activeCrystalAudioTrack.release();
                    activeCrystalAudioTrack = null;
                }
                // The generated audio is PCM 44.1kHz, mono, 16-bit in a
                // standard 44-byte RIFF WAV header (validated by CI).
                byte[] wav;
                try (java.io.InputStream input = activity.getResources()
                        .openRawResource(com.winlator.R.raw.charoite_crystal_startup);
                     java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream()) {
                    byte[] block = new byte[8192];
                    int count;
                    while ((count = input.read(block)) != -1)
                        output.write(block, 0, count);
                    wav = output.toByteArray();
                }
                if (wav.length < 48 || wav[0] != 'R' || wav[1] != 'I'
                        || wav[2] != 'F' || wav[3] != 'F'
                        || wav[8] != 'W' || wav[9] != 'A'
                        || wav[10] != 'V' || wav[11] != 'E'
                        || wav[36] != 'd' || wav[37] != 'a'
                        || wav[38] != 't' || wav[39] != 'a')
                    throw new IllegalStateException("Invalid PCM WAV startup resource");
                int length = wav.length - 44;
                android.media.AudioFormat format = new android.media.AudioFormat.Builder()
                        .setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(44100)
                        .setChannelMask(android.media.AudioFormat.CHANNEL_OUT_MONO)
                        .build();
                android.media.AudioTrack track = new android.media.AudioTrack.Builder()
                        .setAudioAttributes(attributes)
                        .setAudioFormat(format)
                        .setBufferSizeInBytes(length)
                        .setTransferMode(android.media.AudioTrack.MODE_STATIC)
                        .build();
                if (track.getState() != android.media.AudioTrack.STATE_INITIALIZED) {
                    track.release();
                    throw new IllegalStateException("AudioTrack not initialized");
                }
                int written = track.write(wav, 44, length);
                if (written != length) {
                    track.release();
                    throw new IllegalStateException("PCM write incomplete: " + written);
                }
                activeCrystalAudioTrack = track;
                track.play();
                lastAudioResult = "STARTED: direct PCM crystal sound (" + written + " bytes)";
                saveReport(activity);
                OVERLAY_HANDLER.postDelayed(() -> {
                    if (activeCrystalAudioTrack == track) {
                        track.stop();
                        track.release();
                        activeCrystalAudioTrack = null;
                        lastAudioResult = "PASS: direct PCM crystal sound completed";
                        saveReport(activity);
                    }
                }, 4600L);
            } catch (Exception pcmFailure) {
                lastAudioResult = "PCM failed: " + pcmFailure.getClass().getSimpleName()
                        + "; trying MediaPlayer";
                saveReport(activity);
                try {
                    if (activeCrystalMediaPlayer != null) {
                        activeCrystalMediaPlayer.release();
                        activeCrystalMediaPlayer = null;
                    }
                    android.media.MediaPlayer player = android.media.MediaPlayer.create(activity,
                            com.winlator.R.raw.charoite_crystal_startup, attributes, 0);
                    if (player == null) throw new IllegalStateException("MediaPlayer.create null");
                    activeCrystalMediaPlayer = player;
                    player.setOnCompletionListener(mp -> {
                        mp.release();
                        if (activeCrystalMediaPlayer == mp) activeCrystalMediaPlayer = null;
                        lastAudioResult = "PASS: MediaPlayer crystal sound completed";
                        saveReport(activity);
                    });
                    player.setOnErrorListener((mp, what, extra) -> {
                        mp.release();
                        if (activeCrystalMediaPlayer == mp) activeCrystalMediaPlayer = null;
                        lastAudioResult = "FAILED: MediaPlayer " + what + "/" + extra;
                        saveReport(activity);
                        return true;
                    });
                    player.start();
                    lastAudioResult = "STARTED: fallback MediaPlayer crystal sound";
                    saveReport(activity);
                } catch (Exception fallbackFailure) {
                    lastAudioResult = "FAILED: PCM " + pcmFailure.getClass().getSimpleName()
                            + ", MediaPlayer " + fallbackFailure.getClass().getSimpleName();
                    saveReport(activity);
                }
            }
        }, 300L);
    }

}
