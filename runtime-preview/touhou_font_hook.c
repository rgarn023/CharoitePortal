/*
 * Charoite Portal scoped Touhou Inno Setup Japanese GDI compatibility v2.
 *
 * The original v1 hook only updated the installation-path TEdit. Screens
 * farther into the Inno wizard (notably Select Additional Tasks) use owner-
 * drawn TNewCheckListBox, static/checkbox controls with DIFFERENT GDI fonts.
 * Assign a Japanese TrueType font inside the installer's own GUI thread for
 * those controls as pages appear. Do not edit executable files, strings,
 * paths, text, system settings or controls in any other process.
 *
 * This code runs exclusively when the Touhou-specific local font probe has
 * discovered a TWizardForm for the known Japanese installer and started a
 * thread-local WH_GETMESSAGE hook. Original Win32 text is never rewritten.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>
#include <string.h>

#define MAX_PATCHED_CONTROLS 256
static HWND patched_windows[MAX_PATCHED_CONTROLS];
static HFONT patched_fonts[MAX_PATCHED_CONTROLS];
static unsigned patched_count = 0;
static DWORD last_scan_tick = 0;
static BOOL installer_verified = FALSE;
static BOOL scan_started = FALSE;
static BOOL task_list_logged = FALSE;

static void report(const char *message) {
    HANDLE f = CreateFileW(L"C:\\touhou_font_hook.log", FILE_APPEND_DATA,
                  FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS,
                  FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD written = 0;
    WriteFile(f, message, (DWORD)lstrlenA(message), &written, NULL);
    WriteFile(f, "\r\n", 2, &written, NULL);
    CloseHandle(f);
}

static BOOL contains(const wchar_t *haystack, const wchar_t *needle) {
    return haystack && needle && wcsstr(haystack, needle) != NULL;
}

/* When Wine implements a VCL control as an owner-drawn listbox, text is held
 * in list items, not WM_GETTEXT. These classes need a Japanese font even if
 * WM_GETTEXT returns empty. */
static BOOL is_task_list(const wchar_t *klass) {
    return contains(klass, L"CheckListBox") ||
           contains(klass, L"ChecklistBox") ||
           contains(klass, L"ListBox");
}

static BOOL is_text_control(const wchar_t *klass) {
    return is_task_list(klass) ||
           contains(klass, L"StaticText") ||
           contains(klass, L"Label") ||
           contains(klass, L"CheckBox") ||
           contains(klass, L"RadioButton") ||
           contains(klass, L"Button") ||
           contains(klass, L"Edit") ||
           contains(klass, L"ComboBox") ||
           contains(klass, L"Memo");
}

static BOOL already_patched(HWND hwnd) {
    for (unsigned i=0; i<patched_count; i++)
        if (patched_windows[i] == hwnd) return TRUE;
    return FALSE;
}

static BOOL contains_japanese(const wchar_t *value) {
    if (!value) return FALSE;
    for (; *value; value++) {
        if ((*value >= 0x3040 && *value <= 0x30ff) ||
            (*value >= 0x3400 && *value <= 0x9fff) ||
            (*value >= 0xff66 && *value <= 0xff9f))
            return TRUE;
    }
    return FALSE;
}

/* Used to differentiate a font failure from already-mojibake Unicode data.
 * Records hex codes, not user text or file paths. */
static void task_list_diagnostics(HWND hwnd, const wchar_t *klass) {
    if (task_list_logged || !is_task_list(klass)) return;
    task_list_logged = TRUE;
    int count = (int)SendMessageW(hwnd, LB_GETCOUNT, 0, 0);
    char info[320];
    snprintf(info,sizeof(info),
        "hook-v2 task list found class=CheckListBox item_count=%d",count);
    report(info);
    if (count <= 0 || count > 200) return;
    for (int item=0; item<count && item<4; item++) {
        LRESULT units = SendMessageW(hwnd, LB_GETTEXTLEN, item, 0);
        if (units <= 0 || units > 300) continue;
        wchar_t value[304] = {0};
        if (SendMessageW(hwnd, LB_GETTEXT, item, (LPARAM)value) < 0) continue;
        size_t at=0;
        at += (size_t)snprintf(info,sizeof(info),"task-%d utf16=",item);
        for (unsigned i=0; value[i] && i<32 && at+7 < sizeof(info); i++)
            at += (size_t)snprintf(info+at,sizeof(info)-at,"%04X ",(unsigned)value[i]);
        report(info);
    }
}

