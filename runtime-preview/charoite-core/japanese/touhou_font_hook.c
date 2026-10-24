/*
 * Charoite Portal scoped Touhou Inno Setup Japanese GDI compatibility v8.
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
 * This code runs exclusively when the local scoped font probe has discovered
 * the Inno TWizardForm and started a thread-local hook. Original listbox items,
 * Win32 text, game files and checkbox states are never rewritten.
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
static HWND diagnosed_lists[12] = {0};
static int diagnosed_count[12] = {0};
static BOOL draw_seen = FALSE;
static BOOL undrawable_reported = FALSE;
static BOOL group_header_logged = FALSE;
/*
 * Real installer paint audit. WM_DRAWITEM reaches the parent TWizardForm.
 * Capture the HDC's font before / after its original WndProc as evidence for
 * the charset mismatch seen in the synthetic GDI test. Those snapshots do
 * not intercept individual DrawTextA or ExtTextOutA calls; the component may
 * select and restore a temporary font during painting.
 * Restrict to one sample per stage and checklist row, never log user text.
 */
static BOOL paint_audit_seen[2][2]={{FALSE,FALSE},{FALSE,FALSE}};
static BOOL paint_audit_started=FALSE;

/*
 * Strictly scoped Japanese installer pre-paint experiment. The v7 audit
 * proved row 1 sometimes ENTERS WM_DRAWITEM with GDI charset 0 while
 * the item caption itself is intact UTF-16 Japanese.
 *
 * Preserve the original HDC state with SaveDC and restore it from the
 * paired WH_CALLWNDPROCRET hook. No persisted font substitution, message
 * text change, or Wine/global GDI modification. Active only under ACP 932,
 * the verified Inno TWizardForm, and an owner-drawn Japanese task caption.
 */
#define MAX_PREPAINT 12
typedef struct {
    HDC hdc;
    HWND hwnd;
    UINT item;
    int saved;
} PrepaintState;
static PrepaintState prepaintStack[MAX_PREPAINT];
static int prepaintDepth=0;
static HFONT prepaintJapaneseFont=NULL;
static BOOL prepaintLogged[3]={FALSE,FALSE,FALSE};
static BOOL prepaintSkipped[3]={FALSE,FALSE,FALSE};
static BOOL prepaintRestored[3]={FALSE,FALSE,FALSE};

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
    if (!(contains(klass,L"CheckListBox") || contains(klass,L"ChecklistBox"))) return;
    int count=(int)SendMessageW(hwnd,LB_GETCOUNT,0,0);
    if(count<=0 || count>200) return;
    int slot=-1;
    for(int i=0;i<12;i++) {
        if(diagnosed_lists[i]==hwnd) { slot=i; break; }
        if(!diagnosed_lists[i] && slot<0) slot=i;
    }
    if(slot<0 || (diagnosed_lists[slot]==hwnd && diagnosed_count[slot]==count))
        return;
    diagnosed_lists[slot]=hwnd;
    diagnosed_count[slot]=count;

    LONG_PTR style=GetWindowLongPtrW(hwnd,GWL_STYLE);
    char info[512];
    snprintf(info,sizeof(info),
        "hook-v8 checklist slot=%d item_count=%d style=0x%llX has_strings=%d ownerdraw=%d",
        slot,count,(unsigned long long)style,
        !!(style & LBS_HASSTRINGS),
        !!(style & (LBS_OWNERDRAWFIXED|LBS_OWNERDRAWVARIABLE)));
    report(info);
    for(int item=0;item<count && item<8;item++) {
        wchar_t value[512]={0};
        if(!read_task_caption(hwnd,(UINT)item,value,512)) {
            report("hook-v8 list label unavailable through LB_GETTEXT; no unsafe item-data access");
            continue;
        }
        size_t at=(size_t)snprintf(info,sizeof(info),"task-%d utf16=",item);
        for(unsigned i=0;value[i] && i<52 && at+7<sizeof(info);i++)
            at+=(size_t)snprintf(info+at,sizeof(info)-at,"%04X ",(unsigned)value[i]);
        report(info);
        wchar_t recovered[512]={0};
        if(restore_shiftjis_caption(value,recovered,512)) {
            size_t pos=(size_t)snprintf(info,sizeof(info),"task-%d recovered_utf16=",item);
            for(unsigned i=0;recovered[i] && i<52 && pos+7<sizeof(info);i++)
                pos+=(size_t)snprintf(info+pos,sizeof(info)-pos,"%04X ",(unsigned)recovered[i]);
            report(info);
        } else report("hook-v8 task not losslessly recoverable as CP1252-to-CP932");
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
                report("hook-v8 repaired reversible mojibake on static caption");
            } else {
                SetWindowTextW(hwnd,before);
                report("hook-v8 static caption repair verification failed; restored");
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
        report("hook-v8 control verification failed; original font restored");
        return TRUE;
    }
    patched_windows[patched_count]=hwnd;
    patched_fonts[patched_count]=japanese;
    patched_count++;
    if (patched_count < 25 || patched_count % 25 == 0) {
        char info[200];
        snprintf(info,sizeof(info),
            "hook-v8 installed Japanese font on control=%u task_list=%d",
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
        report("hook-v8 Japanese installer TWizardForm found; scanning ALL text controls");
    }
    EnumChildWindows(hwnd,control_callback,0);
    return TRUE;
}

