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
