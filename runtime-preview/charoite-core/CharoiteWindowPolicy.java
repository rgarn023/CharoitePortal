package com.charoitegames.core;

import android.content.Context;
import com.winlator.xserver.ScreenInfo;
import com.winlator.renderer.FullscreenTransformation;
import com.winlator.xserver.Window;
import com.winlator.xserver.XServer;
import java.util.ArrayDeque;
import java.util.Locale;

/** Charoite Core's TPDP phone-window layout, independent of Portal UI. */
public final class CharoiteWindowPolicy {
    private CharoiteWindowPolicy() {}

    /**
     * TPDP keeps its original D3D9 rendering dimensions while Winlator's
     * existing compositor enlarges the client aspect-ratio-correctly.
     * This does not change Wine resolution, graphics driver, or game files.
     */
    public static boolean enlargeHandheldGame(String executable,
                                              boolean desktopWindow) {
        return !desktopWindow && CharoiteCore.isTpdpGameExecutable(executable);
    }

    /**
     * The compositor's built-in fullscreen transformation normally centers
     * the game vertically. Move its enlarged image into the handheld's
     * upper screen region, clear of Select/Start and shoulder buttons.
     * Winlator's InputDeviceManager uses the same transformation for touch.
     */
    public static void placeScaledGame(FullscreenTransformation transform,
                                       ScreenInfo screenInfo,
                                       String executable, boolean desktopWindow) {
        if (transform == null || screenInfo == null ||
                !enlargeHandheldGame(executable, desktopWindow)) return;
        if (screenInfo.height <= screenInfo.width) return;
        // The full-width 720px enlargement clips the decorated TPDP window
        // on tall phones. Use a comfortable 86% of the available desktop
        // width (about 619x464 for TPDP's 480x360 image at 720px).
        // Scale both axes equally so there is no distortion or loss of
        // native D3D9 pixels. FullscreenTransformation retains the correct
        // inverse pointer scaling for taps on the enlarged image.
        final float portraitDisplayScale = 0.86f;
        transform.width = (short)Math.max(1,
                Math.round(transform.width * portraitDisplayScale));
        transform.height = (short)Math.max(1,
                Math.round(transform.height * portraitDisplayScale));
        transform.x = (short)((screenInfo.width - transform.width) / 2);
        int topMargin = Math.max(12, Math.round(screenInfo.height * 0.04f));
        int gameAreaHeight = Math.round(screenInfo.height * 0.56f) - topMargin;
        int y = topMargin + Math.max(0, (gameAreaHeight - transform.height) / 2);
        transform.y = (short)Math.min(
                Math.max(0, screenInfo.height - transform.height), y);
    }

    /**
     * A decorated Wine parent and its client must use a SINGLE scale and
     * origin. Applying the fullscreen-fit equation to each independently
     * stretches the title/border differently from the TPDP image.
     */
    public static void alignWindowFrame(FullscreenTransformation frame,
                                        FullscreenTransformation client,
                                        Window frameWindow, Window clientWindow,
                                        ScreenInfo screenInfo,
                                        String executable, boolean desktopWindow) {
        if (frame == null || client == null || frameWindow == null ||
                clientWindow == null || screenInfo == null ||
                !enlargeHandheldGame(executable, desktopWindow) ||
                screenInfo.height <= screenInfo.width ||
                clientWindow.getWidth() <= 0 || clientWindow.getHeight() <= 0)
            return;
        float scaleX = (float)client.width / clientWindow.getWidth();
        float scaleY = (float)client.height / clientWindow.getHeight();
        // Scale the parent at precisely the same rate as the actual game
        // drawable; don't use its independently computed fullscreen fit.
        frame.width = (short)Math.max(1,
                Math.round(frameWindow.getWidth() * scaleX));
        frame.height = (short)Math.max(1,
                Math.round(frameWindow.getHeight() * scaleY));
        frame.x = (short)Math.round(client.x +
                (frameWindow.getRootX() - clientWindow.getRootX()) * scaleX);
        frame.y = (short)Math.round(client.y +
                (frameWindow.getRootY() - clientWindow.getRootY()) * scaleY);
    }

    public static void centerGameWindow(Context context, XServer xServer,
                                        ScreenInfo screenInfo, Window window,
                                        String executable, boolean desktopWindow) {
        // When TPDP is compositor-scaled, leave its X11 parent/client
        // coordinates untouched. Moving the decorated frame via X11 while
        // separately projecting its child causes a second offset.
        if (enlargeHandheldGame(executable, desktopWindow)) return;
        if (desktopWindow || !CharoiteCore.isTpdpGameExecutable(executable) ||
                xServer == null || screenInfo == null || window == null ||
                !window.isRenderable() || window.isDesktopWindow() ||
                window.isDialogBox()) return;
        int width = window.getWidth(), height = window.getHeight();
        if (width < 360 || height < 260 ||
                width >= screenInfo.width || height >= screenInfo.height) return;
        String clazz = window.getClassName();
        String title = window.getName();
        clazz = clazz == null ? "" : clazz.toLowerCase(Locale.ROOT);
        title = title == null ? "" : title;
        if (!clazz.contains("gn_enbu") && !clazz.contains("enbu_ap") &&
                !title.contains("人形演舞") && !title.contains("ver1.34") &&
                !window.isApplicationWindow()) return;
        Window frame = window;
        while (frame.getParent() != null &&
                frame.getParent() != xServer.windowManager.rootWindow &&
                !frame.getParent().isDesktopWindow() &&
                frame.getParent().getWidth() < screenInfo.width &&
                frame.getParent().getHeight() < screenInfo.height)
            frame = frame.getParent();
        if (frame.getWidth() >= screenInfo.width ||
                frame.getHeight() >= screenInfo.height) return;
        int targetX = (screenInfo.width - frame.getWidth()) / 2;
        // Handheld portrait layout: preserve TPDP's native Direct3D client
        // size while placing the game in the upper display region, leaving
        // the central Select/Start and shoulder buttons unobstructed.
        int targetY;
        if (screenInfo.height > screenInfo.width) {
            float gameAreaHeight = screenInfo.height * 0.51f;
            targetY = Math.max(16, Math.round(
                    (gameAreaHeight - frame.getHeight()) / 2.0f));
        } else {
            targetY = (screenInfo.height - frame.getHeight()) / 2;
        }
        int deltaX = targetX - frame.getRootX();
        int deltaY = targetY - frame.getRootY();
        if (deltaX == 0 && deltaY == 0) return;
        frame.setX((short)(frame.getX() + deltaX));
        frame.setY((short)(frame.getY() + deltaY));
        // Refresh every child surface after moving the decorated Wine frame.
        ArrayDeque<Window> toUpdate = new ArrayDeque<>();
        toUpdate.addLast(frame);
        while (!toUpdate.isEmpty()) {
            Window part = toUpdate.removeFirst();
            xServer.windowManager.triggerOnUpdateWindowGeometry(part, false);
            for (Window child : part.getChildren()) toUpdate.addLast(child);
        }
        CharoiteDiagnostics.recordWindowPlacement(
                context, title, targetX, targetY,
                frame.getWidth(), frame.getHeight());
    }
}
