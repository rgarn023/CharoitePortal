package com.charoitegames.core;

import android.content.Context;
import android.view.View;
import java.lang.ref.WeakReference;
import com.winlator.xserver.ScreenInfo;
import com.winlator.renderer.FullscreenTransformation;
import com.winlator.renderer.ViewTransformation;
import com.winlator.xserver.Window;
import com.winlator.xserver.XServer;
import java.util.ArrayDeque;
import java.util.Locale;

/** Charoite Core's TPDP phone-window layout, independent of Portal UI. */
public final class CharoiteWindowPolicy {
    private CharoiteWindowPolicy() {}

    /** The scaled TPDP client alone is the handheld display. */
    private static volatile int[] lastHandheldScreen;
    // Game-session presentation is a Core feature, not a TPDP-specific one.
    // Only explicit Library game launches can enable generic handheld mode.
    // Existing TPDP/Shard heuristics remain unchanged.
    private static volatile String generalHandheldExecutable;
    private static volatile int generalGameClientId = -1;

    public static void configureSession(String executable, boolean handheldGame) {
        generalHandheldExecutable = handheldGame && executable != null &&
                !CharoiteCore.isTpdpGameExecutable(executable)
                ? executable.replace('\\', '/').toLowerCase(Locale.ROOT) : null;
        generalGameClientId = -1;
        setHandheldOutline(null);
    }

    private static boolean generalHandheldGame(String executable, boolean desktopWindow) {
        return !desktopWindow && generalHandheldExecutable != null &&
                executable != null && generalHandheldExecutable.equals(
                        executable.replace('\\', '/').toLowerCase(Locale.ROOT));
    }
    private static volatile WeakReference<View> outlineRef = new WeakReference<>(null);
    // Only Shard's portrait touch game screen uses this debounce. The base
    // TPDP session, DeX mouse, installers and controls keep native behavior.
    private static long lastShardTouchTapAt;
    private static int lastShardTouchTapX;
    private static int lastShardTouchTapY;
    // When the game changes its native size (including on double-click), it
    // remains the SAME X11 game client. Do not lose the fullscreen transform
    // merely because the new dimensions no longer pass the startup heuristic.
    private static volatile int activeShardClientId = -1;
    private static volatile int activeShardClientWidth = -1;
    private static volatile int activeShardClientHeight = -1;

    public static void setHandheldOutline(View outline) {
        // A new game session must not inherit the previous game's tap or
        // screen coordinates. Do not touch the actual Wine window or files.
        lastShardTouchTapAt = 0;
        lastHandheldScreen = null;
        activeShardClientId = -1;
        activeShardClientWidth = -1;
        activeShardClientHeight = -1;
        outlineRef = new WeakReference<>(outline);
        if (outline != null) outline.postInvalidate();
    }

    public static void invalidateHandheldOutline() {
        View outline = outlineRef.get();
        if (outline != null) outline.postInvalidate();
    }

    public static int[] handheldScreenBounds() {
        return lastHandheldScreen;
    }

    /** The compositor-selected X11 game client is our focus target. */
    public static int handheldGameClientId() {
        return generalGameClientId;
    }

    /**
     * Filter the SECOND nearby Shard-only phone touchscreen tap at the
     * TouchpadView click producer, preventing Wine WM_LBUTTONDBLCLK from
     * changing the game's window dimensions.
     *
     * Do NOT compare these coordinates with lastHandheldScreen. The
     * TouchpadView maps Android touches into Wine desktop coordinates, while
     * the fullscreen transformation draws the game elsewhere in that desktop:
     * the two rectangles are NOT interchangeable. That old boundary check
     * rejected legitimate taps and silently disabled the protection.
     *
     * Only the second short tap is consumed; the first click, holds, drags,
     * physical mouse, handheld keyboard controls, base TPDP and DeX remain
     * unaffected. The originating TouchpadView excludes overlay buttons.
     */
    public static boolean suppressShardTouchDoubleTap(String executable,
                                                       boolean desktopWindow,
                                                       ScreenInfo screenInfo,
                                                       int touchX, int touchY) {
        if (desktopWindow || screenInfo == null ||
                !CharoiteShardOfDreamsSupport.isExpansionGame(executable)) {
            lastShardTouchTapAt = 0;
            return false;
        }
        long now = android.os.SystemClock.uptimeMillis();
        int tolerance = Math.max(20, screenInfo.width / 16);
        boolean repeated = lastShardTouchTapAt > 0 &&
                now - lastShardTouchTapAt <=
                        android.view.ViewConfiguration.getDoubleTapTimeout() &&
                Math.abs(touchX - lastShardTouchTapX) <= tolerance &&
                Math.abs(touchY - lastShardTouchTapY) <= tolerance;
        // Consume exactly the second tap of each pair rather than breaking
        // all taps or permanently disabling game-screen mouse input.
        lastShardTouchTapAt = repeated ? 0 : now;
        lastShardTouchTapX = touchX;
        lastShardTouchTapY = touchY;
        return repeated;
    }

