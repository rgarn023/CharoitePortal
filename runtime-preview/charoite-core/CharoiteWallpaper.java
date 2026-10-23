package com.charoitegames.core;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/**
 * Charoite Core's reusable local launcher-wallpaper storage and display policy.
 * UI ownership, photo-picker screens, and transparency are the launcher's job.
 * No Android system wallpaper, files outside app storage, or game data change.
 */
public final class CharoiteWallpaper {
    public static final int MODE_CROP = 0;
    public static final int MODE_FIT = 1;
    private static final int MAX_IMAGE_BYTES = 50 * 1024 * 1024;
    private static final String FILE_NAME = "charoite_launcher_wallpaper.image";
    private static final String MODE_KEY = "launcher_wallpaper_fit_mode";

    private CharoiteWallpaper() {}

    public static boolean hasWallpaper(Context context) {
        File file = new File(context.getFilesDir(), FILE_NAME);
        return file.isFile() && file.length() > 0;
    }

    public static int getMode(Context context) {
        int mode = context.getSharedPreferences("TouhouEntryActivity",
                Context.MODE_PRIVATE).getInt(MODE_KEY, MODE_CROP);
        return mode == MODE_FIT ? MODE_FIT : MODE_CROP;
    }

    // Same activity-private preferences used by existing Touhou Launcher UI.
    // The host passes its preferences to avoid relying on Activity internal names.
    public static int getMode(android.content.SharedPreferences preferences) {
        return preferences.getInt(MODE_KEY, MODE_CROP) == MODE_FIT ? MODE_FIT : MODE_CROP;
    }

    public static void setMode(android.content.SharedPreferences preferences, int mode) {
        if (mode != MODE_FIT && mode != MODE_CROP)
            throw new IllegalArgumentException("Invalid wallpaper mode");
        preferences.edit().putInt(MODE_KEY, mode).apply();
    }

    /** Copy only an image, atomically replacing the previous image on success. */
    public static void importImage(Context context, Uri pickedImage) throws IOException {
        File destination = new File(context.getFilesDir(), FILE_NAME);
        File temporary = new File(context.getFilesDir(), FILE_NAME + ".partial");
        try {
            String mime = context.getContentResolver().getType(pickedImage);
            if (mime != null && !mime.startsWith("image/"))
                throw new IOException("Select a supported image from your phone");
            long size = 0;
            try (InputStream source = context.getContentResolver().openInputStream(pickedImage);
                 FileOutputStream output = new FileOutputStream(temporary)) {
                if (source == null) throw new IOException("Unable to open image");
                byte[] chunk = new byte[32768];
                int count;
                while ((count = source.read(chunk)) != -1) {
                    size += count;
                    if (size > MAX_IMAGE_BYTES)
                        throw new IOException("Wallpaper image must be smaller than 50 MB");
                    output.write(chunk, 0, count);
                }
                output.flush();
                output.getFD().sync();
            }
            if (size == 0) throw new IOException("Selected image is empty");
            BitmapFactory.Options check = new BitmapFactory.Options();
            check.inJustDecodeBounds = true;
            BitmapFactory.decodeFile(temporary.getAbsolutePath(), check);
            if (check.outWidth <= 0 || check.outHeight <= 0)
                throw new IOException("The selected file isn't a supported image");
            Files.move(temporary.toPath(), destination.toPath(),
                    StandardCopyOption.REPLACE_EXISTING);
        } finally {
            if (temporary.exists()) temporary.delete();
        }
    }

    /** Sample oversized photos so a 100MP camera image won't overwhelm RAM. */
    public static Bitmap loadBitmap(Context context, int maxDimension) {
        File file = new File(context.getFilesDir(), FILE_NAME);
        if (!file.isFile()) return null;
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(file.getAbsolutePath(), bounds);
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null;
        int sample = 1;
        int target = Math.max(512, Math.min(maxDimension, 3072));
        while (Math.max(bounds.outWidth, bounds.outHeight) / sample > target
                && sample <= 512) sample *= 2;
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inSampleSize = sample;
        options.inPreferredConfig = Bitmap.Config.RGB_565;
        try {
            return BitmapFactory.decodeFile(file.getAbsolutePath(), options);
        } catch (OutOfMemoryError ignored) {
            return null;
        }
    }

    public static boolean removeWallpaper(Context context) {
        File file = new File(context.getFilesDir(), FILE_NAME);
        return !file.exists() || file.delete();
    }
}
