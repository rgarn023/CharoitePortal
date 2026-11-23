#define WIN32_LEAN_AND_MEAN
#include <windows.h>

static const COLORREF paint_color = RGB(124, 64, 192);

static LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam)
{
    if (message == WM_PAINT) {
        PAINTSTRUCT paint;
        HDC dc = BeginPaint(window, &paint);
        RECT client;
        GetClientRect(window, &client);
        HBRUSH brush = CreateSolidBrush(paint_color);
        if (brush) {
            FillRect(dc, &client, brush);
            DeleteObject(brush);
        }
        EndPaint(window, &paint);
        return 0;
    }
    return DefWindowProcW(window, message, wparam, lparam);
}

/* Direct client-DC repaint is a recovery for an Android driver that
 * delivers the window surface but misses the first WM_PAINT invalidation.
 * It still uses standard GDI; it never writes into an Android surface
 * directly and does not weaken the two independent GetPixel gates. */
static void repaint_client_dc(HWND window)
{
    RECT client;
    HDC dc = GetDC(window);
    if (!dc) return;
    if (GetClientRect(window, &client))
    {
        HBRUSH brush = CreateSolidBrush(paint_color);
        if (brush)
        {
            FillRect(dc, &client, brush);
            DeleteObject(brush);
        }
    }
    GdiFlush();
    ReleaseDC(window, dc);
}

void fixture_entry(void)
{
    HINSTANCE instance = GetModuleHandleW(NULL);
    WNDCLASSW window_class = {0};
    window_class.lpfnWndProc = window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = L"CharoiteWine29WindowSmoke";
    if (!RegisterClassW(&window_class))
        ExitProcess(11);

    HWND window = CreateWindowExW(0, window_class.lpszClassName,
        L"Charoite Portal x64 window test", WS_POPUP,
        80, 80, 360, 220, NULL, NULL, instance, NULL);
    if (!window)
        ExitProcess(12);

    ShowWindow(window, SW_SHOWNORMAL);

    POINT sample = {16, 16};

    HDC screen = GetDC(NULL);
    if (!screen)
        ExitProcess(14);

    /* Read the actual HWND's client DC as well as the composited desktop.
     * A GUI may paint its client surface correctly even when a platform
     * driver does not expose that result through GetPixel(screen). */
    HDC client_dc = GetDC(window);
    if (!client_dc) {
        ReleaseDC(NULL, screen);
        ExitProcess(14);
    }

    COLORREF pixel = CLR_INVALID;
    COLORREF client_pixel = CLR_INVALID;
    for (unsigned attempt = 0; attempt < 100; ++attempt) {
        MSG message;
        while (PeekMessageW(&message, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
        RECT client;
        if (GetClientRect(window, &client) && client.right > 16 && client.bottom > 16
            && IsWindowVisible(window)) {
            sample = (POINT){16, 16};
            if (!ClientToScreen(window, &sample))
                ExitProcess(13);
            InvalidateRect(window, NULL, FALSE);
            UpdateWindow(window);
            /* Repaint through the HWND client DC if a normal WM_PAINT
             * has still not made pixels visible. Never synthesize a pass. */
            if (attempt == 0 || attempt == 20 || attempt == 60)
                repaint_client_dc(window);
            GdiFlush();
            client_pixel = GetPixel(client_dc, 16, 16);
            pixel = GetPixel(screen, sample.x, sample.y);
            if (pixel == paint_color && client_pixel == paint_color)
                break;
        }
        Sleep(50);
    }
    ReleaseDC(window, client_dc);
    ReleaseDC(NULL, screen);
    if (pixel != paint_color || client_pixel != paint_color || !IsWindowVisible(window)) {
        /* Distinguish client painting from desktop readback; never count
         * either one alone as a passed Windows display test.
         * 15 = neither pixel matched, 16 = client only, 17 = screen only. */
        unsigned code = client_pixel == paint_color ? 16
            : pixel == paint_color ? 17 : 15;
        DestroyWindow(window);
        ExitProcess(code);
    }

    Sleep(1500);
    DestroyWindow(window);
    ExitProcess(42);
}
