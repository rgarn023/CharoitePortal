package com.charoitegames.core;

import android.content.Context;
import com.winlator.xserver.ScreenInfo;
import com.winlator.xserver.Window;
import com.winlator.xserver.XServer;
import java.util.ArrayDeque;
import java.util.Locale;

/** Charoite Core's TPDP phone-window layout, independent of Portal UI. */
public final class CharoiteWindowPolicy {
    private CharoiteWindowPolicy() {}

    public static void centerGameWindow(Context context, XServer xServer,
                                        ScreenInfo screenInfo, Window window,
                                        String executable, boolean desktopWindow) {
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
