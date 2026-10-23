package com.charoitegames.core;

import android.content.Context;
import android.view.MotionEvent;
import android.view.ViewConfiguration;
import android.widget.ScrollView;

/**
 * Charoite Core's reusable horizontally swipeable content view.
 *
 * Left/right gestures change the host application's selected page.
 * Native vertical scrolling, taps, long-press-and-drag game tiles, and DeX
 * mouse input remain untouched. Swipes do not wrap past the first/last tab;
 * callers own the page index and respond to the requested direction.
 */
public final class CharoiteSwipePager extends ScrollView {
    public interface OnPageSwipe {
        /** -1 = swipe right / previous page; +1 = swipe left / next page. */
        void onPageSwipe(int direction);
    }

    private final OnPageSwipe listener;
    private final float touchSlop;
    private final float minSwipe;
    private float downX;
    private float downY;
    private boolean horizontalGesture;
    private boolean touchGesture;

    public CharoiteSwipePager(Context context, OnPageSwipe listener) {
        super(context);
        if (listener == null) throw new IllegalArgumentException("Swipe listener is required");
        this.listener = listener;
        float density = getResources().getDisplayMetrics().density;
        touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        minSwipe = Math.max(touchSlop * 4, 64 * density);
        setVerticalScrollBarEnabled(false);
    }

    private boolean isTouch(MotionEvent event) {
        if (event.getPointerCount() != 1) return false;
        int type = event.getToolType(0);
        // Mouse drags in Samsung DeX must remain mouse drags, not page swipes.
        return type == MotionEvent.TOOL_TYPE_FINGER
                || type == MotionEvent.TOOL_TYPE_STYLUS;
    }

    private void remember(MotionEvent event) {
        downX = event.getX();
        downY = event.getY();
        touchGesture = isTouch(event);
        horizontalGesture = false;
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            remember(event);
            return super.onInterceptTouchEvent(event);
        }
        if (action == MotionEvent.ACTION_CANCEL || action == MotionEvent.ACTION_UP) {
            horizontalGesture = false;
            return super.onInterceptTouchEvent(event);
        }
        if (action == MotionEvent.ACTION_POINTER_DOWN || !touchGesture) {
            return super.onInterceptTouchEvent(event);
        }
        if (action == MotionEvent.ACTION_MOVE && isTouch(event)) {
            float dx = Math.abs(event.getX() - downX);
            float dy = Math.abs(event.getY() - downY);
            if (dx > touchSlop * 2 && dx > dy * 1.45f) {
                horizontalGesture = true;
                // Once claimed, children receive ACTION_CANCEL; a swipe will
                // not also activate a game tile, button, or checkbox.
                return true;
            }
        }
        return super.onInterceptTouchEvent(event);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            remember(event);
        }
        if (horizontalGesture) {
            if (action == MotionEvent.ACTION_UP) {
                float dx = event.getX() - downX;
                float dy = event.getY() - downY;
                horizontalGesture = false;
                if (Math.abs(dx) >= minSwipe
                        && Math.abs(dx) > Math.abs(dy) * 1.4f) {
                    listener.onPageSwipe(dx < 0 ? 1 : -1);
                }
                return true;
            }
            if (action == MotionEvent.ACTION_CANCEL || action == MotionEvent.ACTION_POINTER_DOWN) {
                horizontalGesture = false;
            }
            return true;
        }
        return super.onTouchEvent(event);
    }
}