    /**
     * Keep the working TPDP base-game client selection unchanged. Shard's
     * Japanese executable may map a larger game client with either 4:3 or
     * widescreen dimensions and may advertise window decorations.
     * Restrict the exception to recognized Shard launches, the real game
     * drawable (not its decorated parent), and portrait handheld sessions.
     */
    private static boolean isHandheldGameClient(Window client, ScreenInfo screenInfo,
                                                 String executable, boolean desktopWindow) {
        if (!enlargeHandheldGame(executable, desktopWindow) || client == null ||
                screenInfo == null) return false;
        int width = client.getWidth(), height = client.getHeight();
        if (generalHandheldGame(executable, desktopWindow)) {
            // Choose the actual undecorated game drawable, not a Wine
            // decorated parent, installer, desktop, or tiny popup.
            if (client.isDesktopWindow() || client.isDialogBox() ||
                    client.getType() != Window.Type.NORMAL ||
                    client.getChildCount() != 0 || !client.hasNoDecorations())
                return false;
            if (generalGameClientId != -1 && generalGameClientId != client.id)
                return false;
            if (width < 320 || height < 200 || width >= screenInfo.width ||
                    height >= screenInfo.height ||
                    (float)width / height < 0.65f ||
                    (float)width / height > 2.8f) return false;
            generalGameClientId = client.id;
            return true;
        }
        boolean shard = CharoiteShardOfDreamsSupport.isExpansionGame(executable);
        if (!shard) {
            // Preserve the verified TPDP base-game selection exactly.
            return width >= 460 && width <= 485 &&
                    height >= 335 && height <= 375;
        }
        if (client.isDesktopWindow() || client.isDialogBox() ||
                client.getType() != Window.Type.NORMAL) return false;
        // Shard maps a 968x747 top-level frame AND its 960x720 child.
        // The old size heuristic selected both, repeatedly switching
        // activeShardClientId and rendering two scaled overlapping windows.
        // Do not treat a container with children as the game drawable.
        // Check BEFORE reusing a sticky window ID from an earlier frame.
        if (client.getChildCount() > 0) return false;
        // Shard maps the Wine 968x747 parent before the 960x720 child.
        // At that instant getChildCount() can still be 0, so the parent
        // incorrectly becomes the active game. A never-before-tracked game
        // drawable must fit within the current Wine desktop width.
        // Once the correct X11 ID is known, later game resizes stay tracked.
        if (activeShardClientId != client.id &&
                width > screenInfo.width) return false;
        // An X11 window keeps the same id when Wine resizes it. This is the
        // crucial difference from the former min-460x335 heuristic, which
        // dropped fullscreen scaling as soon as Shard switched window mode.
        boolean sameClient = activeShardClientId == client.id;
        if (sameClient) {
            if (width < 96 || height < 72 || width > 4096 || height > 4096)
                return false;
            if (activeShardClientWidth != width || activeShardClientHeight != height) {
                CharoiteDiagnostics.recordShardWindowChange(client.id,
                        activeShardClientWidth, activeShardClientHeight, width, height,
                        "same game window retained");
                activeShardClientWidth = width;
                activeShardClientHeight = height;
            }
            return true;
        }
        // Do not select the separately decorated Wine parent frame.
        if (client.getChildCount() > 0 &&
                client.hasDecoration(com.winlator.xserver.Decoration.TITLE))
            return false;
        float ratio = height > 0 ? (float)width / height : 0;
        boolean normalGameSize = width >= 460 && height >= 335 &&
                width <= 1920 && height <= 1440 &&
                ratio >= 0.95f && ratio <= 2.4f;
        // A game can replace its X11 drawable on a mode switch; recover by
        // title/class evidence instead of accepting every tiny Wine dialog.
        String title = client.getName();
        String clazz = client.getClassName();
        boolean shardIdentity =
                (title != null && (title.contains("人形演舞") ||
                        title.contains("ユメノカケラ"))) ||
                (clazz != null && (clazz.contains("enbu_ap") ||
                        clazz.contains("幻想人形演舞")));
        boolean smallIdentifiedGame = shardIdentity && width >= 240 &&
                height >= 180 && width <= 1920 && height <= 1440 &&
                ratio >= 0.8f && ratio <= 2.4f;
        if (!normalGameSize && !smallIdentifiedGame) return false;
        activeShardClientId = client.id;
        activeShardClientWidth = width;
        activeShardClientHeight = height;
        CharoiteDiagnostics.recordShardWindowChange(client.id, 0, 0,
                width, height, "Shard game window selected");
        return true;
    }

