package com.charoitegames.core;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Build;
import android.view.View;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.Locale;

/**
 * Per-device INTERNAL PHOTOGRAPH under the transparent purple handheld case.
 * Android provides model identifiers, NOT a view of physical circuitry.
 * Show an actual user-chosen photo for that model, never invent substitute parts.
 * Imported photos stay entirely inside the app's private data directory and
 * cannot affect Wine containers, installations or game saves.
 */
public final class CharoiteHardwareSkin {
    public static final int PICK_INTERNALS_REQUEST = 7916;
    private static String cacheModel;
    private static Bitmap cachedImage;
    private static boolean cacheLoaded;

    private CharoiteHardwareSkin() {}

    private static String modelName() {
        String manufacturer = Build.MANUFACTURER == null ? "" : Build.MANUFACTURER;
        String model = Build.MODEL == null ? "Unknown" : Build.MODEL;
        return (manufacturer + " " + model).trim();
    }

    private static String modelKey() {
        // Distinct installed images per hardware model, including Galaxy variants.
        return modelName().toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", "_");
    }

    private static File path(Activity host) {
        return new File(new File(host.getFilesDir(), "charoite-hardware-photos"),
                modelKey() + ".png");
    }

    public static String currentDevice() {
        return modelName();
    }

    public static void choosePicture(Activity host) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        host.startActivityForResult(intent, PICK_INTERNALS_REQUEST);
    }

    public static boolean onImageSelected(Activity host, int requestCode,
                                          int resultCode, Intent data) {
        if (requestCode != PICK_INTERNALS_REQUEST) return false;
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null)
            return true;
        Bitmap image = null;
        try {
            BitmapFactory.Options probe = new BitmapFactory.Options();
            probe.inJustDecodeBounds = true;
            try (InputStream stream = host.getContentResolver().openInputStream(data.getData())) {
                BitmapFactory.decodeStream(stream, null, probe);
            }
            if (probe.outWidth <= 0 || probe.outHeight <= 0)
                throw new java.io.IOException("Not an image");
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inSampleSize = 1;
            while (probe.outWidth / options.inSampleSize > 2048 ||
                   probe.outHeight / options.inSampleSize > 4096)
                options.inSampleSize *= 2;
            try (InputStream stream = host.getContentResolver().openInputStream(data.getData())) {
                image = BitmapFactory.decodeStream(stream, null, options);
            }
            if (image == null) throw new java.io.IOException("Cannot decode image");
            File destination = path(host);
            File parent = destination.getParentFile();
            if (parent == null || (!parent.exists() && !parent.mkdirs()))
                throw new java.io.IOException("Cannot create image folder");
            File pending = new File(parent, destination.getName() + ".tmp");
            try (FileOutputStream stream = new FileOutputStream(pending)) {
                if (!image.compress(Bitmap.CompressFormat.PNG, 100, stream))
                    throw new java.io.IOException("Cannot save image");
            }
            if (!pending.renameTo(destination))
                throw new java.io.IOException("Cannot apply photo");
            synchronized (CharoiteHardwareSkin.class) {
                if (cachedImage != null && cachedImage != image) cachedImage.recycle();
                cachedImage = image;
                cacheModel = modelKey();
                cacheLoaded = true;
            }
            CharoiteWindowPolicy.invalidateHandheldOutline();
            android.widget.Toast.makeText(host, "Interior photo set for " + modelName(),
                    android.widget.Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            if (image != null) image.recycle();
            android.widget.Toast.makeText(host, "Image could not be imported: " +
                    error.getMessage(), android.widget.Toast.LENGTH_LONG).show();
        }
        return true;
    }

    private static synchronized Bitmap currentImage(Activity host) {
        String current = modelKey();
        if (!current.equals(cacheModel)) {
            if (cachedImage != null) cachedImage.recycle();
            cachedImage = null;
            cacheLoaded = false;
            cacheModel = current;
        }
        if (!cacheLoaded) {
            File image = path(host);
            if (image.isFile()) cachedImage = BitmapFactory.decodeFile(image.getAbsolutePath());
            cacheLoaded = true;
        }
        return cachedImage;
    }

    public static void drawInterior(Canvas canvas, Activity host,
                                    float width, float height) {
        Bitmap image = currentImage(host);
        if (image == null || image.isRecycled()) return;
        Paint paint = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.ANTI_ALIAS_FLAG);
        paint.setAlpha(245);
        // Center crop to the handset's silhouette, avoiding aspect distortion.
        float targetAspect = width / Math.max(1, height);
        float photoAspect = (float)image.getWidth() / Math.max(1, image.getHeight());
        int sourceWidth = image.getWidth(), sourceHeight = image.getHeight();
        android.graphics.Rect source;
        if (photoAspect > targetAspect) {
            int cropW = Math.max(1, Math.round(sourceHeight * targetAspect));
            source = new android.graphics.Rect((sourceWidth - cropW) / 2, 0,
                    (sourceWidth + cropW) / 2, sourceHeight);
        } else {
            int cropH = Math.max(1, Math.round(sourceWidth / targetAspect));
            source = new android.graphics.Rect(0, (sourceHeight - cropH) / 2,
                    sourceWidth, (sourceHeight + cropH) / 2);
        }
        canvas.drawBitmap(image, source, new RectF(0, 0, width, height), paint);
    }
}
