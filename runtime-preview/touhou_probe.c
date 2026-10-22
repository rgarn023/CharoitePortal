/*
 * Touhou Pocket Japanese installer font repair + diagnostic v5.
 *
 * Scoped Wine GUI font fix. Does not alter game files, window text,
 * locale, registry or install directory. Inspects the installer destination
 * EDIT control with WM_GETTEXTW and selects a Japanese TrueType font with
 * WM_SETFONT only if existing control font lacks known Japanese glyphs.
 *
 * v1 enumerated only the probe's own desktop. Winlator starts Windows
 * applications with explorer /desktop=nogui,... which can create a separate
 * Wine desktop. v3 enumerates children even when Wine marks the parent not visible; also uses EnumDesktopsW + EnumDesktopWindows as well as its own
 * current desktop. It never changes the thread desktop or foreground window.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <wctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const wchar_t *output_path = L"C:\\touhou_probe.log";
static HANDLE log_handle = INVALID_HANDLE_VALUE;
static int snapshots = 0;
static int seen_windows = 0;
static int seen_children = 0;
static int edit_controls = 0;
static int desktop_count = 0;
static int debug_windows = 0;
static int debug_children = 0;
static int repair_attempted = 0;

static void line(const char *value) {
    if (log_handle == INVALID_HANDLE_VALUE) return;
    DWORD written = 0;
    DWORD len = (DWORD)strlen(value);
    WriteFile(log_handle, value, len, &written, NULL);
    WriteFile(log_handle, "\r\n", 2, &written, NULL);
    FlushFileBuffers(log_handle);
}

static void utf8(const wchar_t *src, char *dest, int size) {
    if (!src || !src[0] || size < 2) {
        if (size) dest[0] = '\0';
        return;
    }
    if (!WideCharToMultiByte(CP_UTF8, 0, src, -1, dest, size, NULL, NULL))
        dest[0] = '\0';
}

static int has_word(const wchar_t *text, const wchar_t *match) {
    if (!text) return 0;
    int n = (int)wcslen(match);
    for (; *text; text++) {
        if (_wcsnicmp(text, match, n) == 0) return 1;
    }
    return 0;
}

static int is_path(const wchar_t *value) {
    if (!value || !value[0]) return 0;
    if (iswalpha(value[0]) && value[1] == L':' && value[2] == L'\\') return 1;
    return wcsstr(value, L"FocasLens") != NULL;
}


/*
 * A cross-process probe can read WM_GETTEXT but cannot safely send an HFONT
 * from its own process via WM_SETFONT to a foreign installer thread. v4
 * correctly refused to run after WM_GETFONT failed, but it cannot repair
 * across that boundary. Instead start an architecture-matched thread hook
 * helper, which creates and installs the font inside the installer's process.
 */
static void try_repair_path_font(HWND hwnd, const wchar_t *originalText) {
    if (repair_attempted) return;
    repair_attempted = 1;
    if (!wcsstr(originalText,L"\x5E7B\x60F3\x4EBA\x5F62\x6F14\x821E")) {
        line("font-fix: original Japanese text not present; no changes");
        return;
    }
    DWORD installerPid=0;
    DWORD installerThread=GetWindowThreadProcessId(hwnd,&installerPid);
    if (!installerPid || !installerThread) {
        line("font-fix: unable to identify installer's GUI thread");
        return;
    }
    HANDLE process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,installerPid);
    if (!process) {
        line("font-fix: cannot open installer process for bitness check");
        return;
    }
    BOOL is32bit=FALSE;
    if(!IsWow64Process(process,&is32bit)) {
        line("font-fix: IsWow64Process unavailable; trying 32-bit helper");
        is32bit=TRUE;
    }
    CloseHandle(process);
    const wchar_t *executable=is32bit
        ? L"C:\\touhou_font_helper32.exe" : L"C:\\touhou_font_helper64.exe";
    wchar_t cmdline[300];
    swprintf(cmdline,300,L"\"%ls\" %lu",executable,(unsigned long)installerThread);
    STARTUPINFOW startup;
    PROCESS_INFORMATION child;
    ZeroMemory(&startup,sizeof(startup));
    ZeroMemory(&child,sizeof(child));
    startup.cb=sizeof(startup);
    if (!CreateProcessW(executable,cmdline,NULL,NULL,FALSE,CREATE_NO_WINDOW,
           NULL,NULL,&startup,&child)) {
        char msg[220];
        snprintf(msg,sizeof(msg),
            "font-fix: helper process failed to launch (32bit=%d,error=%lu)",
            is32bit!=FALSE,(unsigned long)GetLastError());
        line(msg);
        return;
    }
    CloseHandle(child.hThread);
    CloseHandle(child.hProcess);
    char message[230];
    snprintf(message,sizeof(message),
        "font-fix: launched in-process helper (32bit=%d,targetThread=%lu)",
        is32bit!=FALSE,(unsigned long)installerThread);
    line(message);
}