__declspec(dllexport) LRESULT CALLBACK TouhouFontHook(int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam; (void)lParam;
    if (nCode>=0) {
        DWORD now=GetTickCount();
        // Quickly attach a Japanese-capable font while the Inno wizard is
        // still constructing the page; throttle scans once tasks are present.
        DWORD interval=(diagnosed_count[0]>0 ? 300 : 100);
        if (!scan_started || now-last_scan_tick >= interval) {
            scan_started=TRUE;
            last_scan_tick=now;
            EnumThreadWindows(GetCurrentThreadId(),wizard_callback,0);
        }
    }
    return CallNextHookEx(NULL,nCode,wParam,lParam);
}



/*
 * Safely inspect first two Inno checklist rows, only on the identified
 * installer's UI thread and never in another application's listbox.
 * All getters are read-only; no font, checkbox or user text is modified.
 */
static void audit_installer_paint(const DRAWITEMSTRUCT *item, int stage) {
    if(!item || !item->hDC || !item->hwndItem ||
       item->CtlType!=ODT_LISTBOX || item->itemID>1 ||
       item->itemID==(UINT)-1 || (stage!=0 && stage!=1) ||
       paint_audit_seen[stage][item->itemID] ||
       GetWindowThreadProcessId(item->hwndItem,NULL)!=GetCurrentThreadId() ||
       !installer_task_list(item->hwndItem)) return;
    paint_audit_seen[stage][item->itemID]=TRUE;

    wchar_t original[512]={0};
    BOOL hasCaption=read_task_caption(item->hwndItem,item->itemID,original,512);
    HFONT contextFont=(HFONT)GetCurrentObject(item->hDC,OBJ_FONT);
    HFONT listFont=(HFONT)SendMessageW(item->hwndItem,WM_GETFONT,0,0);
    LOGFONTW contextSpec={0}, listSpec={0};
    BOOL contextOk=contextFont &&
        GetObjectW(contextFont,sizeof(contextSpec),&contextSpec)==sizeof(contextSpec);
    BOOL listOk=listFont &&
        GetObjectW(listFont,sizeof(listSpec),&listSpec)==sizeof(listSpec);
    wchar_t mapped[LF_FACESIZE]={0};
    GetTextFaceW(item->hDC,LF_FACESIZE,mapped);
    char mappedUtf8[160]={0};
    if(!WideCharToMultiByte(CP_UTF8,0,mapped,-1,mappedUtf8,
                          sizeof(mappedUtf8),NULL,NULL))
        lstrcpynA(mappedUtf8,"(unavailable)",sizeof(mappedUtf8));
    int dcCharset=GetTextCharset(item->hDC);
    /*
     * We know ANSI_CHARSET 0 selects Windows-1252 and SHIFTJIS_CHARSET
     * 128 selects CP932 under this Wine build, as the user's test proved.
     * Avoid claiming GDI call-site charset from the WM_DRAWITEM boundary.
     */
    char line[560];
    snprintf(line,sizeof(line),
        "hook-v8 paint-audit phase=%s row=%u dc_charset=%d dc_font_charset=%d list_font_charset=%d dc_face=%s caption_present=%d japanese_utf16=%d font_handles_equal=%d context_font_ok=%d list_font_ok=%d",
        stage==0?"before":"after",(unsigned)item->itemID,
        dcCharset,contextOk?(int)contextSpec.lfCharSet:-1,
        listOk?(int)listSpec.lfCharSet:-1,mappedUtf8,
        hasCaption!=FALSE,hasCaption && contains_japanese(original),
        contextFont!=NULL && contextFont==listFont,
        contextOk!=FALSE,listOk!=FALSE);
    report(line);
    if(!paint_audit_started) {
        paint_audit_started=TRUE;
        report("hook-v8: paint boundary snapshots cannot prove a transient GDI font used inside Delphi DrawTextA; comparing them with the synthetic ANSI_CHARSET reproduction");
    }
}


