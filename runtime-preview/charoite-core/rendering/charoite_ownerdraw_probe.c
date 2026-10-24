/*
 * Charoite Core Windows owner-draw GDI differential test, revision 3.
 *
 * This reproduces the Win32 LISTBOX / WM_DRAWITEM control path and compares
 * DrawTextW/A, ExtTextOutW/A, TextOutW with known, valid Japanese Unicode.
 * Diagnostic-only: no hooks, no Wine binary changes, no access to games/saves.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <string.h>

#define CONTROL 201
#define PAGE_FIRST 301
#define PAGE_LAST 302
#define METHODS 11
#define PAGE_BREAK 5
static const wchar_t jp[] =
    L"\x30A2\x30A4\x30B3\x30F3\x3092\x8FFD\x52A0\x3059\x308B: "
    L"\x30C7\x30B9\x30AF\x30C8\x30C3\x30D7\x306B\x30A2\x30A4\x30B3\x30F3\x3092\x4F5C\x6210";
static const wchar_t* methods[METHODS]={
    L"DrawTextW / SHIFTJIS_CHARSET", L"DrawTextA / SHIFTJIS_CHARSET",
    L"ExtTextOutW / SHIFTJIS_CHARSET", L"ExtTextOutA / SHIFTJIS_CHARSET",
    L"TextOutW / SHIFTJIS_CHARSET",
    L"DrawTextA / DEFAULT_CHARSET", L"DrawTextA / ANSI_CHARSET",
    L"DrawTextW / DEFAULT_CHARSET",
    L"ExtTextOutA / DEFAULT_CHARSET", L"ExtTextOutA / ANSI_CHARSET",
    L"ExtTextOutW / DEFAULT_CHARSET"
};
static HWND checklist=NULL;
static HFONT japaneseFonts[3]={NULL,NULL,NULL};
static BOOL seen[METHODS]={0};
static int pageFirst=0;

static void log_message(const char *value) {
    HANDLE file=CreateFileW(L"C:\\charoite_ownerdraw_render.log",
        FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,
        NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE)return;
    DWORD written;
    WriteFile(file,value,(DWORD)strlen(value),&written,NULL);
    WriteFile(file,"\r\n",2,&written,NULL);
    CloseHandle(file);
}

static void init_log(void) {
    HANDLE file=CreateFileW(L"C:\\charoite_ownerdraw_render.log",GENERIC_WRITE,
        FILE_SHARE_READ,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);
    char info[160];
    snprintf(info,sizeof(info),
        "Charoite Core GDI owner-draw diagnostic v3 ACP=%u OEMCP=%u UI=%04x",
        GetACP(),GetOEMCP(),(unsigned)GetUserDefaultUILanguage());
    log_message(info);
    log_message("Native Win32 LBS_OWNERDRAWFIXED | LBS_HASSTRINGS control; not Delphi VCL.");
    log_message("Each row draws identical Japanese UTF-16/CP932; rows 5-10 test alternate font charsets.");
    log_message("Font mappings are logged before text rendering; no Wine files are changed.");
    log_message("Use FIRST 5 / LAST 6 on-screen buttons; Wine touch scrolling is NOT required.");
}

static void init_font(void) {
    const BYTE characterSets[3]={
        SHIFTJIS_CHARSET, DEFAULT_CHARSET, ANSI_CHARSET
    };
    for(int index=0;index<3;index++) {
        LOGFONTW spec={0};
        spec.lfHeight=-20;
        spec.lfCharSet=characterSets[index];
        lstrcpynW(spec.lfFaceName,L"IPAPGothic",LF_FACESIZE);
        japaneseFonts[index]=CreateFontIndirectW(&spec);
        if(!japaneseFonts[index]) {
            char warning[120];
            snprintf(warning,sizeof(warning),
                "ERROR: cannot create font for charset %u",(unsigned)characterSets[index]);
            log_message(warning);
        }
    }
}

static void log_font(HDC dc) {
    wchar_t face[LF_FACESIZE]={0};
    GetTextFaceW(dc,LF_FACESIZE,face);
    char name[140]={0};
    WideCharToMultiByte(CP_UTF8,0,face,-1,name,sizeof(name),NULL,NULL);
    const wchar_t sample[]=L"\x30A2\x30A4\x30B3\x30F3";
    WORD glyphs[4]={0xffff,0xffff,0xffff,0xffff};
    DWORD rc=GetGlyphIndicesW(dc,sample,4,glyphs,GGI_MARK_NONEXISTING_GLYPHS);
    int missing=0;
    for(int i=0;i<4;i++)if(glyphs[i]==0xffff)missing++;
    char line[300];
    snprintf(line,sizeof(line),
        "owner-draw selected face=%s charset=%d glyph_missing=%d glyph_error=%d",
        name,GetTextCharset(dc),missing,(int)(rc==GDI_ERROR));
    log_message(line);
}

static void draw_item(const DRAWITEMSTRUCT *item) {
    int pageCount=(pageFirst==0 ? PAGE_BREAK : METHODS-PAGE_BREAK);
    if(!item || item->itemID==(UINT)-1 || item->itemID>=(UINT)pageCount ||
       item->CtlType!=ODT_LISTBOX || item->hwndItem!=checklist)return;
    HDC dc=item->hDC;
    int state=SaveDC(dc);
    if(!state)return;
    int index=pageFirst+(int)item->itemID;
    int fontCase=0;
    if(index==5 || index==7 || index==8 || index==10) fontCase=1;
    else if(index==6 || index==9) fontCase=2;
    HGDIOBJ previous=NULL;
    if(japaneseFonts[fontCase]) previous=SelectObject(dc,japaneseFonts[fontCase]);
    if(previous==HGDI_ERROR)previous=NULL;
    wchar_t mappedFace[LF_FACESIZE]={0};
    GetTextFaceW(dc,LF_FACESIZE,mappedFace);
    char mappedUtf8[160]={0};
    WideCharToMultiByte(CP_UTF8,0,mappedFace,-1,
                        mappedUtf8,sizeof(mappedUtf8),NULL,NULL);
    int actualCharset=GetTextCharset(dc);

    BOOL selected=(item->itemState & ODS_SELECTED)!=0;
    HBRUSH bg=CreateSolidBrush(selected?RGB(29,69,122):RGB(248,247,252));
    if(bg) {
        FillRect(dc,&item->rcItem,bg);
        DeleteObject(bg);
    }
    SetBkMode(dc,TRANSPARENT);
    SetTextColor(dc,selected?RGB(255,255,255):RGB(24,27,45));
    RECT title=item->rcItem;
    title.left+=13;
    title.top+=3;
    title.bottom=title.top+24;
    DrawTextW(dc,methods[index],-1,&title,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX);
    RECT line=item->rcItem;
    line.left+=13;
    line.top+=27;
    line.right-=8;
    line.bottom=line.top+31;

    char ansi[256]={0};
    BOOL loss=FALSE;
    int cpSize=WideCharToMultiByte(932,WC_NO_BEST_FIT_CHARS,
                        jp,-1,ansi,sizeof(ansi),NULL,&loss);
    BOOL ok=FALSE;
    if(index==0 || index==7)
        ok=DrawTextW(dc,jp,-1,&line,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX)>0;
    if((index==1 || index==5 || index==6) && cpSize>0 && !loss)
        ok=DrawTextA(dc,ansi,-1,&line,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX)>0;
    if(index==2 || index==10)
        ok=ExtTextOutW(dc,line.left,line.top,ETO_CLIPPED,&line,jp,(UINT)wcslen(jp),NULL);
    if((index==3 || index==8 || index==9) && cpSize>0 && !loss)
        ok=ExtTextOutA(dc,line.left,line.top,ETO_CLIPPED,&line,ansi,(UINT)(cpSize-1),NULL);
    if(index==4)
        ok=TextOutW(dc,line.left,line.top,jp,(int)wcslen(jp));

    if(!seen[index]) {
        wchar_t stored[128]={0};
        LRESULT length=SendMessageW(checklist,LB_GETTEXT,(WPARAM)item->itemID,(LPARAM)stored);
        char report[340];
        snprintf(report,sizeof(report),
            "draw[%d] success=%d original_unicode_intact=%d requested_charset=%d actual_charset=%d mapped_face=%s cp932_bytes=%d substitutions=%d",
            index,ok!=FALSE,(int)(length>0 && wcscmp(stored,jp)==0),
            (int)(fontCase==0 ? SHIFTJIS_CHARSET :
                  (fontCase==1 ? DEFAULT_CHARSET : ANSI_CHARSET)),
            actualCharset,mappedUtf8,cpSize,loss!=FALSE);
        log_message(report);
        if(index==0)log_font(dc);
        seen[index]=TRUE;
    }
    RestoreDC(dc,state);
}

/*
 * This diagnostic owns its synthetic list data. Changing pages only updates
 * these known test strings, not a Delphi installer or any user's game files.
 * Repopulating on button click avoids touch scrolling and wheel emulation.
 */