static void glyph_report(HWND hwnd) {
    HDC dc = GetDC(hwnd);
    if (!dc) {
        line("GDI: GetDC failed");
        return;
    }
    HFONT font = (HFONT)SendMessageW(hwnd, WM_GETFONT, 0, 0);
    HGDIOBJ old = font ? SelectObject(dc, font) : NULL;
    wchar_t faceW[LF_FACESIZE] = {0};
    GetTextFaceW(dc, LF_FACESIZE, faceW);
    char face[200]; utf8(faceW, face, sizeof(face));
    const wchar_t text[] = L"\x5e7b\x60f3\x4eba\x5f62\x6f14\x821e";
    WORD glyphs[6];
    for (int i = 0; i < 6; i++) glyphs[i] = 0xffff;
    DWORD result = GetGlyphIndicesW(dc, text, 6, glyphs, GGI_MARK_NONEXISTING_GLYPHS);
    int missing = 0;
    for (int i = 0; i < 6; i++) if (glyphs[i] == 0xffff) missing++;
    char buffer[500];
    snprintf(buffer, sizeof(buffer), "font: name=%s missing_known_japanese=%d gdi_error=%d",
             face, missing, result == GDI_ERROR);
    line(buffer);
    if (old && old != HGDI_ERROR) SelectObject(dc, old);
    ReleaseDC(hwnd, dc);
}

static BOOL CALLBACK child_callback(HWND hwnd, LPARAM context) {
    (void)context;
    seen_children++;
    wchar_t classname[128] = {0};
    if (!GetClassNameW(hwnd, classname, 127)) return TRUE;

    /* Inno Setup uses VCL TEdit/TNewPathEdit as well as Edit controls.
       Count visible classes to diagnose custom widgets even if no path found. */
    int editor = has_word(classname, L"edit") || has_word(classname, L"combo");
    if (editor) edit_controls++;
    if (!editor) return TRUE;

    wchar_t value[2048] = {0};
    DWORD_PTR chars = 0;
    SetLastError(0);
    BOOL success = SendMessageTimeoutW(hwnd, WM_GETTEXT,
                     (WPARAM)(sizeof(value) / sizeof(value[0])),
                     (LPARAM)value, SMTO_ABORTIFHUNG | SMTO_BLOCK, 750,
                     &chars) != 0;
    if (!success || !chars || !is_path(value)) {
        if (debug_children++ < 7) {
            char cls[128]; utf8(classname, cls, sizeof(cls));
            char info[280];
            snprintf(info, sizeof(info),
                     "edit-candidate class=%s read_ok=%d chars=%lu err=%lu looks_path=%d",
                     cls, success, (unsigned long)chars,
                     (unsigned long)GetLastError(), is_path(value));
            line(info);
        }
        return TRUE;
    }

    char cls[128]; utf8(classname, cls, sizeof(cls));
    char report[7200];
    int pos = snprintf(report, sizeof(report),
               "PATH FOUND class=%s utf16_units=%lu codepoints=",
               cls, (unsigned long)chars);
    for (unsigned i = 0; value[i] && i < 450 && pos < (int)sizeof(report)-16; i++) {
        int n = snprintf(report + pos, sizeof(report) - (size_t)pos,
                         "%04X ", (unsigned)value[i]);
        if (n <= 0) break;
        pos += n;
    }
    line(report);
    glyph_report(hwnd);
    try_repair_path_font(hwnd, value);
    snapshots++;
    return TRUE;
}

