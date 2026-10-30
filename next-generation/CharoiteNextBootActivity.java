package com.charoitegames.core;

import android.app.Activity;
import android.app.Application;
import android.app.Dialog;
import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.os.SystemClock;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
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
    // Prepared during onCreate; installed synchronously in onPostCreate,
    // before Android draws the Portal's first frame.
    private static Activity pendingColdFallbackOwner;

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
        // Do not post/delay this splash: the prior 80ms delay allowed the
        // underlying main screen to render and visibly flash before boot.
        // The UI is finished in Activity.onCreate, so onPostCreate is the
        // earliest safe point to cover all of its content before first draw.
        pendingColdFallbackOwner = portal;
        lastLifecycleEvent = "Direct cold boot prepared before first frame";
        saveReport(portal);
    }

    /** Called synchronously by Portal.onPostCreate, before onStart/onResume
     * and before Android's first visible frame. Adding to android.R.id.content
     * here avoids the main-screen flash caused by Handler.postDelayed. */
    public static void onPortalPostCreated(Activity portal) {
        if (pendingColdFallbackOwner != portal) return;
        pendingColdFallbackOwner = null;
        if (portal.isFinishing() || portal.isDestroyed()) return;
        FrameLayout content = portal.findViewById(android.R.id.content);
        if (content == null) {
            lastLifecycleEvent = "Direct cold boot missing Android content root";
            saveReport(portal);
            return;
        }
        if (activeColdFallback != null) return;
        FrameLayout splash = createBootView(portal);
        splash.setClickable(true);
        splash.setFocusable(true);
        splash.setElevation(density(portal, 64));
        // The content need not be attached to the window yet. It will attach
        // with this splash already on top of the Portal UI.
        content.addView(splash, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        splash.bringToFront();
        coldFallbackOwner = portal;
        activeColdFallback = splash;
        markBootShown(portal);
        lastLifecycleEvent = "Cold fallback present before first Portal draw";
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
    }
    public static void notePortalDestroyed(Activity portal) {
        if (pendingColdFallbackOwner == portal) pendingColdFallbackOwner = null;
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


    /** Five-second cinematic Charoite reveal, no loading bar.
     * The full content area shows the approved portal, unframed and enlarged
     * as far as possible without cropping away its crystal ring. The matching
     * violet backdrop fills the remaining tall-phone or DeX letterbox area.
     * Neither image is replaced or repainted; glow is a transparent overlay.
     */
    private static FrameLayout createBootView(Activity activity) {
        FrameLayout boot = new FrameLayout(activity);
        boot.setBackgroundColor(Color.rgb(43, 18, 83));
        boot.setContentDescription("Charoite crystal portal awakening");
        ImageView backdrop = new ImageView(activity);
        backdrop.setImageResource(com.winlator.R.drawable.charoite_next_boot_backdrop);
        backdrop.setScaleType(ImageView.ScaleType.CENTER_CROP);
        boot.addView(backdrop, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        FrameLayout scene = new FrameLayout(activity);
        boot.addView(scene, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        ImageView artwork = new ImageView(activity);
        artwork.setImageResource(com.winlator.R.drawable.charoite_next_boot_unframed);
        // Avoid CENTER_CROP on the square portal: on a tall phone it removes
        // the entire left/right crystalline arch. FIT_CENTER preserves it.
        artwork.setScaleType(ImageView.ScaleType.FIT_CENTER);
        scene.addView(artwork, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        // Gentle glow passes through the center, isolated little glints light
        // crystal tips, and the artwork breathes by only 3.5 percent.
        CrystalShimmer shimmer = new CrystalShimmer(activity);
        shimmer.setClickable(false);
        shimmer.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        scene.addView(shimmer, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        AnimatorSet slowReveal = new AnimatorSet();
        slowReveal.playTogether(
                ObjectAnimator.ofFloat(scene, "scaleX", 1.0f, 1.035f),
                ObjectAnimator.ofFloat(scene, "scaleY", 1.0f, 1.035f));
        slowReveal.setDuration(BOOT_DURATION_MS);
        slowReveal.setInterpolator(new AccelerateDecelerateInterpolator());
        slowReveal.start();
        return boot;
    }

    /** Original Android-canvas particle layer, no external artwork or video.
     * Coordinates are relative to the original square picture contained
     * inside the screen, so glow aligns on portrait and landscape displays.
     * Only eight small, fixed crystal-tip sparkles are used, not a busy ring.
     * Invalidations stop after BOOT_DURATION_MS; no background animation.
     */
    private static final class CrystalShimmer extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private long firstFrameAt = -1L;
        private static final float[][] CRYSTAL_TIPS = {
                {.50f, .072f}, {.715f, .312f}, {.256f, .377f},
                {.678f, .793f}, {.348f, .766f}, {.521f, .893f},
                {.767f, .551f}, {.439f, .273f}
        };

        CrystalShimmer(Context context) {
            super(context);
            setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            if (firstFrameAt < 0L) firstFrameAt = SystemClock.uptimeMillis();
            final long elapsed = Math.max(0L,
                    SystemClock.uptimeMillis() - firstFrameAt);
            final float t = Math.min(elapsed / 1000f, BOOT_DURATION_MS / 1000f);
            final float side = Math.min(getWidth(), getHeight());
            if (side <= 0f) return;
            final float left = (getWidth() - side) * .5f;
            final float top = (getHeight() - side) * .5f;
            final float glow = .5f + .5f *
                    (float)Math.sin(2.0 * Math.PI * t / 3.6f - .7f);

            // Diffuse purple radiance centered inside the crescent gateway.
            radialGlow(canvas, left + side * .505f, top + side * .46f,
                    side * .31f, (int)(14 + 19 * glow));
            // A quiet, icy-white aura around the main upper crystal tip.
            radialGlow(canvas, left + side * .50f, top + side * .080f,
                    side * .14f, (int)(18 + 22 * glow));

            final float unit = Math.max(2f, side * .007f);
            for (int i = 0; i < CRYSTAL_TIPS.length; i++) {
                float phase = i * 1.77f + .31f;
                float wave = (float)Math.sin(t * (2.25f + i * .10f) + phase);
                float twinkle = (float)Math.pow(Math.max(0f, wave), 5);
                if (twinkle < .08f) continue;
                float x = left + side * CRYSTAL_TIPS[i][0];
                float y = top + side * CRYSTAL_TIPS[i][1];
                float radius = unit * (.95f + 1.25f * twinkle);
                int alpha = (int)(155 * twinkle);
                paint.setShader(new RadialGradient(x, y, radius * 3.2f,
                        new int[]{Color.argb(alpha, 240, 215, 255),
                                Color.TRANSPARENT}, null, Shader.TileMode.CLAMP));
                paint.setStyle(Paint.Style.FILL);
                canvas.drawCircle(x, y, radius * 3.2f, paint);
                paint.setShader(null);
                paint.setColor(Color.argb((int)(220 * twinkle), 255, 248, 255));
                paint.setStrokeWidth(Math.max(.8f, side * .0012f));
                paint.setStrokeCap(Paint.Cap.ROUND);
                canvas.drawLine(x - radius * 2.0f, y, x + radius * 2.0f, y, paint);
                canvas.drawLine(x, y - radius * 2.7f, x, y + radius * 2.7f, paint);
            }
            paint.setShader(null);
            if (elapsed < BOOT_DURATION_MS && isAttachedToWindow())
                postInvalidateOnAnimation();
        }

        private void radialGlow(Canvas canvas, float x, float y,
                float radius, int alpha) {
            paint.setStyle(Paint.Style.FILL);
            paint.setShader(new RadialGradient(x, y, radius,
                    new int[]{Color.argb(alpha, 196, 105, 255),
                            Color.argb(alpha / 3, 166, 82, 242),
                            Color.TRANSPARENT},
                    new float[]{0f, .43f, 1f}, Shader.TileMode.CLAMP));
            canvas.drawCircle(x, y, radius, paint);
            paint.setShader(null);
        }

        @Override protected void onDetachedFromWindow() {
            firstFrameAt = -1L;
            super.onDetachedFromWindow();
        }
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
