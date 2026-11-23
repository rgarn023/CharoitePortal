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
import android.widget.FrameLayout;
import android.graphics.Bitmap;
import android.graphics.SurfaceTexture;
import android.view.Surface;
import android.view.TextureView;
import android.util.SparseArray;
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

    private native void wine_desktop_changed(int width, int height);
    private native void wine_config_changed(int dpi);
    private native void wine_surface_changed(int hwnd, Surface surface, boolean opengl);
    private native boolean wine_motion_event(int hwnd, int action, int x, int y, int state, int vscroll);
    private native boolean wine_keyboard_event(int hwnd, int action, int keycode, int state);

    private static final int WS_VISIBLE = 0x10000000;
    private final SparseArray<TextureView> windows = new SparseArray<>();
    private FrameLayout desktop;
    private int desktopHwnd;
    // Only a posted Android frame (not a Win32 screen-DC readback) can prove presentation.
    private boolean presentedPurpleWindow;
    private boolean sampledWindowFrame;
    private long lastFrameReadbackAt;
    private boolean recordedDrawableWindow;
    private final java.util.ArrayDeque<String> windowStageHistory = new java.util.ArrayDeque<>();

    // Called by Wine's Android driver. Keep all Android view changes on the UI thread.
    public void createDesktopWindow(int hwnd) {
        runOnUiThread(() -> {
            if (isFinishing() || isDestroyed() || desktop != null) return;
            recordWindowStage("Interrupted after Wine requested an Android desktop.");
            desktopHwnd = hwnd;
            desktop = new FrameLayout(this);
            desktop.addOnLayoutChangeListener((view, left, top, right, bottom,
                    oldLeft, oldTop, oldRight, oldBottom) -> {
                int width = right - left;
                int height = bottom - top;
                if (width > 0 && height > 0
                        && (width != oldRight - oldLeft || height != oldBottom - oldTop)) {
                    wine_desktop_changed(width, height);
                    recordWindowStage("Wine received Android desktop dimensions " + width + "×" + height + ".");
                }
            });
            setContentView(desktop);
            addWindow(hwnd, false, FrameLayout.LayoutParams.MATCH_PARENT,
                    FrameLayout.LayoutParams.MATCH_PARENT);
            wine_config_changed(getResources().getDisplayMetrics().densityDpi);
        });
    }

    private synchronized void recordWindowStage(String stage) {
        try {
            // Persist a bounded event history, not just the last checkpoint.
            // This survives a normal Wine ExitProcess and contains no screenshot
            // pixels, file paths, user content, or game state.
            if (windowStageHistory.size() == 20) windowStageHistory.removeFirst();
            windowStageHistory.addLast(stage);
            StringBuilder history = new StringBuilder(
                    "Interrupted during Wine29 x64 window test; Android frame checkpoints:\n");
            for (String event : windowStageHistory) history.append(event).append('\n');
            record(this, history.toString());
        } catch (IOException failure) {
            android.util.Log.w("Wine29Display", "Could not save display checkpoint", failure);
        }
    }

    public void createWindow(int hwnd, boolean opengl, int parent, float scale, int pid) {
        runOnUiThread(() -> addWindow(hwnd, opengl, 1, 1));
    }

    private void addWindow(int hwnd, boolean opengl, int width, int height) {
        if (desktop == null || isFinishing() || isDestroyed() || windows.get(hwnd) != null) return;
        TextureView view = new TextureView(this);
        view.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
            private Surface surface;

            @Override
            public void onSurfaceTextureAvailable(SurfaceTexture texture, int width, int height) {
                surface = new Surface(texture);
                recordWindowStage("Android texture available hwnd "
                        + Integer.toHexString(hwnd) + " size " + width + "x" + height + ".");
                recordWindowStage("Interrupted while handing a window surface to Wine.");
                wine_surface_changed(hwnd, surface, opengl);
                recordWindowStage("Interrupted after handing a window surface to Wine.");
            }

            @Override
            public void onSurfaceTextureSizeChanged(SurfaceTexture texture, int width, int height) {
                if (surface != null) wine_surface_changed(hwnd, surface, opengl);
                if (hwnd != desktopHwnd) recordWindowStage("Android child texture size "
                        + width + "x" + height + ".");
            }

            @Override
            public boolean onSurfaceTextureDestroyed(SurfaceTexture texture) {
                if (surface != null) {
                    try {
                        wine_surface_changed(hwnd, null, opengl);
                    } finally {
                        surface.release();
                        surface = null;
                    }
                }
                return true;
            }

            @Override
            public void onSurfaceTextureUpdated(SurfaceTexture texture) {
                // The desktop can have its own SurfaceTexture. Only sample
                // an actual, sized child window after Android posts a frame.
                if (hwnd == desktopHwnd || presentedPurpleWindow || isFinishing()
                        || isDestroyed() || !view.isAvailable()
                        || view.getWidth() < 16 || view.getHeight() < 16) return;
                // Frame callbacks may arrive rapidly; avoid repeated blocking GPU
                // readbacks on the Android UI thread while a window is animating.
                long now = android.os.SystemClock.uptimeMillis();
                if (now - lastFrameReadbackAt < 250) return;
                lastFrameReadbackAt = now;
                Bitmap frame = null;
                try {
                    // Small, bounded GPU readback. No screenshot or game data is stored.
                    frame = view.getBitmap(64, 64);
                    if (frame == null) return;
                    int pixel = frame.getPixel(8, 8) & 0x00ffffff;
                    if (Math.abs(((pixel >> 16) & 255) - 124) <= 8
                            && Math.abs(((pixel >> 8) & 255) - 64) <= 8
                            && Math.abs((pixel & 255) - 192) <= 8) {
                        presentedPurpleWindow = true;
                        recordWindowStage("Android presentation VERIFIED: the Wine29 x64 "
                                + "window posted a purple RGB frame. "
                                + "Win32 screen-DC readback is a separate gate.");
                    } else if (!sampledWindowFrame) {
                        sampledWindowFrame = true;
                        recordWindowStage(String.format(java.util.Locale.ROOT,
                                "Android posted a Wine29 window frame, sampled RGB #%06X "
                                + "(expected #7C40C0).", pixel));
                    }
                } catch (RuntimeException failure) {
                    android.util.Log.w("Wine29Display", "Could not sample window frame", failure);
                } finally {
                    if (frame != null) frame.recycle();
                }
            }
        });
        windows.put(hwnd, view);
        desktop.addView(view, new FrameLayout.LayoutParams(width, height));
    }

    public void destroyWindow(int hwnd) {
        runOnUiThread(() -> {
            TextureView view = windows.get(hwnd);
            if (view == null) return;
            windows.remove(hwnd);
            desktop.removeView(view);
        });
    }

    public void windowPosChanged(int hwnd, int flags, int after, int owner, int style,
            int left, int top, int right, int bottom,
            int clientLeft, int clientTop, int clientRight, int clientBottom,
            int visibleLeft, int visibleTop, int visibleRight, int visibleBottom) {
        runOnUiThread(() -> {
            TextureView view = windows.get(hwnd);
            if (view == null) return;
            FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(
                    Math.max(1, right - left), Math.max(1, bottom - top));
            layout.leftMargin = left;
            layout.topMargin = top;
            view.setLayoutParams(layout);
            view.setVisibility((style & WS_VISIBLE) != 0 ? TextureView.VISIBLE : TextureView.INVISIBLE);
            if (hwnd != desktopHwnd && !recordedDrawableWindow
                    && (style & WS_VISIBLE) != 0
                    && right - left >= 16 && bottom - top >= 16) {
                recordedDrawableWindow = true;
                recordWindowStage("Android window drawable and visible, hwnd "
                        + Integer.toHexString(hwnd) + " size "
                        + (right - left) + "x" + (bottom - top) + ".");
            }
        });
    }

    // The single-window test uses a flat desktop with Android's default pointer.
    public void setParent(int hwnd, int parent, float scale, int pid) {}
    public void setCursor(int id, int width, int height, int hotspotX, int hotspotY, int[] bits) {}

    public static void showWindowLog(Activity portal) {
        File log = portal.getNoBackupFilesDir();
        for (int version = 18; version >= 1; version--) {
            log = new File(portal.getNoBackupFilesDir(),
                    "charoite-next-wine29-x64-window-v" + version + "/x64-window-native.log");
            if (log.exists()) break;
        }
        String report;
        try {
            if (!log.isFile() || !log.getCanonicalFile().equals(log.getAbsoluteFile())) {
                report = "No preserved native Wine log for the window test.";
            } else {
                try (java.io.RandomAccessFile input = new java.io.RandomAccessFile(log, "r")) {
                    long size = input.length();
                    byte[] tail = new byte[(int) Math.min(size, 16384L)];
                    input.seek(size - tail.length);
                    input.readFully(tail);
                    String detail = new String(tail, StandardCharsets.UTF_8)
                            .replaceAll("[\\p{Cntrl}&&[^\\n\\t]]+", " ")
                            .replaceAll("/[^\\s'\"]+", "[path]").trim();
                    report = detail.isEmpty() ? "The preserved Wine log is empty." : detail;
                }
            }
        } catch (IOException failure) {
            report = "Could not read the preserved Wine window log.";
        }
        final String message = report;
        new AlertDialog.Builder(portal).setTitle("Wine29 window log").setMessage(message)
                .setNegativeButton("Close", null)
                .setPositiveButton("Copy", (dialog, which) -> {
                    android.content.ClipboardManager clipboard =
                            portal.getSystemService(android.content.ClipboardManager.class);
                    if (clipboard != null) clipboard.setPrimaryClip(
                            android.content.ClipData.newPlainText("Wine29 window log", message));
                }).show();
    }

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
        launch(portal, false);
    }

    public static void launchWindow(Activity portal) {
        launch(portal, true);
    }

    private static void launch(Activity portal, boolean window) {
        try {
            record(portal, "Interrupted before the Wine29 display activity started.");
            portal.startActivity(new Intent(portal, WineActivity.class).putExtra("window", window));
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
                // v17 exit codes are diagnostic, never count a single pixel
                // as Windows/Android graphics success.
                if (exit.getReason() == ApplicationExitInfo.REASON_EXIT_SELF) {
                    switch (exit.getStatus()) {
                        case 15: return report + "\nNeither Windows client nor screen pixel matched.";
                        case 16: return report + "\nWindows client pixel matched; screen readback did not.";
                        case 17: return report + "\nWindows screen pixel matched; client readback did not.";
                        case 42: return report + "\nWindows dual-pixel fixture passed; Android visible frame still separate.";
                        default: break;
                    }
                }
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
        boolean window = getIntent().getBooleanExtra("window", false);
        result.setText(window ? "Preparing the private Wine29 window test…" : "Checking Wine29 display libraries…");
        layout.addView(result);
        Button done = new Button(this);
        done.setText("Return to Charoite Portal");
        done.setOnClickListener(view -> finish());
        layout.addView(done);
        setContentView(layout);

        new Thread(() -> {
            String checked = window
                    ? com.charoitegames.core.CharoiteWine29V28FocusedInfProbe.runX64Window(this, this::launchFixture)
                    : checkLibraries();
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

    private void launchFixture(File host, String[] command, String[] environment) throws IOException {
        for (String library : new String[] {"ntdll.so", "win32u.so", "wineandroid.so"}) {
            record(this, "Interrupted while loading window-test " + library + ".");
            System.load(new File(host, "aarch64-unix/" + library).getAbsolutePath());
        }
        record(this, "Interrupted while running the x64 window fixture.");
        android.os.Handler timeout = new android.os.Handler(android.os.Looper.getMainLooper());
        Runnable stop = () -> android.os.Process.killProcess(android.os.Process.myPid());
        timeout.postDelayed(stop, 45000);
        try {
            wine_init(command, environment);
        } finally {
            timeout.removeCallbacks(stop);
        }
        throw new IOException("Wine returned to Java before the test process exited.");
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
