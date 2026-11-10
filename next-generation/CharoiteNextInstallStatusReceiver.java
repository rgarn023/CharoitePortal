package com.charoitegames.core;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.os.Build;
import android.widget.Toast;

/**
 * Explicit non-exported callback from Android's PackageInstaller.
 * Never launches APK itself; only opens Android's mandatory confirmation UI.
 * No source downloads, tokens, Wine commands, files, or user-prefix access.
 */
public final class CharoiteNextInstallStatusReceiver extends BroadcastReceiver {
    public static final String ACTION="com.charoitx.action.NEXT_APK_INSTALL_STATUS";

    @Override public void onReceive(Context context,Intent intent) {
        if(intent==null || !ACTION.equals(intent.getAction())
                || !"com.charoitx".equals(context.getPackageName()))
            return;
        int status=intent.getIntExtra(PackageInstaller.EXTRA_STATUS,
                PackageInstaller.STATUS_FAILURE);
        if(status==PackageInstaller.STATUS_PENDING_USER_ACTION){
            Intent confirmation;
            if(Build.VERSION.SDK_INT>=33)
                confirmation=intent.getParcelableExtra(Intent.EXTRA_INTENT,Intent.class);
            else
                confirmation=(Intent)intent.getParcelableExtra(Intent.EXTRA_INTENT);
            CharoiteNextInAppInstaller.showInstallerConfirmation(context,confirmation);
            return;
        }
        if(status==PackageInstaller.STATUS_SUCCESS) {
            Toast.makeText(context,"Charoite Next updated successfully.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        // User cancellation and signature/version mismatch are handled by
        // Android; do NOT retry install, reset data, or fall back to old APK.
        Toast.makeText(context,
                "Android did not install the update (status "+status+"). "
                +"Your existing Charoite Next data was preserved.",
                Toast.LENGTH_LONG).show();
    }
}