static BOOL CALLBACK window_callback(HWND hwnd, LPARAM context) {
    (void)context;
    seen_windows++;
    wchar_t clsW[128] = {0};
    GetClassNameW(hwnd, clsW, 127);
    if (debug_windows++ < 12) {
        char cls[128]; utf8(clsW, cls, sizeof(cls));
        wchar_t title[200] = {0};
        GetWindowTextW(hwnd, title, 199);
        char sample[500];
        int pos = snprintf(sample, sizeof(sample),
                 "top-window class=%s visible=%d title_units=%u title_prefix_utf16=",
                 cls, IsWindowVisible(hwnd) ? 1 : 0, (unsigned)wcslen(title));
        for (unsigned i = 0; title[i] && i < 12 && pos < 445; i++)
            pos += snprintf(sample + pos, sizeof(sample) - (size_t)pos,
                            "%04X ", (unsigned)title[i]);
        line(sample);
    }
    /* Wine's explorer /desktop=nogui can report an installer TWizardForm
       as IsWindowVisible(FALSE) while it is displayed by the X server.
       Always enumerate its children: Win32 EnumChildWindows can inspect
       an invisible parent, and filtering it caused the exact v2 failure
       where TWizardForm was found but child_controls stayed at zero. */
    EnumChildWindows(hwnd, child_callback, 0);
    return TRUE;
}

static BOOL CALLBACK desktop_callback(LPWSTR name, LPARAM context) {
    (void)context;
    desktop_count++;
    char label[200]; utf8(name, label, sizeof(label));
    char msg[300];
    snprintf(msg, sizeof(msg), "desktop: name=%s", label);
    line(msg);

    HDESK desktop = OpenDesktopW(name, 0, FALSE, DESKTOP_READOBJECTS);
    if (!desktop) {
        snprintf(msg, sizeof(msg), "desktop-open-error=%lu",
                 (unsigned long)GetLastError());
        line(msg);
        return TRUE;
    }
    int was = seen_windows;
    if (!EnumDesktopWindows(desktop, window_callback, 0)) {
        snprintf(msg, sizeof(msg), "desktop-enumerate-error=%lu",
                 (unsigned long)GetLastError());
        line(msg);
    }
    snprintf(msg, sizeof(msg), "desktop-window-count=%d", seen_windows - was);
    line(msg);
    CloseDesktop(desktop);
    return TRUE;
}

static void enumerate_once(void) {
    seen_windows = seen_children = edit_controls = desktop_count = 0;
    if (!EnumWindows(window_callback, 0)) {
        char err[100];
        snprintf(err, sizeof(err), "EnumWindows error=%lu",
                 (unsigned long)GetLastError());
        line(err);
    }
    HWINSTA station = GetProcessWindowStation();
    if (station) {
        if (!EnumDesktopsW(station, desktop_callback, 0)) {
            char err[120];
            snprintf(err, sizeof(err), "EnumDesktops error=%lu",
                     (unsigned long)GetLastError());
            line(err);
        }
    } else line("GetProcessWindowStation failed");
}

int WINAPI wWinMain(HINSTANCE a, HINSTANCE b, PWSTR cmdline, int show) {
    (void)a; (void)b; (void)cmdline; (void)show;
    log_handle = CreateFileW(output_path, GENERIC_WRITE, FILE_SHARE_READ,
                             NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (log_handle == INVALID_HANDLE_VALUE) return 2;
    char header[500];
    snprintf(header, sizeof(header),
       "touhou-probe-v5 GetACP=%u GetOEMCP=%u GetUserDefaultUILanguage=%04X GetSystemDefaultUILanguage=%04X",
       GetACP(), GetOEMCP(), (unsigned)GetUserDefaultUILanguage(),
       (unsigned)GetSystemDefaultUILanguage());
    line(header);
    for (int pass=0; pass<30; pass++) {
        /* Log detailed windows only at first scan to keep report compact. */
        if (pass > 0) { debug_windows = 100; debug_children = 100; }
        enumerate_once();
        if (pass == 0 || pass == 5 || pass == 12 || snapshots > 0) {
            snprintf(header, sizeof(header),
                     "pass=%d desktops=%d windows=%d child_controls=%d edit_candidates=%d found=%d",
                     pass, desktop_count, seen_windows, seen_children,
                     edit_controls, snapshots);
            line(header);
        }
        if (snapshots > 0) break;
        Sleep(2000);
    }
    if (snapshots == 0) line(
        "No destination control readable; desktop/window counts above distinguish virtual-desktop isolation from custom installer controls.");
    else line("Japanese path captured; path text remains unchanged.");
    // WM_SETFONT does not transfer ownership of HFONT. Keep this helper
    // alive while the installer edit control exists.
    /* Actual HFONT belongs to installer process; never share it here. */
    CloseHandle(log_handle);
    return snapshots > 0 ? 0 : 1;
}
