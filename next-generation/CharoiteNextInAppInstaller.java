package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Owner-triggered, token-free IN-APP APK download and Android PackageInstaller.
 * No browser/file manager or app storage write. PackageInstaller alone stages
 * the verified signed Next update; Android user confirmation is REQUIRED.
 * Never executes Wine or reads/manipulates game data, rootfs or Wine prefixes.
 */
public final class CharoiteNextInAppInstaller {
    private static final String PACKAGE = "com.charoitx";
    private static final long MIN_APK = 1024L * 1024L;
    private static final long MAX_APK = 1024L * 1024L * 1024L;
    private static final AtomicBoolean BUSY = new AtomicBoolean(false);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static volatile WeakReference<Activity> currentOwner =
            new WeakReference<>(null);

    private CharoiteNextInAppInstaller() {}

    public static void updateWithConsent(Activity activity, String downloadUrl,
            long expectedBytes, String expectedDigest, long newVersionCode) {
        if (!PACKAGE.equals(activity.getPackageName()) || activity.isFinishing()
                || activity.isDestroyed()) return;
        if (!downloadUrl.matches("https://github\\.com/rgarn023/CharoitePortal/releases/download/charoite-next-vc[1-9][0-9]{0,8}/Charoite-Next-Android\\.apk")
                || !expectedDigest.matches("sha256:[a-f0-9]{64}")
                || expectedBytes < MIN_APK || expectedBytes > MAX_APK
                || newVersionCode < 1) {
            error(activity,"Update metadata failed the trusted GitHub release check.");
            return;
        }
        long installed;
        try {
            installed=activity.getPackageManager()
                    .getPackageInfo(PACKAGE,0).getLongVersionCode();
        } catch(Exception ex) {
            error(activity,"Cannot verify the installed Charoite Next version.");
            return;
        }
        if(newVersionCode<=installed) {
            error(activity,"The selected release is not newer than installed Next.");
            return;
        }
        if(!activity.getPackageManager().canRequestPackageInstalls()){
            new AlertDialog.Builder(activity)
                .setTitle("Allow Charoite Next to install its own updates")
                .setMessage("Android requires permission to install an APK from this app. "
                    +"Enable 'Allow from this source', return to Charoite Next, then "
                    +"tap Check for updates → Update in app again. This does NOT "
                    +"uninstall, reset or touch any Wine prefix.")
                .setNegativeButton("Not now",null)
                .setPositiveButton("Open Android settings",(d,w)-> {
                    try {
                        Intent settings=new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                Uri.parse("package:"+PACKAGE));
                        activity.startActivity(settings);
                    }catch(Exception ignored) {
                        error(activity,"Unable to open Android installation settings.");
                    }
                }).show();
            return;
        }
        if(!BUSY.compareAndSet(false,true)){
            error(activity,"An in-app Charoite Next update is already in progress.");
            return;
        }
        currentOwner=new WeakReference<>(activity);
        final AtomicBoolean cancel=new AtomicBoolean(false);
        final LinearLayout panel=new LinearLayout(activity);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad=Math.round(20*activity.getResources().getDisplayMetrics().density);
        panel.setPadding(pad,pad,pad,pad);
        final TextView state=new TextView(activity);
        state.setText("Preparing verified GitHub APK download…");
        final ProgressBar bar=new ProgressBar(activity,null,
                android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);
        bar.setProgress(0);
        panel.addView(state);
        panel.addView(bar);
        final AlertDialog progress=new AlertDialog.Builder(activity)
            .setTitle("Updating Charoite Next in app")
            .setMessage("Only the official Next release will be staged. "
                +"GitHub SHA-256 and APK size must match. Android will ask "
                +"for confirmation to install over the existing app.")
            .setView(panel)
            .setNegativeButton("Cancel download",(d,w)->cancel.set(true))
            .create();
        progress.setCancelable(false);
        progress.show();
        new Thread(() -> {
            PackageInstaller installer=activity.getPackageManager().getPackageInstaller();
            PackageInstaller.Session session=null;
            HttpURLConnection connection=null;
            boolean committed=false;
            try {
                if(cancel.get())throw new InterruptedException("Download canceled");
                PackageInstaller.SessionParams params=new PackageInstaller.SessionParams(
                        PackageInstaller.SessionParams.MODE_FULL_INSTALL);
                params.setAppPackageName(PACKAGE);
                params.setSize(expectedBytes);
                if(Build.VERSION.SDK_INT>=31)
                    params.setRequireUserAction(
                            PackageInstaller.SessionParams.USER_ACTION_REQUIRED);
                int id=installer.createSession(params);
                session=installer.openSession(id);
                connection=openPinnedGitHubAsset(downloadUrl);
                int response=connection.getResponseCode();
                if(response!=HttpURLConnection.HTTP_OK)
                    throw new SecurityException("GitHub APK HTTP status "+response);
                long length=connection.getContentLengthLong();
                if(length>=0 && length!=expectedBytes)
                    throw new SecurityException("GitHub APK length differs from release metadata");
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                long count=0,prevPercent=-1;
                try(InputStream input=connection.getInputStream();
                    OutputStream staged=session.openWrite("base.apk",0,expectedBytes)){
                    byte[] bytes=new byte[128*1024];int n;
                    while((n=input.read(bytes))!=-1){
                        if(cancel.get())throw new InterruptedException("Download canceled");
                        count+=n;
                        if(count>expectedBytes || count>MAX_APK)
                            throw new SecurityException("APK exceeded signed release size");
                        digest.update(bytes,0,n);
                        staged.write(bytes,0,n);
                        final int percent=(int)(count*100/expectedBytes);
                        if(percent>=prevPercent+2){
                            prevPercent=percent;
                            MAIN.post(() -> {
                                if(progress.isShowing()){
                                    bar.setProgress(percent);
                                    state.setText("Verified download: "+percent+"%");
                                }
                            });
                        }
                    }
                    session.fsync(staged);
                }
                StringBuilder sha=new StringBuilder("sha256:");
                for(byte byteValue:digest.digest())
                    sha.append(String.format(Locale.US,"%02x",byteValue&255));
                if(count!=expectedBytes || !expectedDigest.equals(sha.toString()))
                    throw new SecurityException("APK SHA-256 mismatch — install blocked");
                if(cancel.get())throw new InterruptedException("Download canceled");
                Intent statusIntent=new Intent(activity,
                        CharoiteNextInstallStatusReceiver.class);
                statusIntent.setAction(CharoiteNextInstallStatusReceiver.ACTION);
                statusIntent.putExtra("session_id",id);
                PendingIntent callback=PendingIntent.getBroadcast(activity,id,statusIntent,
                        PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_MUTABLE);
                session.commit(callback.getIntentSender());
                committed=true;
                MAIN.post(()->{
                    if(progress.isShowing()){
                        state.setText("Verified. Opening Android installation approval…");
                        progress.dismiss();
                    }
                    if(!activity.isFinishing() && !activity.isDestroyed())
                        android.widget.Toast.makeText(activity,
                            "APK verified. Approve Android's installer to update in place.",
                            android.widget.Toast.LENGTH_LONG).show();
                });
            }catch(Exception ex){
                final String message=cancel.get() || ex instanceof InterruptedException
                        ? "Update canceled. No APK installed or app data changed."
                        : "In-app update could not complete ("+ex.getClass().getSimpleName()
                          +"). Nothing was installed. Try Check for updates again.";
                MAIN.post(()->{
                    if(progress.isShowing())progress.dismiss();
                    if(!activity.isFinishing() && !activity.isDestroyed())error(activity,message);
                });
            }finally{
                if(connection!=null)connection.disconnect();
                if(session!=null){
                    if(!committed)try{session.abandon();}catch(Exception ignored){}
                    try{session.close();}catch(Exception ignored){}
                }
                BUSY.set(false);
            }
        },"CharoiteNextVerifiedInAppApkUpdate").start();
    }

    /** HTTPS + exact domain allowlist; GitHub release assets use signed redirects. */
    private static HttpURLConnection openPinnedGitHubAsset(String location)
            throws Exception {
        URL current=new URL(location);
        for(int redirect=0;redirect<6;redirect++){
            if(!"https".equalsIgnoreCase(current.getProtocol())
                    || (current.getPort()!=-1 && current.getPort()!=443)
                    || current.getUserInfo()!=null || current.getRef()!=null)
                throw new SecurityException("Unsafe GitHub release redirect");
            String host=current.getHost().toLowerCase(Locale.US);
            if(!host.equals("github.com")
                    && !host.equals("release-assets.githubusercontent.com")
                    && !host.equals("objects.githubusercontent.com"))
                throw new SecurityException("Update redirect host not trusted");
            HttpURLConnection c=(HttpURLConnection)current.openConnection();
            c.setRequestMethod("GET");
            c.setInstanceFollowRedirects(false);
            c.setConnectTimeout(15000);
            c.setReadTimeout(30000);
            c.setRequestProperty("Accept","application/octet-stream");
            c.setRequestProperty("User-Agent","CharoiteNext-VerifiedUpdater/1");
            int status=c.getResponseCode();
            if(status==HttpURLConnection.HTTP_MOVED_PERM
                    || status==HttpURLConnection.HTTP_MOVED_TEMP
                    || status==307 || status==308){
                String next=c.getHeaderField("Location");
                c.disconnect();
                if(next==null || next.length()>4096)
                    throw new SecurityException("Invalid GitHub asset redirect");
                current=new URL(current,next);
                continue;
            }
            if(status!=HttpURLConnection.HTTP_OK){
                c.disconnect();
                throw new SecurityException("GitHub asset download refused");
            }
            return c;
        }
        throw new SecurityException("Too many GitHub release redirects");
    }

    public static void showInstallerConfirmation(android.content.Context context,
            Intent confirmation){
        if(confirmation==null)return;
        Activity owner=currentOwner.get();
        if(owner!=null && !owner.isFinishing() && !owner.isDestroyed()){
            MAIN.post(()->{
                try {owner.startActivity(confirmation);}
                catch(Exception ignored){showFallbackApproval(context,confirmation);}
            });
        } else showFallbackApproval(context,confirmation);
    }

    private static void showFallbackApproval(android.content.Context context,
            Intent confirmation){
        try {
            confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(confirmation);
        } catch(Exception ignored) {
            // System may restrict background UI. The user can open app again.
            android.widget.Toast.makeText(context,
                "Android install confirmation could not open. Return to Charoite Next.",
                android.widget.Toast.LENGTH_LONG).show();
        }
    }

    private static void error(Activity activity,String message){
        new AlertDialog.Builder(activity)
            .setTitle("Charoite Next update")
            .setMessage(message)
            .setPositiveButton("Close",null).show();
    }
}