static BOOL font_has_japanese(HWND hwnd, HFONT font) {
    HDC dc=GetDC(hwnd);
    if (!dc) return FALSE;
    HGDIOBJ old=font ? SelectObject(dc,font) : NULL;
    const wchar_t example[]=L"\x5E7B\x60F3\x4EBA\x5F62\x6F14\x821E";
    WORD glyphs[6]={0xffff,0xffff,0xffff,0xffff,0xffff,0xffff};
    DWORD result=GetGlyphIndicesW(dc,example,6,glyphs,GGI_MARK_NONEXISTING_GLYPHS);
    BOOL good=(result != GDI_ERROR);
    for(int i=0;i<6;i++) if(glyphs[i]==0xffff) good=FALSE;
    if(old && old != HGDI_ERROR) SelectObject(dc,old);
    ReleaseDC(hwnd,dc);
    return good;
}

static BOOL CALLBACK control_callback(HWND hwnd, LPARAM data) {
    (void)data;
    if (patched_count >= MAX_PATCHED_CONTROLS || already_patched(hwnd))
        return TRUE;
    wchar_t klass[128]={0}, before[1024]={0}, after[1024]={0};
    if (!GetClassNameW(hwnd,klass,127) || !is_text_control(klass))
        return TRUE;
    BOOL task = is_task_list(klass);
    if (task) task_list_diagnostics(hwnd,klass);

    int units=GetWindowTextW(hwnd,before,1023);
    BOOL text_japanese=(units > 0 && contains_japanese(before));
    /* Also cover Delphi's custom task list, where labels live in LB items. */
    if (!task && !text_japanese) return TRUE;
    HFONT original=(HFONT)SendMessageW(hwnd,WM_GETFONT,0,0);
    if (!task && original && font_has_japanese(hwnd,original)) return TRUE;

    LOGFONTW face;
    ZeroMemory(&face,sizeof(face));
    if (!original || GetObjectW(original,sizeof(face),&face)!=sizeof(face)) {
        face.lfHeight=-15;
        face.lfWeight=FW_NORMAL;
        face.lfPitchAndFamily=DEFAULT_PITCH|FF_SWISS;
    }
    face.lfCharSet=SHIFTJIS_CHARSET;
    lstrcpynW(face.lfFaceName,L"IPAPGothic",LF_FACESIZE);
    HFONT japanese=CreateFontIndirectW(&face);
    if (!japanese) return TRUE;
    if (!font_has_japanese(hwnd,japanese)) {
        DeleteObject(japanese);
        return TRUE;
    }
    SendMessageW(hwnd,WM_SETFONT,(WPARAM)japanese,TRUE);

    // Confirm the Unicode text is IDENTICAL after setting the font.
    GetWindowTextW(hwnd,after,1023);
    if (wcscmp(before,after)!=0 ||
            (HFONT)SendMessageW(hwnd,WM_GETFONT,0,0)!=japanese) {
        SendMessageW(hwnd,WM_SETFONT,(WPARAM)original,TRUE);
        DeleteObject(japanese);
        report("hook-v2 control verification failed; original font restored");
        return TRUE;
    }
    patched_windows[patched_count]=hwnd;
    patched_fonts[patched_count]=japanese;
    patched_count++;
    if (patched_count < 25 || patched_count % 25 == 0) {
        char info[200];
        snprintf(info,sizeof(info),
            "hook-v2 installed Japanese font on control=%u task_list=%d",
            patched_count,(int)task);
        report(info);
    }
    InvalidateRect(hwnd,NULL,TRUE);
    return TRUE;
}

static BOOL CALLBACK wizard_callback(HWND hwnd, LPARAM data) {
    (void)data;
    wchar_t klass[128]={0};
    if (!GetClassNameW(hwnd,klass,127) || !contains(klass,L"TWizardForm"))
        return TRUE;
    // The thread-scoped helper already identified the window and process.
    // This can never affect an unrelated Wine application's UI.
    if (!installer_verified) {
        installer_verified=TRUE;
        report("hook-v2 Japanese installer TWizardForm found; scanning ALL text controls");
    }
    EnumChildWindows(hwnd,control_callback,0);
    return TRUE;
}

__declspec(dllexport) LRESULT CALLBACK TouhouFontHook(int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam; (void)lParam;
    if (nCode>=0) {
        DWORD now=GetTickCount();
        if (!scan_started || now-last_scan_tick >= 500) {
            scan_started=TRUE;
            last_scan_tick=now;
            EnumThreadWindows(GetCurrentThreadId(),wizard_callback,0);
        }
    }
    return CallNextHookEx(NULL,nCode,wParam,lParam);
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID reserved) {
    (void)h; (void)reserved;
    if(reason==DLL_PROCESS_DETACH) {
        // The controls and their original GUI process are closing. Font
        // objects are process-local; don't destroy fonts while live in use.
        for (unsigned i=0; i<patched_count; i++) {
            if (!IsWindow(patched_windows[i])) DeleteObject(patched_fonts[i]);
        }
    }
    return TRUE;
}
