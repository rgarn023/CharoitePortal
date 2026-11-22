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

    COLORREF pixel = CLR_INVALID;
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
            GdiFlush();
            pixel = GetPixel(screen, sample.x, sample.y);
            if (pixel == paint_color)
                break;
        }
        Sleep(50);
    }
    ReleaseDC(NULL, screen);
    if (pixel != paint_color || !IsWindowVisible(window)) {
        DestroyWindow(window);
        ExitProcess(15);
    }

    Sleep(1500);
    DestroyWindow(window);
    ExitProcess(42);
}