    /**
     * Winlator ordinarily requires the client to fit INSIDE Wine's desktop
     * before applying its fullscreen transformation. Shard's startup window
     * may equal or exceed that desktop, leaving its title bar visible and
     * clipping the game over the controls. Allow only Shard game clients.
     */
    /** Prevent a Shard window container from receiving its own fullscreen
     * projection, even when it passes upstream's original size check. */
    public static boolean isShardHandheldContainer(Window window,
                                                    ScreenInfo screenInfo,
                                                    String executable,
                                                    boolean desktopWindow) {
        return CharoiteShardOfDreamsSupport.isExpansionGame(executable) &&
                enlargeHandheldGame(executable, desktopWindow) &&
                screenInfo != null && screenInfo.height > screenInfo.width &&
                window != null && !window.isDesktopWindow() &&
                window.getChildCount() > 0;
    }

    public static boolean allowOversizedShardGame(Window client, ScreenInfo screenInfo,
                                                    String executable, boolean desktopWindow) {
        return CharoiteShardOfDreamsSupport.isExpansionGame(executable) &&
                isHandheldGameClient(client, screenInfo, executable, desktopWindow);
    }

    /**
     * The upstream compositor applies fullscreen only to undecorated windows.
     * Shard's real D3D9 client can still advertise decorations; its separate
     * parent frame is discarded, never stretched along with the game.
     * Do not permit this override for installers, dialogs, or other games.
     */
    public static boolean allowDecoratedShardClient(Window client,
                                                     ScreenInfo screenInfo,
                                                     String executable,
                                                     boolean desktopWindow) {
        return CharoiteShardOfDreamsSupport.isExpansionGame(executable) &&
                isHandheldGameClient(client, screenInfo, executable, desktopWindow) &&
                client.getChildCount() == 0;
    }

    private static void rememberClientScreen(FullscreenTransformation rect,
                                             ScreenInfo screenInfo, Window client,
                                             String executable, boolean desktopWindow) {
        if (!isHandheldGameClient(client, screenInfo, executable, desktopWindow)) return;
        int[] next = new int[]{
                rect.x, rect.y, rect.width, rect.height,
                screenInfo.width, screenInfo.height};
        int[] old = lastHandheldScreen;
        if (old != null && java.util.Arrays.equals(old, next)) return;
        lastHandheldScreen = next;
        View view = outlineRef.get();
        if (view != null) view.postInvalidate();
    }

    /**
     * The Wine title bar/border is an independent X11 drawable. It must not
     * be rendered along with the fullscreen-scaled game client on phones:
     * this created the separated top and bottom strips in the screenshots.
     * Only remove that parent's drawable, not its X11 window, children,
     * keyboard focus, game process, or its actual geometry.
     */
    public static boolean hideNativeFrame(Window frame, Window client,
                                          ScreenInfo screenInfo,
                                          String executable, boolean desktopWindow) {
        if (!enlargeHandheldGame(executable, desktopWindow) ||
                frame == null || client == null || screenInfo == null ||
                frame == client || screenInfo.height <= screenInfo.width)
            return false;
        int dw = frame.getWidth() - client.getWidth();
        int dh = frame.getHeight() - client.getHeight();
        if (!isHandheldGameClient(client, screenInfo, executable, desktopWindow))
            return false;
        // The Shard frame is a separate X11 drawable, about 8x27px larger
        // than the game. Hide its quad even when Wine decoration flags are
        // absent, but ONLY for the selected direct child/parent pair.
        // Do not delete either X11 window or affect game files/input.
        if (CharoiteShardOfDreamsSupport.isExpansionGame(executable) &&
                activeShardClientId == client.id)
            return client.getParent() == frame &&
                    frame.getChildCount() == 1 &&
                    !frame.isDesktopWindow() &&
                    dw >= 0 && dw <= 48 && dh >= 0 && dh <= 80 &&
                    (dw > 0 || dh > 0);
        return dw >= 0 && dw <= 48 && dh >= 0 && dh <= 80 &&
                (dw > 0 || dh > 0);
    }

