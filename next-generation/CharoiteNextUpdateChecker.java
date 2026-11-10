package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Experimental Next-only read-only startup update check.
 * Reads PUBLIC GitHub Releases metadata; never reads Wine scratch or downloads,
 * executes, installs or deletes an APK automatically. Android user approves upgrade.
 */
public final class CharoiteNextUpdateChecker {
    private static final String PACKAGE = "com.charoitx";
    private static final String RELEASE_API =
            "https://api.github.com/repos/rgarn023/CharoitePortal/releases?per_page=30";
    private static final String RELEASE_BASE =
            "https://github.com/rgarn023/CharoitePortal/releases/download/";
    private static final String TAG_PREFIX = "charoite-next-vc";
    private static final String APK_NAME = "Charoite-Next-Android.apk";
    private static final AtomicBoolean CHECKING = new AtomicBoolean(false);
    private CharoiteNextUpdateChecker() {}

    private static final class Available {
        final long versionCode;
        final String versionLabel, downloadUrl, sha256;
        Available(long code, String label, String url, String digest) {
            versionCode=code;versionLabel=label;downloadUrl=url;sha256=digest;
        }
    }

    private static long installedVersionCode(Activity activity) {
        try {
            PackageInfo p=activity.getPackageManager().getPackageInfo(
                    activity.getPackageName(),0);
            return p.getLongVersionCode();
        } catch (Exception ignored) { return -1L; }
    }

    /** No authentication, no redirects, bounded 256 KiB and 10 seconds. */
    private static JSONArray fetchPublicReleases() throws Exception {
        URL url=new URL(RELEASE_API);
        if (!"https".equals(url.getProtocol())
                || !"api.github.com".equals(url.getHost()))
            throw new SecurityException("Untrusted update endpoint");
        HttpURLConnection c=(HttpURLConnection)url.openConnection();
        try {
            c.setRequestMethod("GET");
            c.setInstanceFollowRedirects(false);
            c.setConnectTimeout(8000);
            c.setReadTimeout(10000);
            c.setRequestProperty("Accept","application/vnd.github+json");
            c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");
            if (c.getResponseCode()!=200)
                throw new IllegalStateException("GitHub releases unavailable");
            ByteArrayOutputStream raw=new ByteArrayOutputStream();
            try(InputStream input=c.getInputStream()) {
                byte[] bytes=new byte[8192]; int n;
                while((n=input.read(bytes))!=-1) {
                    if(raw.size()+n>256*1024)
                        throw new SecurityException("Update metadata over size cap");
                    raw.write(bytes,0,n);
                }
            }
            return new JSONArray(raw.toString(StandardCharsets.UTF_8.name()));
        } finally {c.disconnect();}
    }

    private static Available newestNextRelease(JSONArray releases) {
        Available newest=null;
        for(int i=0;i<releases.length() && i<30;i++) {
            JSONObject r=releases.optJSONObject(i);
            if(r==null || r.optBoolean("draft",true) || r.optBoolean("prerelease",true))
                continue;
            String tag=r.optString("tag_name","");
            if(!tag.matches("charoite-next-vc[1-9][0-9]{0,8}"))continue;
            long code;
            try{code=Long.parseLong(tag.substring(TAG_PREFIX.length()));}
            catch(NumberFormatException e){continue;}
            JSONArray assets=r.optJSONArray("assets");
            if(assets==null)continue;
            for(int k=0;k<assets.length() && k<16;k++){
                JSONObject asset=assets.optJSONObject(k);
                if(asset==null || !APK_NAME.equals(asset.optString("name"))
                        || !"uploaded".equals(asset.optString("state"))
                        || asset.optLong("size",0)<1024*1024
                        || asset.optLong("size",0)>1024L*1024L*1024L)
                    continue;
                String expected=RELEASE_BASE+tag+"/"+APK_NAME;
                if(!expected.equals(asset.optString("browser_download_url","")))continue;
                String digest=asset.optString("digest","");
                if(!digest.matches("sha256:[a-f0-9]{64}"))continue;
                if(newest==null || code>newest.versionCode) {
                    String label=r.optString("name","");
                    if(label.length()>90 || !label.matches("[A-Za-z0-9 ._\\-]+"))
                        label="Charoite Next build "+code;
                    newest=new Available(code,label,expected,digest);
                }
            }
        }
        return newest;
    }

    private static void check(Activity activity, boolean manual) {
        if(!PACKAGE.equals(activity.getPackageName()) || !CHECKING.compareAndSet(false,true))
            return;
        long installed=installedVersionCode(activity);
        if(installed<1){CHECKING.set(false);return;}
        new Thread(() -> {
            Available newest=null;
            boolean failed=false;
            try {newest=newestNextRelease(fetchPublicReleases());}
            catch(Exception ignored) {failed=true;}
            final Available result=newest;
            final boolean error=failed;
            new Handler(Looper.getMainLooper()).postDelayed(() -> {
                CHECKING.set(false);
                if(activity.isFinishing() || activity.isDestroyed())return;
                if(result!=null && result.versionCode>installed) {
                    new AlertDialog.Builder(activity)
                        .setTitle("Charoite Next update available")
                        .setMessage(result.versionLabel+" (build "+result.versionCode+")\n"
                            +"Installed build: "+installed+"\n\n"
                            +"Open the official GitHub APK download? "
                            +"Android will request approval before installation. "
                            +"Install OVER the existing com.charoitx app; never uninstall, "
                            +"clear storage or touch stable Portal or Wine prefixes.\n\n"
                            +"Release checksum: "+result.sha256)
                        .setNegativeButton("Later",null)
                        .setPositiveButton("Open GitHub download",(d,w) -> {
                            try {activity.startActivity(new Intent(
                                Intent.ACTION_VIEW,Uri.parse(result.downloadUrl)));}
                            catch(Exception ignored) {new AlertDialog.Builder(activity)
                                .setMessage("Browser unavailable. Open the official GitHub releases page.")
                                .setPositiveButton("Close",null).show();}
                        }).show();
                } else if(manual) {
                    String message=error ? "Could not check GitHub releases. Try again later."
                        : result==null ? "No signed Charoite Next APK releases available yet."
                        : "Up to date. Installed build "+installed
                            +" is at least as recent as published build "+result.versionCode+".";
                    new AlertDialog.Builder(activity)
                        .setTitle("Charoite Next updates")
                        .setMessage(message)
                        .setPositiveButton("Close",null).show();
                }
            },manual?0L:7200L); // do not interrupt the 7-second boot splash
        },"CharoiteNextPublicGitHubUpdateCheck").start();
    }

    /** Called once when Portal Activity is created, not on tab switch or resume. */
    public static void checkOnLaunch(Activity activity){check(activity,false);}
    public static void checkNow(Activity activity){check(activity,true);}
}