/*
 * The installer can create the checklist before its WM_SETFONT correction
 * arrives. Use a dedicated SHIFTJIS_CHARSET IPAPGothic font for that narrow
 * first-draw window. Leave the original HFONT untouched and owned by VCL.
 */
static HFONT get_prepaint_japanese_font(HWND list) {
    if(prepaintJapaneseFont)return prepaintJapaneseFont;
    LOGFONTW spec;
    ZeroMemory(&spec,sizeof(spec));
    HFONT controlFont=(HFONT)SendMessageW(list,WM_GETFONT,0,0);
    if(!controlFont ||
       GetObjectW(controlFont,sizeof(spec),&spec)!=sizeof(spec)) {
        spec.lfHeight=-15;
        spec.lfWeight=FW_NORMAL;
        spec.lfPitchAndFamily=DEFAULT_PITCH|FF_SWISS;
    }
    spec.lfCharSet=SHIFTJIS_CHARSET;
    lstrcpynW(spec.lfFaceName,L"IPAPGothic",LF_FACESIZE);
    prepaintJapaneseFont=CreateFontIndirectW(&spec);
    return prepaintJapaneseFont;
}

static void select_japanese_before_installer_draw(const DRAWITEMSTRUCT *item) {
    if(!item || !item->hDC || !item->hwndItem ||
       item->CtlType!=ODT_LISTBOX || item->itemID==(UINT)-1 ||
       item->itemID>=3 || GetACP()!=932 ||
       prepaintDepth>=MAX_PREPAINT ||
       GetWindowThreadProcessId(item->hwndItem,NULL)!=GetCurrentThreadId() ||
       !installer_task_list(item->hwndItem) ||
       !(GetWindowLongPtrW(item->hwndItem,GWL_STYLE)&LBS_HASSTRINGS))
        return;
    wchar_t text[512]={0};
    if(!read_task_caption(item->hwndItem,item->itemID,text,512) ||
       !contains_japanese(text))return;

    int oldCharset=GetTextCharset(item->hDC);
    if(oldCharset==SHIFTJIS_CHARSET) {
        if(!prepaintSkipped[item->itemID]) {
            prepaintSkipped[item->itemID]=TRUE;
            char msg[144];
            snprintf(msg,sizeof(msg),
               "hook-v8 prepaint row=%u already-shiftjis=128; no font change",
               (unsigned)item->itemID);
            report(msg);
        }
        return;
    }

    HFONT replacement=get_prepaint_japanese_font(item->hwndItem);
    if(!replacement) {
        report("hook-v8 prepaint skipped: could not create Japanese font");
        return;
    }
    int saved=SaveDC(item->hDC);
    if(!saved)return;
    HGDIOBJ previous=SelectObject(item->hDC,replacement);
    if(!previous || previous==HGDI_ERROR ||
       GetTextCharset(item->hDC)!=SHIFTJIS_CHARSET) {
        RestoreDC(item->hDC,saved);
        if(!prepaintSkipped[item->itemID]) {
            prepaintSkipped[item->itemID]=TRUE;
            report("hook-v8 prepaint rejected: temporary font does not resolve to SHIFTJIS");
        }
        return;
    }
    PrepaintState *entry=&prepaintStack[prepaintDepth++];
    entry->hwnd=item->hwndItem;
    entry->item=item->itemID;
    entry->hdc=item->hDC;
    entry->saved=saved;
    if(!prepaintLogged[item->itemID]) {
        prepaintLogged[item->itemID]=TRUE;
        char line[196];
        snprintf(line,sizeof(line),
            "hook-v8 prepaint selected SHIFTJIS font before Delphi draw row=%u old_charset=%d new_charset=%d",
            (unsigned)item->itemID,oldCharset,GetTextCharset(item->hDC));
        report(line);
    }
}

