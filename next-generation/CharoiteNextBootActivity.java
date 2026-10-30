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
    // The live Portal is the session: Home/Recents do not destroy it.
    // A genuine Activity finish or a killed process permits boot again.
    private static volatile java.lang.ref.WeakReference<Activity> currentPortal =
            new java.lang.ref.WeakReference<>(null);
    private static final AtomicBoolean COLD_ARRIVAL_SOUND_PENDING =
            new AtomicBoolean(false);
    private static final Handler OVERLAY_HANDLER = new Handler(Looper.getMainLooper());
    private static final String LAST_BOOT_VERSION = "last_boot_version";
    private static FrameLayout activeColdFallback;
    private static Activity coldFallbackOwner;

    private static final String STARTUP_PREFS = "charoite_next_startup_diagnostics";
    private static volatile String lastLifecycleEvent = "Not yet observed";
    private static volatile String lastAudioResult = "Not yet attempted";

    /** First Portal creation, not a foreground-resume event. */
    public static void installReentryTracker(Activity portal) {
        currentPortal = new java.lang.ref.WeakReference<>(portal);
    }
    private static boolean hasLivePortalSession() {
        Activity portal = currentPortal.get();
        return portal != null && !portal.isFinishing() && !portal.isDestroyed();
    }

    private static boolean hasLivePortalInSameTask(Activity launcher) {
        Activity portal = currentPortal.get();
        return portal != null && !portal.isFinishing() && !portal.isDestroyed()
                && portal.getTaskId() == launcher.getTaskId();
    }

    private static long installedVersion(Activity activity) {
        try {
            return activity.getPackageManager()
                    .getPackageInfo(activity.getPackageName(), 0).getLongVersionCode();
        } catch (Exception ignored) {
            return -1L;
        }
    }

    private static void markBootShown(Activity activity) {
        activity.getSharedPreferences(STARTUP_PREFS, Context.MODE_PRIVATE).edit()
                .putLong(LAST_BOOT_VERSION, installedVersion(activity)).apply();
    }

    /** Samsung can recreate Portal directly as task root after an APK update,
     * bypassing the launcher Activity. This handles only actual creation;
     * switching apps invokes onResume and must never show this fallback. */
    public static void onPortalCreated(Activity portal, Bundle state) {
        Activity previous = currentPortal.get();
        boolean differentLivePortal = previous != null && previous != portal
                && !previous.isFinishing() && !previous.isDestroyed();
        installReentryTracker(portal);
        Intent intent = portal.getIntent();
        if (intent != null && intent.getBooleanExtra(EXTRA_PLAY_CHIME, false)) return;
        if (!portal.isTaskRoot() || differentLivePortal || portal.isChangingConfigurations())
            return;
        long version = installedVersion(portal);
        long seen = portal.getSharedPreferences(STARTUP_PREFS, Context.MODE_PRIVATE)
                .getLong(LAST_BOOT_VERSION, -1L);
        if (state != null && seen == version) return;
        lastLifecycleEvent = "Fresh Portal created directly; cold boot fallback";
        saveReport(portal);
        showColdPortalFallback(portal, 0);
    }

    private static void showColdPortalFallback(Activity portal, int attempt) {
        portal.getWindow().getDecorView().postDelayed(() -> {
            if (portal.isFinishing() || portal.isDestroyed()) return;
            FrameLayout content = portal.findViewById(android.R.id.content);
            if (content == null || !content.isAttachedToWindow()) {
                if (attempt < 12) showColdPortalFallback(portal, attempt + 1);
                else {
                    lastLifecycleEvent = "Fresh Portal boot fallback could not attach";
                    saveReport(portal);
                }
                return;
            }
            if (activeColdFallback != null) return;
            FrameLayout splash = createBootView(portal);
            splash.setClickable(true);
            splash.setFocusable(true);
            splash.setElevation(density(portal, 64));
            content.addView(splash, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            splash.bringToFront();
            coldFallbackOwner = portal;
            activeColdFallback = splash;
            markBootShown(portal);
            lastLifecycleEvent = "Direct fresh Portal fallback shown for five seconds";
            saveReport(portal);
            OVERLAY_HANDLER.postDelayed(() -> {
                if (coldFallbackOwner != portal || activeColdFallback != splash) return;
                activeColdFallback = null;
                coldFallbackOwner = null;
                if (splash.getParent() instanceof ViewGroup)
                    ((ViewGroup) splash.getParent()).removeView(splash);
                if (!portal.isFinishing() && !portal.isDestroyed())
                    playCrystalChime(portal);
            }, BOOT_DURATION_MS);
        }, attempt == 0 ? 80L : 160L);
    }
    public static void notePortalDestroyed(Activity portal) {
        if (coldFallbackOwner == portal) {
            if (activeColdFallback != null
                    && activeColdFallback.getParent() instanceof ViewGroup)
                ((ViewGroup) activeColdFallback.getParent()).removeView(activeColdFallback);
            activeColdFallback = null;
            coldFallbackOwner = null;
        }
        if (currentPortal.get() == portal) {
            currentPortal.clear();
            lastLifecycleEvent = "Portal destroyed; new launch can boot";
            saveReport(portal);
        }
    }
    /** Never display a splash on an existing Portal's onResume. */
    public static void onPortalResumed(Activity portal) {
        currentPortal = new java.lang.ref.WeakReference<>(portal);
        playArrivalChimeIfRequested(portal);
    }
    /** First cold-arrival audio is allowed to wait for window focus. */
    public static void onPortalWindowFocusChanged(Activity portal, boolean focused) {
        if (focused) playPendingColdArrivalIfReady(portal);
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
                + "Splash art: approved gateway with black outside corners removed\n"
                + "Boot: once per genuine launch, never on app switching\n"
                + "Boot duration: 5000 ms\n"
                + "Last lifecycle: " + prefs.getString("last_event", lastLifecycleEvent) + "\n"
                + "Portal session live: " + hasLivePortalSession() + "\n"
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


    /** Source-faithful art with transparent corners and a full-screen
     * violet continuation, never a black square around the icon. */
    private static FrameLayout createBootView(Activity activity) {
        FrameLayout boot = new FrameLayout(activity);
        boot.setBackgroundColor(Color.rgb(43, 18, 83));
        boot.setContentDescription("Charoite Core starting");
        ImageView backdrop = new ImageView(activity);
        backdrop.setImageResource(com.winlator.R.drawable.charoite_next_boot_backdrop);
        backdrop.setScaleType(ImageView.ScaleType.CENTER_CROP);
        boot.addView(backdrop, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        LinearLayout emblem = new LinearLayout(activity);
        emblem.setOrientation(LinearLayout.VERTICAL);
        emblem.setGravity(Gravity.CENTER);
        emblem.setPadding(density(activity, 20), density(activity, 24),
                density(activity, 20), density(activity, 24));

        ImageView icon = new ImageView(activity);
        // Exact full-resolution user-supplied asset; also installed as the launcher icon.
        icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_unframed);
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

    @Override public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        // If the Portal already exists, launcher/Recents must not restart
        // the visual sequence or crystal sound just for task switching.
        if (hasLivePortalInSameTask(this)) {
            lastLifecycleEvent = "Already running in same task; boot skipped";
            saveReport(this);
            Intent portal = new Intent(this, com.winlator.TouhouEntryActivity.class);
            portal.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(portal);
            finish();
            return;
        }
        markBootShown(this);
        getWindow().setStatusBarColor(Color.rgb(43, 18, 83));
        getWindow().setNavigationBarColor(Color.rgb(43, 18, 83));
        setContentView(createBootView(this));

        // Single cold-launch delay, not a blocking sleep or a Wine startup delay.
        openMain = () -> {
            if (completed || isFinishing() || isDestroyed()) return;
            completed = true;
            Intent main = new Intent(this, com.winlator.TouhouEntryActivity.class);
            main.putExtra(EXTRA_PLAY_CHIME, true);
            startActivity(main);
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            // Keep this completed launcher beneath Portal as the task root.
            // Finishing here caused Android to restore Portal directly forever.
        };
        handler.postDelayed(openMain, BOOT_DURATION_MS);
    }

    @Override protected void onResume() {
        super.onResume();
        if (completed) {
            // Portal was genuinely exited, not merely backgrounded via Home.
            lastLifecycleEvent = "Portal exited; launcher task root closed";
            saveReport(this);
            finish();
        }
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
