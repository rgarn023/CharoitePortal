package org.winehq.wine;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.os.Build;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.app.AlertDialog;
import android.util.AtomicFile;
import android.widget.LinearLayout;
import android.widget.Button;
import android.widget.TextView;

import androidx.annotation.Keep;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.IOException;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.io.InputStream;
import java.nio.file.Files;

// Wine looks up the class and method by their original JNI names.
@Keep
public final class WineActivity extends Activity {
    // ntdll registers this exact method during JNI_OnLoad.
    @Keep
    private native String wine_init(String[] command, String[] environment);

    private static AtomicFile checkpoint(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), "wine29-display-check.txt"));
    }

    private static void record(Context context, String message) throws IOException {
        AtomicFile file = checkpoint(context);
        FileOutputStream output = file.startWrite();
        try {
            output.write(message.getBytes(StandardCharsets.UTF_8));
            file.finishWrite(output);
        } catch (IOException failure) {
            file.failWrite(output);
            throw failure;
        }
    }

    public static void launchCheck(Activity portal) {
        try {
            record(portal, "Interrupted before the Wine29 display activity started.");
            portal.startActivity(new Intent(portal, WineActivity.class));
        } catch (IOException | RuntimeException failure) {
            checkpoint(portal).delete();
            new AlertDialog.Builder(portal).setTitle("Wine29 display check")
                    .setMessage("Could not start the check. " + failure.getClass().getSimpleName())
                    .setPositiveButton("OK", null).show();
        }
    }

    public static void showLastCheck(Activity portal) {
        AtomicFile file = checkpoint(portal);
        if (!file.getBaseFile().isFile()) return;
        try {
            long recordedAt = file.getBaseFile().lastModified();
            String report = new String(file.readFully(), StandardCharsets.UTF_8);
            if (report.startsWith("Interrupted")) report += describeExit(portal, recordedAt);
            file.delete();
            new AlertDialog.Builder(portal).setTitle("Wine29 display check")
                    .setMessage(report).setPositiveButton("OK", null).show();
        } catch (IOException failure) {
            android.util.Log.w("Wine29Display", "Could not read display checkpoint", failure);
        }
    }

    private static String describeExit(Activity portal, long recordedAt) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return "";
        ActivityManager manager = portal.getSystemService(ActivityManager.class);
        if (manager == null) return "";
        String processName = portal.getPackageName() + ":wine29_display";
        try {
            for (ApplicationExitInfo exit : manager.getHistoricalProcessExitReasons(
                    portal.getPackageName(), 0, 20)) {
                if (!processName.equals(exit.getProcessName()) || exit.getTimestamp() < recordedAt) {
                    continue;
                }
                String reason;
                switch (exit.getReason()) {
                    case ApplicationExitInfo.REASON_CRASH_NATIVE: reason = "native crash"; break;
                    case ApplicationExitInfo.REASON_CRASH: reason = "Java crash"; break;
                    case ApplicationExitInfo.REASON_SIGNALED: reason = "signal"; break;
                    case ApplicationExitInfo.REASON_EXIT_SELF: reason = "process exit"; break;
                    case ApplicationExitInfo.REASON_ANR: reason = "process did not respond"; break;
                    default: reason = "reason " + exit.getReason(); break;
                }
                String report = "\nAndroid reports " + reason + " (status " + exit.getStatus() + ").";
                return exit.getReason() == ApplicationExitInfo.REASON_CRASH_NATIVE
                        ? report + readAbortMessage(exit) : report;
            }
        } catch (RuntimeException failure) {
            android.util.Log.w("Wine29Display", "Could not read process exit reason", failure);
        }
        return "\nAndroid has no matching process-exit record yet.";
    }

    private static String readAbortMessage(ApplicationExitInfo exit) {
        // Android tombstone.proto: the top-level abort_message is string field 14.
        try (InputStream trace = exit.getTraceInputStream()) {
            if (trace == null) return "\nAndroid has no native abort detail.";
            DataInputStream input = new DataInputStream(new BufferedInputStream(trace));
            int remaining = 128 * 1024;
            while (remaining > 0) {
                long tag = readVarint(input);
                remaining -= 10;
                int wire = (int) (tag & 7);
                if (wire == 0) {
                    readVarint(input);
                    remaining -= 10;
                    continue;
                }
                long length;
                switch (wire) {
                    case 1: length = 8; break;
                    case 2: length = readVarint(input); remaining -= 10; break;
                    case 5: length = 4; break;
                    default: return "\nAndroid returned an unreadable abort detail.";
                }
                if (length < 0 || length > remaining) break;
                if (tag == ((14 << 3) | 2)) {
                    byte[] bytes = new byte[(int) Math.min(length, 768)];
                    input.readFully(bytes);
                    String detail = new String(bytes, StandardCharsets.UTF_8)
                            .replaceAll("[\\p{Cntrl}]+", " ")
                            .replaceAll("/[^\\s'\"]+", "[path]").trim();
                    if (!detail.isEmpty()) return "\nNative abort: " + detail;
                    break;
                }
                if (input.skipBytes((int) length) != length) break;
                remaining -= (int) length;
            }
        } catch (IOException | RuntimeException failure) {
            android.util.Log.w("Wine29Display", "Could not read native abort detail", failure);
        }
        return "\nAndroid has no readable native abort detail.";
    }

    private static long readVarint(DataInputStream input) throws IOException {
        long value = 0;
        for (int shift = 0; shift < 64; shift += 7) {
            int next = input.readUnsignedByte();
            if (shift == 63 && next > 1) throw new IOException("Invalid tombstone varint");
            value |= (long) (next & 127) << shift;
            if ((next & 128) == 0) return value;
        }
        throw new IOException("Invalid tombstone varint");
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int inset = Math.round(20 * getResources().getDisplayMetrics().density);
        layout.setPadding(inset, inset, inset, inset);
        TextView result = new TextView(this);
        result.setText("Checking Wine29 display libraries…");
        layout.addView(result);
        Button done = new Button(this);
        done.setText("Return to Charoite Portal");
        done.setOnClickListener(view -> finish());
        layout.addView(done);
        setContentView(layout);

        new Thread(() -> {
            String checked = checkLibraries();
            try {
                record(this, checked);
            } catch (IOException failure) {
                android.util.Log.w("Wine29Display", "Could not save display result", failure);
            }
            String report = checked;
            runOnUiThread(() -> {
                if (!isDestroyed()) result.setText(report);
            });
        }, "Wine29DisplayLibraries").start();
    }

    private String checkLibraries() {
        String[] libraries = {"ntdll.so", "win32u.so", "wineandroid.so"};
        File directory = null;
        String current = "staging";
        try {
            record(this, "Interrupted while preparing the Wine29 display libraries.");
            directory = Files.createTempDirectory(getCacheDir().toPath(), "wine29-display-").toFile();
            for (String library : libraries) {
                current = library;
                File file = new File(directory, library);
                try (InputStream asset = getAssets().open("wine29-java-host/" + library)) {
                    Files.copy(asset, file.toPath());
                }
                record(this, "Interrupted while loading " + library + ".");
                System.load(file.getAbsolutePath());
                record(this, "Interrupted after loading " + library + ".");
            }
            return "PASS — Android loaded all three Wine29 display libraries.";
        } catch (IOException | LinkageError failure) {
            return "FAIL — " + current + " — " + failure.getMessage();
        } finally {
            if (directory != null) {
                for (String library : libraries) new File(directory, library).delete();
                directory.delete();
            }
        }
    }
}
