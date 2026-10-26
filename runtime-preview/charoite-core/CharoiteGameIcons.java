package com.charoitegames.core;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Looper;
import android.util.LruCache;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import com.winlator.win32.MSIcon;
import com.winlator.win32.PEParser;

import java.io.File;
import java.io.FileOutputStream;
import java.lang.ref.WeakReference;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Displays each installed Windows game's genuine executable icon.
 *
 * Uses Winlator's existing native PE RT_ICON resource extractor rather than
 * guessing images based on the filename or shipping third-party artwork.
 * Local .ico/.png artwork may be used when the executable has no readable
 * icon. Work stays off the UI thread and thumbnail cache is disposable.
 */
public final class CharoiteGameIcons {
    private static final int SIZE_PX = 192;
    private static final int MAX_ICON_FILE = 4 * 1024 * 1024;
    private static final int MAX_EXE_FILE = 128 * 1024 * 1024;
    private static final ExecutorService WORKER = Executors.newSingleThreadExecutor();
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private static final LruCache<String, Bitmap> MEMORY = new LruCache<>(32);

    private CharoiteGameIcons() {}

    /** Only call on the UI thread. The fallback remains until an icon loads. */
    public static void bind(Context context, String executable,
                            ImageView target, TextView fallback) {
        target.setVisibility(View.GONE);
        fallback.setVisibility(View.VISIBLE);
        target.setTag(executable);
        File file = new File(executable);
        if (!file.isFile()) return;
        String key = cacheKey(file);
        Bitmap cached;
        synchronized (MEMORY) { cached = MEMORY.get(key); }
        if (cached != null && !cached.isRecycled()) {
            show(target, fallback, executable, cached);
            return;
        }

        Context app = context.getApplicationContext();
        WeakReference<ImageView> viewRef = new WeakReference<>(target);
        WeakReference<TextView> fallbackRef = new WeakReference<>(fallback);
        WORKER.execute(() -> {
            Bitmap icon = null;
            try {
                File cache = new File(app.getCacheDir(), "charoite-game-icons");
                File thumb = new File(cache, key + ".png");
                if (thumb.isFile() && thumb.length() > 0 &&
                        thumb.length() <= MAX_ICON_FILE)
                    icon = BitmapFactory.decodeFile(thumb.getAbsolutePath());
                if (icon == null) {
                    icon = genuineIcon(file);
                    if (icon != null) {
                        Bitmap resized = Bitmap.createScaledBitmap(icon, SIZE_PX, SIZE_PX, true);
                        if (resized != icon) icon.recycle();
                        icon = resized;
                        if ((cache.isDirectory() || cache.mkdirs()) &&
                                !thumb.exists()) {
                            File temp = File.createTempFile("icon-", ".png", cache);
                            try {
                                try (FileOutputStream out = new FileOutputStream(temp)) {
                                    icon.compress(Bitmap.CompressFormat.PNG, 100, out);
                                }
                                // Regenerable cache only; no installed game files touched.
                                if (!temp.renameTo(thumb)) temp.delete();
                            } finally { temp.delete(); }
                        }
                    }
                }
            } catch (Exception | LinkageError ignored) {
                // A game without PE icons must remain usable with its
                // original fallback Library glyph.
            }
            if (icon == null) return;
            final Bitmap result = icon;
            synchronized (MEMORY) { MEMORY.put(key, result); }
            UI.post(() -> {
                ImageView view = viewRef.get();
                TextView text = fallbackRef.get();
                if (view != null && text != null)
                    show(view, text, executable, result);
            });
        });
    }

    private static void show(ImageView target, TextView fallback,
                             String executable, Bitmap icon) {
        if (!executable.equals(target.getTag())) return;
        target.setImageBitmap(icon);
        target.setVisibility(View.VISIBLE);
        fallback.setVisibility(View.GONE);
    }

    private static Bitmap genuineIcon(File exe) {
        Bitmap icon = null;
        if (exe.length() > 0 && exe.length() <= MAX_EXE_FILE) {
            try { icon = PEParser.extractIcon(exe); }
            catch (Exception | LinkageError ignored) { /* Invalid PE icon. */ }
        }
        if (icon != null) return icon;
        // Some Windows games ship their official icon beside the EXE.
        File folder = exe.getParentFile();
        if (folder == null) return null;
        String name = exe.getName().replaceFirst("(?i)\\.exe$", "");
        for (String candidate : new String[]{name + ".ico", "icon.ico",
                name + ".png", "icon.png"}) {
            File source = new File(folder, candidate);
            if (!source.isFile() || source.length() <= 0 ||
                    source.length() > MAX_ICON_FILE) continue;
            try {
                icon = candidate.toLowerCase(Locale.ROOT).endsWith(".ico")
                        ? MSIcon.decodeFile(source)
                        : BitmapFactory.decodeFile(source.getAbsolutePath());
                if (icon != null) return icon;
            } catch (Exception | LinkageError ignored) {
                // Continue to the next user-installed official icon.
            }
        }
        return null;
    }

    /** Invalidate on reinstallation/replacement, even at the same path. */
    private static String cacheKey(File exe) {
        String identity = exe.getAbsolutePath() + "\n" + exe.length() +
                "\n" + exe.lastModified();
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(identity.getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder(bytes.length * 2);
            for (byte b : bytes) result.append(String.format(Locale.ROOT, "%02x", b & 0xff));
            return result.toString();
        } catch (Exception ignored) {
            return Integer.toHexString(identity.hashCode());
        }
    }
}
