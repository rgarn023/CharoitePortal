/*
 * Touhou Pocket Japanese installer font repair + diagnostic v4.
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
static HWND repaired_edit = NULL;
static HFONT repaired_font = NULL;
static HFONT previous_font = NULL;
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
 * Replace only the font of the exact destination TEdit control, not its text.
 * The installer continues using the original C:\game\FocasLens\... path.
 *
 * WM_SETFONT is a system Windows message supported by a standard EDIT/VCL
 * control. Some environments reject a font handle from another process;
 * verify WM_GETFONT after sending and revert on failure. Keep the HFONT alive
 * until the edit window closes, rather than freeing it while in use.
 */
static void try_repair_path_font(HWND hwnd, const wchar_t *originalText) {
    if (repair_attempted || repaired_edit != NULL) return;
    repair_attempted = 1;
    int hasJapanese = 0;
    for (int i=0; originalText[i]; i++)
        if ((originalText[i] >= 0x3000 && originalText[i] <= 0x9fff) ||
            (originalText[i] >= 0xf900 && originalText[i] <= 0xfaff))
            { hasJapanese = 1; break; }
    if (!hasJapanese) {
        line("font-fix: no Japanese characters in destination; unchanged");
        return;
    }

    DWORD_PTR old = 0;
    if (!SendMessageTimeoutW(hwnd, WM_GETFONT, 0, 0,
             SMTO_ABORTIFHUNG | SMTO_BLOCK, 750, &old)) {
        line("font-fix: failed to read current EDIT font; unchanged");
        return;
    }

    previous_font = (HFONT)(UINT_PTR)old;
    char detail[320];
    snprintf(detail, sizeof(detail), "font-fix: old-font-is-null=%d",
             previous_font == NULL ? 1 : 0);
    line(detail);

    // Only intervene when this specific edit field cannot draw Japanese.
    // The font selected through WM_GETFONT may be NULL; in that case the
    // edit control is using a stock font ("System" in the v3 phone report).
    HDC existingDC = GetDC(hwnd);
    if (existingDC) {
        HGDIOBJ beforeSelection = previous_font
            ? SelectObject(existingDC, previous_font) : NULL;
        const wchar_t originalGlyphs[] =
            L"\x5e7b\x60f3\x4eba\x5f62\x6f14\x821e";
        WORD beforeIndices[6] = {0};
        DWORD beforeResult = GetGlyphIndicesW(existingDC, originalGlyphs, 6,
                 beforeIndices, GGI_MARK_NONEXISTING_GLYPHS);
        int beforeMissing = 0;
        for(int i=0;i<6;i++) if (beforeIndices[i] == 0xffff) beforeMissing++;
        snprintf(detail, sizeof(detail),
            "font-fix: old-font missing_japanese=%d gdi_error=%d",
            beforeMissing, beforeResult == GDI_ERROR);
        line(detail);
        if (beforeSelection && beforeSelection != HGDI_ERROR)
            SelectObject(existingDC, beforeSelection);
        ReleaseDC(hwnd, existingDC);
        if (beforeResult != GDI_ERROR && beforeMissing == 0) {
            line("font-fix: existing edit font supports Japanese; no modification required");
            return;
        }
    }

    HFONT japanese = CreateFontW(
        -15, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        SHIFTJIS_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"IPAPGothic");
    if (!japanese) { line("font-fix: CreateFontW failed; unchanged"); return; }

    HDC dc = GetDC(hwnd);
    if (!dc) {
        line("font-fix: unable to inspect new font DC; unchanged");
        DeleteObject(japanese);
        return;
    }
    HGDIOBJ previous = SelectObject(dc, japanese);
    wchar_t fontFace[LF_FACESIZE] = {0};
    GetTextFaceW(dc, LF_FACESIZE, fontFace);
    const wchar_t japaneseSample[] =
        L"\x5e7b\x60f3\x4eba\x5f62\x6f14\x821e";
    WORD indices[6] = {0};
    DWORD glyphs = GetGlyphIndicesW(
        dc, japaneseSample, 6, indices, GGI_MARK_NONEXISTING_GLYPHS);
    unsigned missing = 0;
    for(int i=0;i<6;i++) if (indices[i] == 0xffff) missing++;
    char face[200]; utf8(fontFace,face,sizeof(face));
    snprintf(detail,sizeof(detail),
             "font-fix: selected-font=%s glyph-missing=%u gdi-error=%d",
             face, missing, glyphs == GDI_ERROR);
    line(detail);
    if (previous && previous != HGDI_ERROR) SelectObject(dc, previous);
    ReleaseDC(hwnd, dc);
    if (glyphs == GDI_ERROR || missing != 0) {
        line("font-fix: new font unsuitable; installer left unchanged");
        DeleteObject(japanese);
        return;
    }

    DWORD_PTR result = 0;
    if (!SendMessageTimeoutW(hwnd, WM_SETFONT,
            (WPARAM)japanese, (LPARAM)TRUE,
            SMTO_ABORTIFHUNG | SMTO_BLOCK, 850, &result)) {
        line("font-fix: WM_SETFONT timed out; installer left unchanged");
        DeleteObject(japanese);
        return;
    }
    DWORD_PTR verified = 0;
    int readBack = SendMessageTimeoutW(hwnd, WM_GETFONT, 0, 0,
                         SMTO_ABORTIFHUNG | SMTO_BLOCK, 850, &verified) != 0;
    wchar_t check[2048] = {0};
    DWORD_PTR count = 0;
    int textOK = SendMessageTimeoutW(hwnd, WM_GETTEXT, 2048,
                          (LPARAM)check, SMTO_ABORTIFHUNG | SMTO_BLOCK,
                          850, &count) != 0;
    if (!readBack || (HFONT)(UINT_PTR)verified != japanese ||
        !textOK || wcscmp(check,originalText) != 0) {
        // Must never rewrite or damage the install directory.
        SendMessageTimeoutW(hwnd, WM_SETFONT,
                (WPARAM)previous_font, (LPARAM)TRUE,
                SMTO_ABORTIFHUNG | SMTO_BLOCK, 850, &result);
        line("font-fix: verification failed; restored original font and left path unchanged");
        DeleteObject(japanese);
        return;
    }
    repaired_edit = hwnd;
    repaired_font = japanese;
    line("font-fix: SUCCESS: TEdit now uses IPAPGothic; original Japanese directory confirmed unchanged");
    InvalidateRect(hwnd, NULL, TRUE);
    UpdateWindow(hwnd);
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
       "touhou-probe-v4 GetACP=%u GetOEMCP=%u GetUserDefaultUILanguage=%04X GetSystemDefaultUILanguage=%04X",
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
    if (repaired_font && repaired_edit) {
        line("font-fix: retaining font handle while installer control exists.");
        while (IsWindow(repaired_edit)) Sleep(1000);
        DeleteObject(repaired_font);
        line("font-fix: installer control closed, released temporary Japanese font.");
    }
    CloseHandle(log_handle);
    return snapshots > 0 ? 0 : 1;
}
