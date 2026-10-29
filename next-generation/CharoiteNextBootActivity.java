package com.charoitegames.core;

import android.app.Activity;
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
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable openMain;
    private boolean completed;

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        getWindow().setStatusBarColor(Color.rgb(13, 8, 30));
        getWindow().setNavigationBarColor(Color.rgb(13, 8, 30));
        FrameLayout boot = new FrameLayout(this);
        boot.setBackgroundColor(Color.rgb(13, 8, 30));
        boot.setContentDescription("Charoite Core starting");
        LinearLayout emblem = new LinearLayout(this);
        emblem.setOrientation(LinearLayout.VERTICAL);
        emblem.setGravity(Gravity.CENTER);
        emblem.setPadding(dp(20), dp(24), dp(20), dp(24));

        ImageView icon = new ImageView(this);
        icon.setImageResource(com.winlator.R.drawable.charoite_portal_icon);
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setContentDescription("Charoite Core icon");
        emblem.addView(icon, new LinearLayout.LayoutParams(dp(236), dp(236)));

        TextView title = new TextView(this);
        title.setText("CHAROITE CORE");
        title.setGravity(Gravity.CENTER);
        title.setTextColor(Color.WHITE);
        title.setTextSize(23);
        title.setLetterSpacing(0.13f);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams titleParams =
                new LinearLayout.LayoutParams(-2, -2);
        titleParams.topMargin = dp(20);
        emblem.addView(title, titleParams);

        TextView subtitle = new TextView(this);
        subtitle.setText("NEXT");
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setTextColor(Color.rgb(198, 180, 240));
        subtitle.setTextSize(12);
        subtitle.setLetterSpacing(0.34f);
        LinearLayout.LayoutParams subtitleParams =
                new LinearLayout.LayoutParams(-2, -2);
        subtitleParams.topMargin = dp(6);
        emblem.addView(subtitle, subtitleParams);

        FrameLayout.LayoutParams emblemParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        boot.addView(emblem, emblemParams);
        setContentView(boot);

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
        intent.removeExtra(EXTRA_PLAY_CHIME); // never repeat after rotation/resume
        activity.getWindow().getDecorView().postDelayed(() -> {
            if (activity.isFinishing() || activity.isDestroyed() || !activity.hasWindowFocus())
                return;
            AudioManager audio = (AudioManager)
                    activity.getSystemService(Activity.AUDIO_SERVICE);
            if (audio != null && audio.getRingerMode() == AudioManager.RINGER_MODE_SILENT)
                return; // respect phone silent setting
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
                // Never crash the launcher merely because audio is unavailable.
            }
        }, 220L);
    }
}
