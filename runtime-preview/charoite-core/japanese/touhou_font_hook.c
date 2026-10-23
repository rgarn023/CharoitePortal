/*
 * Charoite Portal scoped Touhou Inno Setup Japanese GDI compatibility v3.
 *
 * The original v1 hook only updated the installation-path TEdit. Screens
 * farther into the Inno wizard (notably Select Additional Tasks) use owner-
 * drawn TNewCheckListBox, static/checkbox controls with DIFFERENT GDI fonts.
 * Assign a Japanese TrueType font inside the installer's own GUI thread for
 * those controls as pages appear. Do not edit executable files, strings,
 * paths, system settings or controls in any other process. Version 3 also
 * repairs reversible CP1252-to-CP932 mojibake on installer task labels at
 * paint time, without modifying listbox data, checkbox state or game files.
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

static BOOL restore_shiftjis_caption(const wchar_t *, wchar_t *, int);
static BOOL read_task_caption(HWND, UINT, wchar_t *, int);

/* Used to differentiate a font failure from already-mojibake Unicode data.
 * Records hex codes, not user text or file paths. */
static void task_list_diagnostics(HWND hwnd, const wchar_t *klass) {
    if (task_list_logged || !(contains(klass,L"CheckListBox") || contains(klass,L"ChecklistBox"))) return;
    int count = (int)SendMessageW(hwnd, LB_GETCOUNT, 0, 0);
    if (count <= 0 || count > 200) return; // A hidden, empty page may precede the task page.
    task_list_logged = TRUE;
    char info[320];
    snprintf(info,sizeof(info),
        "hook-v3 task list found class=CheckListBox item_count=%d",count);
    report(info);
    for (int item=0; item<count && item<4; item++) {
        wchar_t value[304] = {0};
        if (!read_task_caption(hwnd, (UINT)item, value, 304)) {
            report("hook-v3 task item text not accessible through LB_GETTEXT; no edit attempted");
            continue;
        }
        size_t at=0;
        at += (size_t)snprintf(info,sizeof(info),"task-%d utf16=",item);
        for (unsigned i=0; value[i] && i<32 && at+7 < sizeof(info); i++)
            at += (size_t)snprintf(info+at,sizeof(info)-at,"%04X ",(unsigned)value[i]);
        report(info);
        wchar_t recovered[304]={0};
        if (restore_shiftjis_caption(value,recovered,304))
            report("hook-v3 task item has losslessly recoverable CP1252/CP932 text");
        else
            report("hook-v3 task item not losslessly CP1252/CP932 recoverable");
    }
}


/*
 * Some ANSI Inno task captions reach VCL as CP932 bytes decoded as CP1252.
 * Only recover captions with a lossless two-way conversion:
 * Unicode mojibake -> original CP1252 bytes -> CP932 Japanese -> same bytes.
 * Already-correct Japanese, ambiguous mappings and replacement characters
 * are left untouched. This deliberately does NOT affect paths or executables.
 */
static BOOL restore_shiftjis_caption(const wchar_t *wrong,
                                    wchar_t *restored, int capacity) {
    if (!wrong || !*wrong || !restored || capacity < 2 ||
            contains_japanese(wrong)) return FALSE;
    char source[2048], roundtrip[2048];
    BOOL used_default=FALSE;
    int source_len=WideCharToMultiByte(1252,WC_NO_BEST_FIT_CHARS,wrong,-1,
                               source,sizeof(source),NULL,&used_default);
    if (source_len <= 1 || used_default || source_len >= (int)sizeof(source))
        return FALSE;
    int high_bytes=0;
    for (int i=0; i<source_len-1; i++)
        if ((unsigned char)source[i]>=0x80) high_bytes++;
    if (high_bytes < 2) return FALSE;

    int units=MultiByteToWideChar(932,MB_ERR_INVALID_CHARS,source,source_len,
                                  restored,capacity);
    if (units<=1) return FALSE;
    int japanese=0;
    for (int i=0; i<units-1; i++) {
        if ((restored[i]>=0x3040 && restored[i]<=0x30ff) ||
            (restored[i]>=0x3400 && restored[i]<=0x9fff)) japanese++;
        if (restored[i]==0xfffd) return FALSE;
    }
    if (japanese<2) return FALSE;
    used_default=FALSE;
    int len=WideCharToMultiByte(932,WC_NO_BEST_FIT_CHARS,restored,-1,
                     roundtrip,sizeof(roundtrip),NULL,&used_default);
    return !used_default && len==source_len &&
            memcmp(source,roundtrip,source_len)==0;
}

static BOOL read_task_caption(HWND hwnd, UINT index, wchar_t *text, int limit) {
    if (!text || limit<2 || !(GetWindowLongPtrW(hwnd,GWL_STYLE)&LBS_HASSTRINGS))
        return FALSE;
    LRESULT length=SendMessageW(hwnd,LB_GETTEXTLEN,index,0);
    if(length<=0 || length>=limit) return FALSE;
    ZeroMemory(text,(size_t)limit*sizeof(wchar_t));
    LRESULT read=SendMessageW(hwnd,LB_GETTEXT,index,(LPARAM)text);
    return read>0 && read<limit && text[0] && text[limit-1]==0;
}

