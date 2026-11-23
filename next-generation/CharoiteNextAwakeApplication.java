package com.charoitegames.core;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.view.Window;
import android.view.WindowManager;

/**
 * Experimental Meteorite Alpha only: keep the display awake while one of this
 * application's activities is visible/resumed. Works for Portal, installers,
 * gameplay, and the separate Wine29 display process.
 *
 * Do not hold a PARTIAL_WAKE_LOCK or change system sleep settings. This flag
 * is local to each window; pausing releases it so Home/background/screen-off
 * are controlled by Android and the user as usual.
 */
public final class CharoiteNextAwakeApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        registerActivityLifecycleCallbacks(new ActivityLifecycleCallbacks() {
            @Override
            public void onActivityCreated(Activity activity, Bundle state) {}

            @Override
            public void onActivityStarted(Activity activity) {}

            @Override
            public void onActivityResumed(Activity activity) {
                Window window = activity.getWindow();
                if (window != null) {
                    window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                }
            }

            @Override
            public void onActivityPaused(Activity activity) {
                Window window = activity.getWindow();
                if (window != null) {
                    window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                }
            }

            @Override
            public void onActivityStopped(Activity activity) {}

            @Override
            public void onActivitySaveInstanceState(Activity activity, Bundle outState) {}

            @Override
            public void onActivityDestroyed(Activity activity) {}
        });
    }
}
