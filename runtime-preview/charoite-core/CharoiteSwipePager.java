package com.charoitegames.core;

import android.content.Context;
import android.view.MotionEvent;
import android.view.ViewConfiguration;
import android.widget.ScrollView;

/**
 * A vertical scroll view that observes all descendant touch events for
 * side-to-side page gestures. Unlike interception-only handlers, dispatch-
 * level observation still works when buttons, cards, nested layouts or game
 * tiles consume MOVE/UP or disallow their parent from intercepting touches.
 *
 * This never consumes a horizontal gesture from a child (normal drag/drop,
 * taps, native scrolling continue through Android touch dispatch). The host
 * switches selected tabs only after a completed, clearly horizontal swipe.
 */
public final class CharoiteSwipePager extends ScrollView {
    public interface OnPageSwipe {
        /** +1 = swipe left/next; -1 = swipe right/previous. */
        void onPageSwipe(int direction);
    }

    private final OnPageSwipe listener;
    private final float minimumDistance;
    private final float movementThreshold;
    private final float screenEdgeWidth;
    private float startX;
    private float startY;
    private long startTime;
    private boolean tracking;
    private boolean vertical;
    private int pointerId = -1;

    public CharoiteSwipePager(Context context, OnPageSwipe listener) {
        super(context);
        if (listener == null) throw new IllegalArgumentException("Page swipe callback required");
        this.listener = listener;
        float density = getResources().getDisplayMetrics().density;
        minimumDistance = Math.max(64f * density,
                ViewConfiguration.get(context).getScaledTouchSlop() * 4f);
        movementThreshold = ViewConfiguration.get(context).getScaledTouchSlop() * 1.5f;
        screenEdgeWidth = 28f * density;
        setVerticalScrollBarEnabled(false);
    }

    private boolean isFingerOrStylus(MotionEvent event) {
        if (event.getPointerCount() != 1) return false;
        int tool = event.getToolType(0);
        return tool == MotionEvent.TOOL_TYPE_FINGER ||
                tool == MotionEvent.TOOL_TYPE_STYLUS;
    }

    /**
     * Called for every touch event entering the scroll content, including
     * children which consume touches. Horizontal movement is only observed,
     * not intercepted, so vertically scrollable pages remain scrollable.
     */
    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        int swipeDirection = 0;
        if (action == MotionEvent.ACTION_DOWN) {
            pointerId = event.getPointerId(0);
            startX = event.getX();
            startY = event.getY();
            startTime = event.getEventTime();
            // Leave Android edge-back gestures and Samsung DeX mouse alone.
            tracking = isFingerOrStylus(event) &&
                    startX >= screenEdgeWidth && startX <= getWidth() - screenEdgeWidth;
            vertical = false;
        } else if (action == MotionEvent.ACTION_POINTER_DOWN ||
                   action == MotionEvent.ACTION_CANCEL) {
            tracking = false;
        } else if (tracking && event.getPointerCount() != 1) {
            tracking = false;
        } else if (tracking && event.getPointerId(0) == pointerId) {
            float dx = event.getX() - startX;
            float dy = event.getY() - startY;
            if (action == MotionEvent.ACTION_MOVE) {
                // If vertical scrolling wins first, never turn it into a tab
                // change even if the swipe veers sideways near the end.
                if (Math.abs(dy) > movementThreshold * 2f &&
                        Math.abs(dy) > Math.abs(dx) * 1.1f)
                    vertical = true;
            } else if (action == MotionEvent.ACTION_UP) {
                long duration = event.getEventTime() - startTime;
                if (!vertical && duration < 1600L &&
                        Math.abs(dx) >= minimumDistance &&
                        Math.abs(dx) > Math.abs(dy) * 1.65f)
                    swipeDirection = dx < 0 ? 1 : -1;
                tracking = false;
            }
        }
        // Let the original page, drag handlers and controls finish their event
        // before changing the selected tab/layout.
        boolean consumed = super.dispatchTouchEvent(event);
        if (swipeDirection != 0) listener.onPageSwipe(swipeDirection);
        return consumed || swipeDirection != 0;
    }
}