    /**
     * TPDP keeps its original D3D9 rendering dimensions while Winlator's
     * existing compositor enlarges the client aspect-ratio-correctly.
     * This does not change Wine resolution, graphics driver, or game files.
     */
    public static boolean enlargeHandheldGame(String executable,
                                              boolean desktopWindow) {
        return !desktopWindow &&
                (CharoiteCore.isTpdpGameExecutable(executable) ||
                 generalHandheldGame(executable, desktopWindow));
    }

    /**
     * The compositor's built-in fullscreen transformation normally centers
     * the game vertically. Move its enlarged image into the handheld's
     * upper screen region, clear of Select/Start and shoulder buttons.
     * Winlator's InputDeviceManager uses the same transformation for touch.
     */
    public static void placeScaledGame(FullscreenTransformation transform,
                                       ScreenInfo screenInfo, Window client,
                                       String executable, boolean desktopWindow) {
        if (transform == null || screenInfo == null || client == null ||
                !enlargeHandheldGame(executable, desktopWindow)) return;
        // Do not resize Wine's decorated parent or its other guest windows.
        if (!isHandheldGameClient(client, screenInfo, executable, desktopWindow)) return;
        if (generalHandheldGame(executable, desktopWindow)) {
            // Use the same upper-screen bezel and touch-space as TPDP,
            // while respecting each game's ORIGINAL pixel aspect ratio.
            // Do not resize the Windows client or alter its graphics driver.
            // Inset the entire game quad so HUD text survives the bezel.
            float maxWidth = screenInfo.width * 0.80f;
            float maxHeight = screenInfo.height * 0.42f;
            float scale = Math.min(maxWidth / Math.max(1, transform.width),
                    maxHeight / Math.max(1, transform.height));
            if (!(scale > 0f)) return;
            transform.width = (short)Math.max(1, Math.round(transform.width * scale));
            transform.height = (short)Math.max(1, Math.round(transform.height * scale));
            transform.x = (short)((screenInfo.width - transform.width) / 2);
            transform.y = (short)Math.max(0,
                    Math.round(screenInfo.height * 0.065f +
                    (screenInfo.height * 0.42f - transform.height) / 2f));
            rememberClientScreen(transform, screenInfo, client, executable, desktopWindow);
            return;
        }
        // A game started in landscape already looks right. Record its game
        // surface for an eventual physical turn to portrait, but DO NOT
        // change its original upstream fullscreen transform.
        if (screenInfo.height <= screenInfo.width) {
            rememberClientScreen(transform, screenInfo, client, executable, desktopWindow);
            return;
        }
        // The full-width 720px enlargement clips the decorated TPDP window
        // on tall phones. Use a comfortable 86% of the available desktop
        // width (about 619x464 for TPDP's 480x360 image at 720px).
        // Scale both axes equally so there is no distortion or loss of
        // native D3D9 pixels. FullscreenTransformation retains the correct
        // inverse pointer scaling for taps on the enlarged image.
        final float portraitDisplayScale = 0.86f;
        // Leave the verified base TPDP 480x360 transform unchanged.
        // Shard may draw to a *square* 4:3-ish or widescreen X11 surface;
        // scaling only its width to 86% can produce a 620x620 viewport on
        // a 720-pixel desktop, overlapping controls and cropping its art.
        // Fit its ORIGINAL surface aspect ratio INSIDE the same 4:3 handheld
        // screen rectangle as the base game. No guest window resize/stretch.
        if (CharoiteShardOfDreamsSupport.isExpansionGame(executable)) {
            final int targetWidth = Math.max(1,
                    Math.round(screenInfo.width * portraitDisplayScale));
            final int top = Math.max(12, Math.round(screenInfo.height * 0.04f));
            final int targetHeight = Math.max(1, Math.min(
                    Math.round(targetWidth * 0.75f),
                    Math.round(screenInfo.height * 0.50f) - top));
            final float fit = Math.min((float) targetWidth / transform.width,
                    (float) targetHeight / transform.height);
            transform.width = (short)Math.max(1, Math.round(transform.width * fit));
            transform.height = (short)Math.max(1, Math.round(transform.height * fit));
        } else {
            transform.width = (short)Math.max(1,
                    Math.round(transform.width * portraitDisplayScale));
            transform.height = (short)Math.max(1,
                    Math.round(transform.height * portraitDisplayScale));
        }
        transform.x = (short)((screenInfo.width - transform.width) / 2);
        int topMargin = Math.max(12, Math.round(screenInfo.height * 0.04f));
        int gameAreaHeight = Math.round(screenInfo.height * 0.56f) - topMargin;
        int y = topMargin + Math.max(0, (gameAreaHeight - transform.height) / 2);
        transform.y = (short)Math.min(
                Math.max(0, screenInfo.height - transform.height), y);
        rememberClientScreen(transform, screenInfo, client, executable, desktopWindow);
    }