static void show_page(int first) {
    if(!checklist)return;
    if(first!=0 && first!=PAGE_BREAK)return;
    pageFirst=first;
    SendMessageW(checklist,WM_SETREDRAW,FALSE,0);
    SendMessageW(checklist,LB_RESETCONTENT,0,0);
    int count=(first==0 ? PAGE_BREAK : METHODS);
    for(int i=first;i<count;i++)
        SendMessageW(checklist,LB_ADDSTRING,0,(LPARAM)jp);
    SendMessageW(checklist,WM_SETREDRAW,TRUE,0);
    InvalidateRect(checklist,NULL,TRUE);
    UpdateWindow(checklist);
    log_message(first==0 ? "page=first5 visible_indices=0..4" :
                           "page=last6 visible_indices=5..10");
}

static LRESULT CALLBACK window_proc(HWND hwnd,UINT message,WPARAM wp,LPARAM lp) {
    switch(message) {
        case WM_MEASUREITEM: {
            MEASUREITEMSTRUCT *measure=(MEASUREITEMSTRUCT*)lp;
            if(measure && measure->CtlID==CONTROL) {
                measure->itemHeight=64;
                return TRUE;
            }
            break;
        }
        case WM_DRAWITEM: {
            DRAWITEMSTRUCT *item=(DRAWITEMSTRUCT*)lp;
            if(item && item->CtlID==CONTROL) {
                draw_item(item);
                return TRUE;
            }
            break;
        }
        case WM_COMMAND: {
            if(HIWORD(wp)==BN_CLICKED && LOWORD(wp)==PAGE_FIRST) {
                show_page(0);
                return 0;
            }
            if(HIWORD(wp)==BN_CLICKED && LOWORD(wp)==PAGE_LAST) {
                show_page(PAGE_BREAK);
                return 0;
            }
            break;
        }
        case WM_DESTROY:
            for(int i=0;i<3;i++)if(japaneseFonts[i])DeleteObject(japaneseFonts[i]);
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd,message,wp,lp);
}