/*
 * Run only in the paired post-draw hook. The fallback draws AFTER this
 * restoration, and independently selects its own Japanese font.
 */
static void restore_installer_prepaint(const DRAWITEMSTRUCT *item) {
    if(!item || !item->hDC || !item->hwndItem ||
       item->itemID==(UINT)-1)return;
    for(int slot=prepaintDepth-1;slot>=0;slot--) {
        PrepaintState *entry=&prepaintStack[slot];
        if(entry->hdc!=item->hDC || entry->hwnd!=item->hwndItem ||
           entry->item!=item->itemID)continue;
        int before=GetTextCharset(item->hDC);
        BOOL ok=RestoreDC(item->hDC,entry->saved);
        UINT row=item->itemID;
        for(int next=slot+1;next<prepaintDepth;next++)
            prepaintStack[next-1]=prepaintStack[next];
        prepaintDepth--;
        if(row<3 && !prepaintRestored[row]) {
            prepaintRestored[row]=TRUE;
            char msg[210];
            snprintf(msg,sizeof(msg),
                "hook-v8 prepaint restored original DC row=%u success=%d charset_after_delphi=%d charset_restored=%d",
                (unsigned)row,(int)ok,before,GetTextCharset(item->hDC));
            report(msg);
        }
        return;
    }
}

