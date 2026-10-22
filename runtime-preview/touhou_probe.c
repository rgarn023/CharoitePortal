/*
 * Touhou Pocket read-only Japanese installer diagnostic.
 *
 * No gameplay code, no registry writes, no changes to the installer, no network.
 * Reads the contents of target installer EDIT controls using WM_GETTEXTW.
 * Captures only UTF-16 code-unit hex plus selected font metadata (no
 * human-readable path text) and Win32 code pages into C:\touhou_probe.log.
 * Built with mingw-w64 by GitHub Actions and bundled as an independent .exe.
 *
 * The diagnostic deliberately uses the same Win32 subsystem as the installer,
 * so the observed text reflects Wine's actual ANSI -> Unicode conversion.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>
#include <stdlib.h>

static const wchar_t *output_path = L"C:\\touhou_probe.log";
static HANDLE out = INVALID_HANDLE_VALUE;
static int snapshots = 0;

static void log_line(const char *line) {
    if (out == INVALID_HANDLE_VALUE) return;
    DWORD len = (DWORD)lstrlenA(line), written = 0;
    WriteFile(out, line, len, &written, NULL);
    WriteFile(out, "\r\n", 2, &written, NULL);
    FlushFileBuffers(out);
}

static BOOL CALLBACK enumerate_edit(HWND hwnd, LPARAM lp) {
    (void)lp;
    wchar_t cls[128] = {0};
    if (!GetClassNameW(hwnd, cls, 127)) return TRUE;
    if (wcsstr(cls, L"Edit") == NULL && wcsstr(cls, L"EDIT") == NULL)
        return TRUE;

    wchar_t value[1024] = {0};
    DWORD_PTR result = 0;
    BOOL ok = SendMessageTimeoutW(hwnd, WM_GETTEXT, 1023, (LPARAM)value,
                                  SMTO_ABORTIFHUNG | SMTO_BLOCK, 500, &result) != 0;
    if (!ok || result == 0) return TRUE;

    int hasDrive = (value[0] && value[1] == L':') ||
                    wcsstr(value, L"FocasLens") != NULL;
    if (!hasDrive) return TRUE;
    char summary[4096];
    int pos = snprintf(summary, sizeof(summary),
                       "edit class=%ls utf16_units=%lu codepoints=",
                       cls, (unsigned long)result);
    for (unsigned i = 0; value[i] && i < 180 && pos < 3800; i++) {
        pos += snprintf(summary + pos, sizeof(summary) - (size_t)pos,
                        "%04X ", (unsigned)value[i]);
    }
    if (pos < (int)sizeof(summary)) summary[pos] = 0;
    log_line(summary);

    // Check Japanese glyphs in a known Unicode string with Wine's GDI,
    // independent of whatever the installer stored in its edit control.
    HDC dc = GetDC(hwnd);
    if (dc) {
        HFONT requested = (HFONT)SendMessageW(hwnd, WM_GETFONT, 0, 0);
        HFONT prior = requested ? (HFONT)SelectObject(dc, requested) : NULL;
        wchar_t face[LF_FACESIZE] = {0};
        GetTextFaceW(dc, LF_FACESIZE, face);
        const wchar_t test[] = L"\x5E7B\x60F3\x4EBA\x5F62\x6F14\x821E";
        WORD indices[6] = {0};
        DWORD glyphResult = GetGlyphIndicesW(dc, test, 6, indices,
                                               GGI_MARK_NONEXISTING_GLYPHS);
        unsigned missing = 0;
        if (glyphResult != GDI_ERROR) for (int i=0;i<6;i++) if (indices[i] == 0xFFFF) missing++;
        char glyphLine[512];
        snprintf(glyphLine, sizeof(glyphLine),
                 "selected-face=%ls japanese-test-missing-glyphs=%u gdi-error=%d",
                 face, missing, glyphResult == GDI_ERROR);
        log_line(glyphLine);
        if (prior) SelectObject(dc, prior);
        ReleaseDC(hwnd, dc);
    }
    snapshots++;
    return TRUE;
}

static BOOL CALLBACK enumerate_window(HWND hwnd, LPARAM lp) {
    (void)lp;
    if (!IsWindowVisible(hwnd)) return TRUE;
    wchar_t title[256] = {0};
    GetWindowTextW(hwnd, title, 255);
    if (!(wcsstr(title,L"\x30BB\x30C3\x30C8\x30A2\x30C3\x30D7") ||
          wcsstr(title,L"\x5E7B\x60F3\x4EBA\x5F62") ||
          wcsstr(title,L"Setup"))) return TRUE;
    EnumChildWindows(hwnd, enumerate_edit, 0);
    return TRUE;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE prior, PWSTR cmdline, int show) {
    (void)instance; (void)prior; (void)cmdline; (void)show;
    out = CreateFileW(output_path, GENERIC_WRITE, FILE_SHARE_READ, NULL,
                      CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (out == INVALID_HANDLE_VALUE) return 2;
    char header[512];
    snprintf(header, sizeof(header),
             "touhou-probe-v1 GetACP=%u GetOEMCP=%u GetUserDefaultUILanguage=%04X GetSystemDefaultUILanguage=%04X",
             GetACP(), GetOEMCP(), (unsigned)GetUserDefaultUILanguage(),
             (unsigned)GetSystemDefaultUILanguage());
    log_line(header);
    for (int pass=0; pass<24; pass++) {
        EnumWindows(enumerate_window, 0);
        if (snapshots > 0) {
            log_line("captured-edit-path; no installer data changed");
            break;
        }
        Sleep(2500);
    }
    if (snapshots == 0) log_line("No supported installer destination edit control found in 60 seconds.");
    CloseHandle(out);
    return snapshots ? 0 : 1;
}