int WINAPI wWinMain(HINSTANCE app,HINSTANCE prev,PWSTR args,int show) {
    (void)prev;(void)args;
    init_log();
    init_font();
    WNDCLASSW wc={0};
    wc.hInstance=app;
    wc.lpfnWndProc=window_proc;
    wc.hCursor=LoadCursorW(NULL,IDC_ARROW);
    wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
    wc.lpszClassName=L"CharoiteOwnerDrawGdiTest";
    if(!RegisterClassW(&wc)) {
        log_message("ERROR: window class registration failed");
        return 2;
    }
    HWND window=CreateWindowExW(0,wc.lpszClassName,
        L"Charoite Core - Owner-Draw Text Diagnostics",
        WS_OVERLAPPEDWINDOW|WS_VISIBLE,
        CW_USEDEFAULT,CW_USEDEFAULT,840,650,
        NULL,NULL,app,NULL);
    if(!window) {
        log_message("ERROR: Win32 diagnostic window failed");
        return 3;
    }
    CreateWindowExW(0,L"STATIC",
        L"Owner-drawn Japanese text - all eleven rows should match",
        WS_CHILD|WS_VISIBLE,14,15,780,25,window,NULL,app,NULL);
    CreateWindowExW(0,L"STATIC",jp,WS_CHILD|WS_VISIBLE,
        14,49,780,25,window,NULL,app,NULL);
    /* Large, directly clickable Win32 buttons work on touch-only devices. */
    HWND firstButton=CreateWindowExW(0,L"BUTTON",L"FIRST 5 TESTS (1-5)",
        WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,
        14,82,375,35,window,(HMENU)(INT_PTR)PAGE_FIRST,app,NULL);
    HWND lastButton=CreateWindowExW(0,L"BUTTON",L"LAST 6 TESTS (6-11)",
        WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,
        410,82,384,35,window,(HMENU)(INT_PTR)PAGE_LAST,app,NULL);
    if(!firstButton || !lastButton) {
        log_message("ERROR: navigation button creation failed");
        DestroyWindow(window);
        return 5;
    }
    checklist=CreateWindowExW(WS_EX_CLIENTEDGE,L"LISTBOX",L"",
        WS_CHILD|WS_VISIBLE|LBS_OWNERDRAWFIXED|
        LBS_HASSTRINGS|LBS_NOTIFY|LBS_NOINTEGRALHEIGHT,
        14,124,780,400,window,(HMENU)(INT_PTR)CONTROL,app,NULL);
    if(!checklist) {
        log_message("ERROR: owner-drawn Win32 listbox creation failed");
        DestroyWindow(window);
        return 4;
    }
    show_page(0);
    ShowWindow(window,show);
    UpdateWindow(window);
    MSG event;
    while(GetMessageW(&event,NULL,0,0)>0) {
        TranslateMessage(&event);
        DispatchMessageW(&event);
    }
    return 0;
}
