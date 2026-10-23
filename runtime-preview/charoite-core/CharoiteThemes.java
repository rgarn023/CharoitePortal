package com.charoitegames.core;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;
import android.graphics.PixelFormat;
import androidx.annotation.NonNull;

/**
 * Original, offline theme wallpaper artwork. No bundled game assets.
 * Each environment may override it with a privately chosen phone image.
 */
public final class CharoiteThemes {
    private CharoiteThemes() {}

    public static Drawable defaultWallpaper(String template, boolean dark) {
        return new PortalWallpaper("touhou".equals(template), dark);
    }


    /**
     * Short, legible, realm-specific hero/banner artwork. This is deliberately
     * separate from the full-screen user wallpaper so each realm retains a
     * recognizable identity even when the user selects a custom background.
     * The host overlays the realm name as real accessible TextView text.
     */
    public static Drawable realmBanner(String template) {
        return new RealmBanner("touhou".equals(template));
    }

    private static final class RealmBanner extends Drawable {
        private final boolean touhou;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

        RealmBanner(boolean touhou) {
            this.touhou = touhou;
        }

        private float frac(float number) {
            return number - (float)Math.floor(number);
        }

        @Override public void draw(@NonNull Canvas canvas) {
            android.graphics.Rect rect = getBounds();
            float width = rect.width(), height = rect.height();
            if (width <= 0 || height <= 0) return;
            canvas.save();
            canvas.translate(rect.left, rect.top);

            // True rounded banner art, not a game/app icon thumbnail.
            Path mask = new Path();
            float radius = Math.min(width, height) * 0.14f;
            mask.addRoundRect(0, 0, width, height, radius, radius, Path.Direction.CW);
            canvas.clipPath(mask);

            int left = touhou ? 0xff33203b : 0xff1A1A41;
            int right = touhou ? 0xffAE5C92 : 0xff7655BD;
            paint.setShader(new LinearGradient(0, 0, width, height * 0.6f,
                    left, right, Shader.TileMode.CLAMP));
            paint.setStyle(Paint.Style.FILL);
            canvas.drawRect(0, 0, width, height, paint);
            paint.setShader(null);

            if (touhou) {
                // Original floating cherry blossom and branch scene, biased to
                // the right so the main title remains very easy to read.
                Path branch = new Path();
                branch.moveTo(width * 1.06f, -height * 0.16f);
                branch.cubicTo(width * 0.92f, height * 0.27f,
                        width * 0.74f, height * 0.37f,
                        width * 0.69f, height * 0.66f);
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(0xBB4A2649);
                paint.setStrokeWidth(Math.max(3f, height * 0.035f));
                canvas.drawPath(branch, paint);
                paint.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 40; i++) {
                    float x = width * (0.63f + 0.39f * frac(i * 0.6180339f));
                    float y = height * (0.07f + 0.82f * frac(i * 0.41421f));
                    paint.setColor(i % 4 == 0 ? 0xFFFCE5F3 : 0xEAF3A3CB);
                    canvas.save();
                    canvas.translate(x, y);
                    canvas.rotate((i * 43) % 180);
                    float rx = Math.max(3f, height * (0.025f + 0.011f * frac(i * 0.163f)));
                    canvas.drawOval(-rx, -rx * 0.53f, rx, rx * 0.53f, paint);
                    canvas.restore();
                }
                // A quiet glow behind the blossoms.
                paint.setColor(0x40F6A3DD);
                canvas.drawCircle(width * 0.88f, height * 0.59f, height * 0.50f, paint);
            } else {
                // Original charoite gemstone and astral portal arcs. General
                // and custom Windows realms deliberately have no Touhou motifs.
                float cx = width * 0.82f, cy = height * 0.48f;
                for (int i = 0; i < 5; i++) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setStrokeWidth(Math.max(2f, height * (0.012f + i * 0.0015f)));
                    paint.setColor(i % 2 == 0 ? 0x88D5B0FF : 0x66F2D8FF);
                    float rr = height * (0.23f + 0.12f * i);
                    canvas.drawCircle(cx, cy, rr, paint);
                }
                paint.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 46; i++) {
                    float x = width * (0.52f + 0.48f * frac(i * 0.75487766f));
                    float y = height * frac(i * 0.56984029f);
                    paint.setColor(i % 4 == 0 ? 0xFFF5E7FF : 0x99C5B7FF);
                    float r = Math.max(1.2f, height * (0.005f + 0.008f * frac(i * 0.27f)));
                    canvas.drawCircle(x, y, r, paint);
                }
                // A subtle central luminous point within the portal.
                paint.setColor(0x99F2DFFF);
                canvas.drawCircle(cx, cy, height * 0.035f, paint);
            }

            // Shadow over the text-side, not a separate card or emblem.
            paint.setShader(new LinearGradient(0, 0, width * 0.76f, 0,
                    0x70301F38, 0x00301F38, Shader.TileMode.CLAMP));
            canvas.drawRect(0, 0, width, height, paint);
            paint.setShader(null);
            canvas.restore();
        }

        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(android.graphics.ColorFilter filter) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }

    private static final class PortalWallpaper extends Drawable {
        private final boolean touhou;
        private final boolean dark;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

        PortalWallpaper(boolean touhou, boolean dark) {
            this.touhou = touhou;
            this.dark = dark;
        }

        @Override public void draw(@NonNull Canvas canvas) {
            android.graphics.Rect r = getBounds();
            float w = r.width(), h = r.height();
            if (w <= 0 || h <= 0) return;
            canvas.save();
            canvas.translate(r.left, r.top);
            int top = touhou ? (dark ? 0xff24142b : 0xffFFE5EF)
                    : (dark ? 0xff0D1029 : 0xffE9E4FD);
            int bottom = touhou ? (dark ? 0xff54344F : 0xffF3C8DC)
                    : (dark ? 0xff3B2365 : 0xffC7B5F8);
            paint.setShader(new LinearGradient(0, 0, w, h, top, bottom, Shader.TileMode.CLAMP));
            canvas.drawRect(0, 0, w, h, paint);
            paint.setShader(null);
            if (touhou) {
                // A delicate painted sakura branch and petals; no Touhou assets.
                paint.setColor(dark ? 0x775D335C : 0x77785470);
                paint.setStrokeWidth(Math.max(3f, w * 0.008f));
                paint.setStyle(Paint.Style.STROKE);
                Path branch = new Path();
                branch.moveTo(w * 0.88f, -h * 0.04f);
                branch.cubicTo(w * 0.76f, h * 0.12f, w * 0.60f, h * 0.08f, w * 0.47f, h * 0.22f);
                canvas.drawPath(branch, paint);
                paint.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 27; i++) {
                    float x = w * (0.45f + 0.48f * frac(i * 0.361f));
                    float y = h * (0.01f + 0.27f * frac(i * 0.631f));
                    petal(canvas, x, y, w * (0.012f + 0.01f * frac(i * 0.24f)),
                            dark ? 0xB5FFA5D6 : 0xD9F99DC3);
                }
                for (int i = 0; i < 18; i++) {
                    petal(canvas, w * frac(i * 0.618f), h * frac(i * 0.372f),
                            w * 0.011f, dark ? 0x66FFCCE7 : 0x77D56AA2);
                }
            } else {
                // Charoite cosmic rings and stars for the general Windows theme.
                paint.setColor(dark ? 0x335A42BB : 0x446F50D4);
                float cx = w * 0.57f, cy = h * 0.40f;
                for (int i = 0; i < 4; i++) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setStrokeWidth(w * 0.007f);
                    canvas.drawCircle(cx, cy, w * (0.20f + i * 0.055f), paint);
                }
                paint.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 40; i++) {
                    float x = w * frac(i * 0.754877f);
                    float y = h * frac(i * 0.569841f);
                    paint.setColor(dark ? 0xCCEBCEFF : 0x99FFFFFF);
                    canvas.drawCircle(x, y, Math.max(1f, w * 0.002f), paint);
                }
            }
            canvas.restore();
        }

        private void petal(Canvas c, float x, float y, float radius, int color) {
            paint.setColor(color);
            c.save();
            c.translate(x, y);
            c.rotate(35);
            c.drawOval(-radius, -radius * 0.5f, radius, radius * 0.5f, paint);
            c.restore();
        }

        private float frac(float value) { return value - (float)Math.floor(value); }
        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(android.graphics.ColorFilter filter) {}
        @Override public int getOpacity() { return PixelFormat.OPAQUE; }
    }
}
