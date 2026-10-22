/*
 * Touhou-only compatibility hook for the original TPDP Inno Setup wizard.
 * This DLL is injected solely into the known installer's GUI thread via a
 * thread-specific WH_GETMESSAGE hook. The installed game / directory / text /
 * registry is never modified; only the destination TEdit's HFONT is changed
 * and checked. No global hook, networking or persistence.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

static HFONT chosen_font = NULL;
static int checked = 0;

static void report(const char *message) {
    HANDLE f = CreateFileW(L"C:\\touhou_font_hook.log", FILE_APPEND_DATA,
                  FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS,
                  FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD written;
    WriteFile(f, message, (DWORD)lstrlenA(message), &written, NULL);
    WriteFile(f, "\r\n", 2, &written, NULL);
    CloseHandle(f);
}
static int path_text(const wchar_t *text) {
    if (!text || text[0] != L'C' || text[1] != L':' || text[2] != L'\\') return 0;
    return wcsstr(text, L"FocasLens") != NULL &&
        wcsstr(text, L"\x5E7B\x60F3\x4EBA\x5F62\x6F14\x821E") != NULL;
}
static BOOL CALLBACK edit_callback(HWND hwnd, LPARAM ignored) {
    (void)ignored;
    wchar_t klass[100]={0}, before[1024]={0}, after[1024]={0};
    if (!GetClassNameW(hwnd, klass, 99) || !wcsstr(klass,L"Edit")) return TRUE;
    if (!GetWindowTextW(hwnd,before,1023) || !path_text(before)) return TRUE;
    if (chosen_font) return FALSE;
    report("hook-v1: target TEdit found in original installer thread");
    HFONT original = (HFONT)SendMessageW(hwnd, WM_GETFONT, 0, 0);
    HDC dc = GetDC(hwnd);
    if(!dc) { report("hook-v1: edit GDI DC not available"); return FALSE; }
    HFONT desired = CreateFontW(-15,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,
         SHIFTJIS_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,
         DEFAULT_QUALITY,DEFAULT_PITCH|FF_SWISS,L"IPAPGothic");
    if(!desired) {
        report("hook-v1: CreateFontW failed");
        ReleaseDC(hwnd,dc);
        return FALSE;
    }
    HGDIOBJ old = SelectObject(dc,desired);
    wchar_t chosen[LF_FACESIZE]={0};
    GetTextFaceW(dc,LF_FACESIZE,chosen);
    WORD glyphs[6]={0xffff,0xffff,0xffff,0xffff,0xffff,0xffff};
    const wchar_t sample[]=L"\x5E7B\x60F3\x4EBA\x5F62\x6F14\x821E";
    DWORD result=GetGlyphIndicesW(dc,sample,6,glyphs,GGI_MARK_NONEXISTING_GLYPHS);
    int missing=0;
    for(int i=0;i<6;i++) if(glyphs[i]==0xffff) missing++;
    if(old && old!=HGDI_ERROR) SelectObject(dc,old);
    ReleaseDC(hwnd,dc);
    if(result==GDI_ERROR || missing>0 || wcscmp(chosen,L"IPAPGothic")!=0) {
        char msg[180];
        snprintf(msg,sizeof(msg),
          "hook-v1: font unavailable or lacks glyphs (missing=%d,gdi_error=%d); unchanged",
          missing, result==GDI_ERROR);
        report(msg);
        DeleteObject(desired);
        return FALSE;
    }
    SendMessageW(hwnd,WM_SETFONT,(WPARAM)desired,TRUE);
    HFONT applied=(HFONT)SendMessageW(hwnd,WM_GETFONT,0,0);
    GetWindowTextW(hwnd,after,1023);
    if(applied!=desired || wcscmp(before,after)!=0) {
        SendMessageW(hwnd,WM_SETFONT,(WPARAM)original,TRUE);
        report("hook-v1: font/path verification failed; original font restored");
        DeleteObject(desired);
        return FALSE;
    }
    chosen_font=desired;
    report("hook-v1: SUCCESS applied IPAPGothic to path edit; original Unicode destination unchanged");
    InvalidateRect(hwnd,NULL,TRUE);
    return FALSE;
}
static BOOL CALLBACK wizard_callback(HWND hwnd, LPARAM ignored) {
    (void)ignored;
    wchar_t classname[128]={0};
    if(GetClassNameW(hwnd,classname,127) &&
       wcsstr(classname,L"TWizardForm"))
        EnumChildWindows(hwnd,edit_callback,0);
    return TRUE;
}
__declspec(dllexport) LRESULT CALLBACK TouhouFontHook(int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam; (void)lParam;
    if(nCode>=0 && !checked) {
        checked=1;
        report("hook-v1: callback executing within installer GUI thread");
        EnumThreadWindows(GetCurrentThreadId(),wizard_callback,0);
        if(!chosen_font) report("hook-v1: no suitable path edit or font found");
    }
    return CallNextHookEx(NULL,nCode,wParam,lParam);
}
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID reserved) {
    (void)h; (void)reserved;
    if(reason==DLL_PROCESS_DETACH && chosen_font) {
        // Windows has already torn down the installer's control at exit.
        DeleteObject(chosen_font);
        chosen_font=NULL;
    }
    return TRUE;
}