static BOOL installer_task_list(HWND hwnd) {
    wchar_t klass[128]={0};
    if (!GetClassNameW(hwnd,klass,127) ||
        !(contains(klass,L"CheckListBox") || contains(klass,L"ChecklistBox")))
        return FALSE;
    // Never draw on other applications or generic Wine UI.
    for (HWND parent=hwnd; parent; parent=GetParent(parent)) {
        wchar_t parent_class[128]={0};
        if (GetClassNameW(parent,parent_class,127) &&
            contains(parent_class,L"TWizardForm")) return TRUE;
    }
    return FALSE;
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
    if (patched_count >= MAX_PATCHED_CONTROLS) return TRUE;
    wchar_t klass[128]={0}, before[1024]={0}, after[1024]={0};
    if (!GetClassNameW(hwnd,klass,127) || !is_text_control(klass))
        return TRUE;
    BOOL task = is_task_list(klass);
    // A task list can be created before its items; retry diagnostics even
    // after its font has been patched, once options have populated.
    if (task) task_list_diagnostics(hwnd,klass);
    if (already_patched(hwnd)) return TRUE;

    int units=GetWindowTextW(hwnd,before,1023);
    BOOL text_japanese=(units > 0 && contains_japanese(before));
    /* Correct only static explanatory captions, never installer input, edit
     * boxes, checkbox state, file paths or clickable button labels. */
    if (!task && !text_japanese &&
            (contains(klass,L"StaticText") || contains(klass,L"Label"))) {
        wchar_t repaired[1024]={0};
        if (restore_shiftjis_caption(before,repaired,1024)) {
            SetWindowTextW(hwnd,repaired);
            if (GetWindowTextW(hwnd,after,1023)>0 &&
                    wcscmp(repaired,after)==0) {
                lstrcpynW(before,repaired,1024);
                text_japanese=TRUE;
                report("hook-v3 repaired reversible mojibake on static caption");
            } else {
                SetWindowTextW(hwnd,before);
                report("hook-v3 static caption repair verification failed; restored");
            }
        }
    }
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
        report("hook-v3 control verification failed; original font restored");
        return TRUE;
    }
    patched_windows[patched_count]=hwnd;
    patched_fonts[patched_count]=japanese;
    patched_count++;
    if (patched_count < 25 || patched_count % 25 == 0) {
        char info[200];
        snprintf(info,sizeof(info),
            "hook-v3 installed Japanese font on control=%u task_list=%d",
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
        report("hook-v3 Japanese installer TWizardForm found; scanning ALL text controls");
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


/*
 * Owner-drawn checklist items send WM_DRAWITEM to their parent. A thread-only
 * WH_CALLWNDPROCRET callback sees the completed draw while its DRAWITEMSTRUCT
 * and HDC are valid. Overlay text ONLY when CP932 recovery is fully reversible.
 * Never LB_DELETESTRING/LB_INSERTSTRING: VCL stores checkbox state and other
 * installer objects alongside its items. No changes to the underlying label,
 * selection, item data or future saved-game/installer files occur.
 */
static BOOL draw_recovered_task(const DRAWITEMSTRUCT *item) {
    if (!item || item->CtlType!=ODT_LISTBOX || !item->hwndItem ||
            !item->hDC || item->itemID==(UINT)-1 || item->itemID>200 ||
            !installer_task_list(item->hwndItem)) return FALSE;
    if (GetWindowThreadProcessId(item->hwndItem,NULL)!=GetCurrentThreadId())
        return FALSE;
    wchar_t original[512]={0}, fixed[512]={0};
    if (!read_task_caption(item->hwndItem,item->itemID,original,512) ||
            !restore_shiftjis_caption(original,fixed,512)) return FALSE;

    RECT region=item->rcItem;
    region.left+=GetSystemMetrics(SM_CXMENUCHECK)+14;
    region.top+=2;
    region.bottom-=2;
    region.right-=2;
    if(region.left>=region.right || region.top>=region.bottom) return FALSE;

    // Keep the checkmark, selection state and focus border drawn by Inno.
    HDC dc=item->hDC;
    COLORREF bg=GetBkColor(dc);
    if(bg==CLR_INVALID) bg=GetSysColor(COLOR_WINDOW);
    HBRUSH brush=CreateSolidBrush(bg);
    if(!brush) return FALSE;
    FillRect(dc,&region,brush);
    DeleteObject(brush);

    int previous=SetBkMode(dc,TRANSPARENT);
    HFONT selected=(HFONT)SendMessageW(item->hwndItem,WM_GETFONT,0,0);
    HGDIOBJ prior=selected ? SelectObject(dc,selected) : NULL;
    DrawTextW(dc,fixed,-1,&region,
            DT_SINGLELINE|DT_VCENTER|DT_LEFT|DT_NOPREFIX|DT_END_ELLIPSIS);
    if(prior && prior!=HGDI_ERROR) SelectObject(dc,prior);
    SetBkMode(dc,previous);
    return TRUE;
}

__declspec(dllexport) LRESULT CALLBACK TouhouDrawHook(
        int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam;
    if(nCode>=0 && lParam) {
        const CWPRETSTRUCT *event=(const CWPRETSTRUCT *)lParam;
        if(event->message==WM_DRAWITEM && event->lParam) {
            static BOOL logged=FALSE;
            if(draw_recovered_task((const DRAWITEMSTRUCT *)event->lParam) && !logged) {
                logged=TRUE;
                report("hook-v3: rendered recovered CP932 task label; installer data unchanged");
            }
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
