package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Explicit opt-in, STRICT READ-ONLY V28 postmortem.
 *
 * Inspect ONLY four named V28 diagnostic logs and V28 system.reg, with small
 * bounded reads. Never touch other generations, launch Wine, create/delete
 * files, follow symlinks, print raw lines, values or paths.
 */
public final class CharoiteWine29V28PreservedReadOnly {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine29-entry-v28";
    private static final String[] LOGS = {
        "v28-foreground-wineserver.log",
        "v28-wine-direct-init.log",
        "v28-independent-defaultinstall.log",
        "v28-independent-sc-rpcss-query.log"
    };
    private static final int[] LIMITS = {
        262144, 2097152, 4194304, 2097152
    };
    private CharoiteWine29V28PreservedReadOnly() {}

    private static void safeDirectory(File directory) throws Exception {
        if (!directory.isDirectory() || !directory.getCanonicalFile().equals(directory.getAbsoluteFile()))
            throw new SecurityException("A preserved V28 directory is missing or unsafe");
        StructStat stat=Os.lstat(directory.getAbsolutePath());
        if (!OsConstants.S_ISDIR(stat.st_mode))
            throw new SecurityException("A preserved V28 directory is not a regular directory");
    }
    private static File exactChild(File parent, String name) throws Exception {
        if (name.contains("/") || name.contains("\\") || name.equals(".") || name.equals(".."))
            throw new SecurityException("Non-allowlisted child name");
        File child=new File(parent,name);
        if (!child.getAbsoluteFile().getParentFile().equals(parent.getAbsoluteFile())
                || !child.getCanonicalFile().equals(child.getAbsoluteFile()))
            throw new SecurityException("Symlink or unsafe V28 path");
        return child;
    }
    private static String readIfSafe(File parent, String name, int maximum, StringBuilder out)
            throws Exception {
        File file=exactChild(parent,name);
        if (!file.exists()) {
            out.append(name).append(": ABSENT (no read)\n");
            return null;
        }
        StructStat stat=Os.lstat(file.getAbsolutePath());
        if (!OsConstants.S_ISREG(stat.st_mode) || !file.isFile()
                || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            throw new SecurityException("Non-regular preserved evidence; no contents read");
        long size=file.length();
        out.append(name).append(" bounded regular file: ").append(size>=0 && size<=maximum)
           .append("; bytes: ").append(size).append('\n');
        if (size<0 || size>maximum) {
            out.append(name).append(": OVER CAP; no contents read\n");
            return null;
        }
        ByteArrayOutputStream bytes=new ByteArrayOutputStream((int)Math.min(size,65536L));
        try(InputStream in=new FileInputStream(file)) {
            byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1) {
                if (bytes.size()+n>maximum)
                    throw new SecurityException("Preserved V28 evidence grew beyond file cap");
                bytes.write(buffer,0,n);
            }
        }
        return bytes.toString(StandardCharsets.UTF_8.name()).toLowerCase(Locale.US);
    }
    private static void flag(StringBuilder b,String label, String log,String pattern) {
        b.append(label).append(": ")
            .append(log==null?"UNKNOWN (missing/over-cap log)":Boolean.toString(log.contains(pattern)))
            .append('\n');
    }
    private static void registryMarkers(String registry,StringBuilder b) {
        if(registry==null){
            b.append("Registry service evidence: UNKNOWN (no bounded registry read)\n");
            return;
        }
        boolean inRpcss=false,root=false,image=false,start=false,type=false,header;
        int serviceRoots=0;
        header=registry.startsWith("wine registry version");
        for(String line:registry.split("\n")){
            String trimmed=line.trim();
            if(trimmed.startsWith("[")&&trimmed.contains("]")){
                String key=trimmed.substring(1,trimmed.indexOf(']')).replace("\\\\","\\");
                int p=key.indexOf("\\services\\");
                String tail=p<0?"":key.substring(p+"\\services\\".length());
                inRpcss=p>=0 && "rpcss".equals(tail);
                if(p>=0 && tail.length()>0 && !tail.contains("\\"))serviceRoots++;
                root|=inRpcss;
            }else if(inRpcss){
                image|=trimmed.startsWith("\"imagepath\"=");
                start|=trimmed.startsWith("\"start\"=");
                type|=trimmed.startsWith("\"type\"=");
            }
        }
        b.append("V28 registry header recognized: ").append(header).append('\n');
        b.append("V28 service root count: ").append(serviceRoots).append('\n');
        b.append("V28 exact RpcSs root: ").append(root).append('\n');
        b.append("V28 RpcSs ImagePath present: ").append(image).append('\n');
        b.append("V28 RpcSs Start present: ").append(start).append('\n');
        b.append("V28 RpcSs Type present: ").append(type).append('\n');
        b.append("Registry values/names other than fixed allowlist: NOT COPIED\n");
    }
    public static String inspect(Context context) {
        StringBuilder b=new StringBuilder(
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md\n"
            +"CHAROITE NEXT — WINE29 V28 PERMANENTLY CONSUMED READ-ONLY POSTMORTEM\n"
            +"NO Wine/wineserver/Wineboot/sc.exe/rundll32.exe or process creation. "
            +"NO writes, cleanup, scratch creation, retry, old generation visits, games or saves.\n");
        if(!PACKAGE.equals(context.getPackageName()))
            return b.append("RESULT: BLOCKED — wrong app identity\n").toString();
        try {
            File base=context.getNoBackupFilesDir().getCanonicalFile();
            safeDirectory(base);
            File scratch=exactChild(base,SCRATCH);
            safeDirectory(scratch);
            b.append("V28 existing scratch: PRESENT; preserved and never altered\n");
            String[] content=new String[4];
            for(int i=0;i<LOGS.length;i++)
                content[i]=readIfSafe(scratch,LOGS[i],LIMITS[i],b);
            String server=content[0],wineboot=content[1],helper=content[2],scm=content[3];
            flag(b,"V28 server trace has internal --init mention",server,"--init");
            flag(b,"V28 server trace has RpcSs mention",server,"rpcss");
            flag(b,"V28 Wineboot trace start_rundll32 mention",wineboot,"start_rundll32");
            flag(b,"V28 Wineboot trace PreInstall mention",wineboot,"installhinfsection preinstall");
            flag(b,"V28 Wineboot trace DefaultInstall mention",wineboot,"installhinfsection defaultinstall");
            flag(b,"V28 Wineboot trace kernel32 missing",wineboot,"c0000135");
            flag(b,"V28 helper trace InstallHinfSection mention",helper,"installhinfsection");
            flag(b,"V28 helper trace ARM64 DefaultInstall section",helper,"defaultinstall.ntarm64");
            flag(b,"V28 helper trace RpcSs mention",helper,"rpcss");
            flag(b,"V28 helper trace INF open failure",helper,"failed to open");
            flag(b,"V28 helper trace SetupAPI error",helper,"err:setupapi");
            flag(b,"V28 helper trace child exec error",helper,"charoite_wine29_v6_child_execv_failure");
            flag(b,"V28 SCM query identifies RpcSs",scm,"service_name: rpcss");
            flag(b,"V28 SCM query service-state field",scm,"state");
            flag(b,"V28 SCM query error 1060",scm,"1060");
            flag(b,"V28 SCM query error 1722",scm,"1722");
            flag(b,"V28 SCM query module error",scm,"c0000135");
            // Only fixed categories, never raw SCM or SetupAPI lines/paths.
            // A generic "state" token does NOT prove a valid service-state row.
            CharoiteWine29V28ScopedTriage.appendMarkers(b,scm,helper);
            File prefix=exactChild(scratch,"prefix");
            safeDirectory(prefix);
            String registry=readIfSafe(prefix,"system.reg",1048576,b);
            registryMarkers(registry,b);
            b.append("RESULT: READ-ONLY REVIEW COMPLETE; markers do not imply successful SCM operation\n");
        } catch(Exception ex) {
            b.append("RESULT: READ-ONLY REVIEW BLOCKED — ")
             .append(ex.getClass().getSimpleName())
             .append("; no unsafe content read, no data modified\n");
        }
        b.append("V28 is CONSUMED; NEVER retry V28; V1–V27, Wine28, stable Portal, games, saves, rootfs untouched\n")
         .append("END OF V28 PRESERVED READ-ONLY POSTMORTEM\n");
        return b.toString();
    }