__declspec(dllexport) LRESULT CALLBACK TouhouAuditHook(
        int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam;
    if(nCode>=0 && lParam) {
        const CWPSTRUCT *event=(const CWPSTRUCT *)lParam;
        if(event->message==WM_DRAWITEM && event->lParam) {
            const DRAWITEMSTRUCT *item=(const DRAWITEMSTRUCT *)event->lParam;
            audit_installer_paint(item,0);
            select_japanese_before_installer_draw(item);
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
    wchar_t original[512]={0}, repaired[512]={0};
    if (!read_task_caption(item->hwndItem,item->itemID,original,512))
        return FALSE;
    /*
     * The FocasLens installer provides VALID Japanese UTF-16 in LB_GETTEXT.
     * Its checkbox captions are corrupted only by Delphi/Wine owner drawing.
     * Always prioritize that exact original UTF-16 over ANSI recovery.
     * Only use reversible CP1252->CP932 as fallback for a different installer.
     */
    const wchar_t *label=original;
    BOOL originally_japanese=contains_japanese(original);
    if (!originally_japanese) {
        if (!restore_shiftjis_caption(original,repaired,512)) return FALSE;
        label=repaired;
    }

    /*
     * Inno task-list row zero is a plain section header ("Add icons:"),
     * not a selectable checkbox. The previous overlay erased only text to
     * the RIGHT of the checkbox gutter, leaving the Wine-rendered "|A|C|"
     * debris in the header's left edge. Repaint the entire header text area
     * only for an unselected, colon-terminated first row. All checkbox
     * rows retain their original checkbox gutter and clickable state.
     */
    size_t label_len=wcslen(label);
    BOOL section_header=(item->itemID==0 &&
            !(item->itemState & ODS_SELECTED) &&
            label_len>0 &&
            (label[label_len-1]==L':' || label[label_len-1]==0xff1a));
    RECT region=item->rcItem;
    region.left+=section_header ? 2 : GetSystemMetrics(SM_CXMENUCHECK)+14;
    region.top+=2;
    region.bottom-=2;
    region.right-=2;
    if(region.left>=region.right || region.top>=region.bottom) return FALSE;

    // Keep the checkmark, selection state and focus border drawn by Inno.
    HDC dc=item->hDC;
    HFONT selected=(HFONT)SendMessageW(item->hwndItem,WM_GETFONT,0,0);
    if(!selected || !font_has_japanese(item->hwndItem,selected))
        return FALSE;
    int saved=SaveDC(dc);
    if(!saved) return FALSE;
    HGDIOBJ prior=SelectObject(dc,selected);
    if(!prior || prior==HGDI_ERROR) {
        RestoreDC(dc,saved);
        return FALSE;
    }

    // Paint the text portion only; preserve the existing checkmark, row
    // selection, focus outline, item data and item check state.
    COLORREF bg=(item->itemState & ODS_SELECTED)
            ? GetSysColor(COLOR_HIGHLIGHT) : GetBkColor(dc);
    if(bg==CLR_INVALID) bg=GetSysColor(COLOR_WINDOW);
    COLORREF fg=(item->itemState & ODS_SELECTED)
            ? GetSysColor(COLOR_HIGHLIGHTTEXT) : GetTextColor(dc);
    HBRUSH brush=CreateSolidBrush(bg);
    if(!brush) {
        RestoreDC(dc,saved);
        return FALSE;
    }
    FillRect(dc,&region,brush);
    DeleteObject(brush);
    SetBkMode(dc,TRANSPARENT);
    SetTextColor(dc,fg==CLR_INVALID ? GetSysColor(COLOR_WINDOWTEXT) : fg);
    int drawn=DrawTextW(dc,label,-1,&region,
            DT_SINGLELINE|DT_VCENTER|DT_LEFT|DT_NOPREFIX|DT_END_ELLIPSIS);
    RestoreDC(dc,saved);
    if(section_header && drawn>0 && !group_header_logged) {
        group_header_logged=TRUE;
        report("hook-v8: complete unselected section heading repainted; no checkbox area modified");
    }
    return drawn>0;
}

__declspec(dllexport) LRESULT CALLBACK TouhouDrawHook(
        int nCode, WPARAM wParam, LPARAM lParam) {
    (void)wParam;
    if(nCode>=0 && lParam) {
        const CWPRETSTRUCT *event=(const CWPRETSTRUCT *)lParam;
        if(event->message==WM_DRAWITEM && event->lParam) {
            const DRAWITEMSTRUCT *item=(const DRAWITEMSTRUCT *)event->lParam;
            audit_installer_paint(item,1);
            restore_installer_prepaint(item);
            if(item->CtlType==ODT_LISTBOX && item->hwndItem &&
                    installer_task_list(item->hwndItem) && !draw_seen) {
                draw_seen=TRUE;
                report("hook-v8 owner-draw checklist paint event detected");
            }
            if(item->CtlType==ODT_LISTBOX && item->hwndItem &&
                    installer_task_list(item->hwndItem) &&
                    !(GetWindowLongPtrW(item->hwndItem,GWL_STYLE)&LBS_HASSTRINGS) &&
                    !undrawable_reported) {
                undrawable_reported=TRUE;
                report("hook-v8 owner-draw has no LBS_HASSTRINGS; source captions require deeper Delphi diagnostics");
            }
            static BOOL logged=FALSE;
            if(draw_recovered_task((const DRAWITEMSTRUCT *)event->lParam) && !logged) {
                logged=TRUE;
                report("hook-v8: rendered original Unicode or strictly reversible Japanese task label; installer data unchanged");
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
        if(prepaintJapaneseFont)DeleteObject(prepaintJapaneseFont);
    }
    return TRUE;
}