    /**
     * Re-project the SAME live Wine desktop when the Android surface rotates.
     * The guest's X11 / Direct3D9 resolution is never changed mid-session.
     * On matching orientations, preserve the existing working viewport.
     *
     * On a mismatch, zoom the game quad into the available native display
     * region with ONE scalar for X and Y; no stretching or letterbox
     * distortion. The XServer still contains all windows; we only change
     * the Android GL projection and matching pointer mapping.
     */
    public static void updateLiveViewport(ViewTransformation view,
                                          ScreenInfo guest,
                                          int physicalWidth, int physicalHeight,
                                          String executable, boolean desktopWindow) {
        if (view == null || guest == null || physicalWidth <= 0 || physicalHeight <= 0)
            return;
        view.update(physicalWidth, physicalHeight, guest.width, guest.height);
        if (!enlargeHandheldGame(executable, desktopWindow)) return;
        int[] game = lastHandheldScreen;
        if (game == null || game.length < 6 || game[2] <= 0 || game[3] <= 0 ||
                game[4] != guest.width || game[5] != guest.height) return;
        boolean physicalPortrait = physicalHeight >= physicalWidth;
        boolean guestPortrait = guest.height >= guest.width;
        if (physicalPortrait == guestPortrait) return;

        // Portrait: keep the game high above controls. Landscape: center
        // the display between left/right gamepad controls.
        final float maxW = physicalWidth * (physicalPortrait ? 0.80f : 0.69f);
        final float maxH = physicalHeight * (physicalPortrait ? 0.42f : 0.70f);
        final float scale = Math.min(maxW / game[2], maxH / game[3]);
        if (!(scale > 0f) || Float.isInfinite(scale) || Float.isNaN(scale)) return;
        final float shownW = game[2] * scale;
        final float shownH = game[3] * scale;
        final float gameLeft = (physicalWidth - shownW) * 0.5f;
        final float gameTop = physicalHeight * (physicalPortrait ? 0.055f : 0.10f);
        // Android GL viewport Y has a bottom origin; Window XForm uses
        // top-down guest scene coordinates. Match both consistently.
        final float sceneLeft = gameLeft - game[0] * scale;
        final float sceneTop = gameTop - game[1] * scale;
        final int projectedWidth = Math.max(1, Math.round(guest.width * scale));
        final int projectedHeight = Math.max(1, Math.round(guest.height * scale));
        view.aspect = scale;
        view.viewWidth = projectedWidth;
        view.viewHeight = projectedHeight;
        view.viewOffsetX = Math.round(sceneLeft);
        view.viewOffsetY = Math.round(physicalHeight - sceneTop - projectedHeight);
        view.sceneScaleX = (guest.width * scale) / physicalWidth;
        view.sceneScaleY = (guest.height * scale) / physicalHeight;
        view.sceneOffsetX = -sceneLeft * guest.width / physicalWidth;
        view.sceneOffsetY = -sceneTop * guest.height / physicalHeight;
        View outline = outlineRef.get();
        if (outline != null) outline.postInvalidate();
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