    public static void askConsent(Activity activity) {
        new AlertDialog.Builder(activity)
          .setTitle("Read ONLY preserved V28 evidence?")
          .setMessage("V28 is CONSUMED and cannot be rerun. With this separate "
             +"authorization, inspect ONLY V28's FOUR named diagnostic logs "
             +"(limits: 256 KiB, 2 MiB, 4 MiB, 2 MiB) and "
             +"V28 prefix/system.reg (1 MiB), using no-follow path/regular-file "
             +"gates. Report fixed markers/byte counts, anchored historical "
             +"RpcSs service STATE (if unambiguous) and allowlisted SetupAPI "
             +"error categories ONLY. Never expose raw logs, registry "
             +"values, paths or identifiers. No Wine, no other generation, "
             +"no new scratch, writes, cleanup, deletion or network. "
             +"If you do not authorize, tap Cancel.")
          .setNegativeButton("Cancel — no file access",null)
          .setPositiveButton("Authorize bounded READ ONLY",(dialog,which) -> {
              new Thread(() -> {
                  String report=inspect(activity.getApplicationContext());
                  new Handler(Looper.getMainLooper()).post(() -> {
                      if(activity.isFinishing()||activity.isDestroyed())return;
                      new AlertDialog.Builder(activity)
                        .setTitle("V28 preserved read-only postmortem")
                        .setMessage(report)
                        .setPositiveButton("Copy read-only report",(d,w) -> {
                            android.content.ClipboardManager clipboard=
                              (android.content.ClipboardManager)activity.getSystemService(
                                  Context.CLIPBOARD_SERVICE);
                            if(clipboard!=null)clipboard.setPrimaryClip(
                              android.content.ClipData.newPlainText(
                                "V28 consumed read-only postmortem",report));
                        })
                        .setNegativeButton("Close",null)
                        .show();
                  });
              },"CharoiteV28ReadOnlyPostmortem").start();
          }).show();
    }
}
