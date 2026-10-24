/*
 * Charoite Core Windows owner-draw GDI differential test, revision 1.
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
#define METHODS 5
static const wchar_t jp[] =
    L"\x30A2\x30A4\x30B3\x30F3\x3092\x8FFD\x52A0\x3059\x308B: "
    L"\x30C7\x30B9\x30AF\x30C8\x30C3\x30D7\x306B\x30A2\x30A4\x30B3\x30F3\x3092\x4F5C\x6210";
static const wchar_t* methods[METHODS]={
    L"DrawTextW (Unicode)", L"DrawTextA (ANSI CP932)",
    L"ExtTextOutW (Unicode)", L"ExtTextOutA (ANSI CP932)",
    L"TextOutW (Unicode)"
};
static HWND checklist=NULL;
static HFONT japanFont=NULL;
static BOOL seen[METHODS]={FALSE,FALSE,FALSE,FALSE,FALSE};

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
        "Charoite Core GDI owner-draw diagnostic v1 ACP=%u OEMCP=%u UI=%04x",
        GetACP(),GetOEMCP(),(unsigned)GetUserDefaultUILanguage());
    log_message(info);
    log_message("Native Win32 LBS_OWNERDRAWFIXED | LBS_HASSTRINGS control; not Delphi VCL.");
    log_message("Each row draws the SAME known Japanese text using the stated GDI API.");
}

static void init_font(void) {
    LOGFONTW spec={0};
    spec.lfHeight=-20;
    spec.lfCharSet=SHIFTJIS_CHARSET;
    lstrcpynW(spec.lfFaceName,L"IPAPGothic",LF_FACESIZE);
    japanFont=CreateFontIndirectW(&spec);
    if(!japanFont)log_message("ERROR: unable to construct Japanese GDI font");
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
    if(!item || item->itemID==(UINT)-1 || item->itemID>=METHODS ||
       item->CtlType!=ODT_LISTBOX || item->hwndItem!=checklist)return;
    HDC dc=item->hDC;
    int state=SaveDC(dc);
    if(!state)return;
    int index=(int)item->itemID;
    HGDIOBJ previous=NULL;
    if(japanFont) previous=SelectObject(dc,japanFont);
    if(previous==HGDI_ERROR)previous=NULL;

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
    line.top+=30;
    line.right-=8;
    line.bottom=line.top+36;

    char ansi[256]={0};
    BOOL loss=FALSE;
    int cpSize=WideCharToMultiByte(932,WC_NO_BEST_FIT_CHARS,
                        jp,-1,ansi,sizeof(ansi),NULL,&loss);
    BOOL ok=FALSE;
    if(index==0)
        ok=DrawTextW(dc,jp,-1,&line,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX)>0;
    if(index==1 && cpSize>0 && !loss)
        ok=DrawTextA(dc,ansi,-1,&line,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX)>0;
    if(index==2)
        ok=ExtTextOutW(dc,line.left,line.top,ETO_CLIPPED,&line,jp,(UINT)wcslen(jp),NULL);
    if(index==3 && cpSize>0 && !loss)
        ok=ExtTextOutA(dc,line.left,line.top,ETO_CLIPPED,&line,ansi,(UINT)(cpSize-1),NULL);
    if(index==4)
        ok=TextOutW(dc,line.left,line.top,jp,(int)wcslen(jp));

    if(!seen[index]) {
        wchar_t stored[128]={0};
        LRESULT length=SendMessageW(checklist,LB_GETTEXT,(WPARAM)index,(LPARAM)stored);
        char report[210];
        snprintf(report,sizeof(report),
            "draw[%d] success=%d original_unicode_intact=%d cp932_bytes=%d substitutions=%d",
            index,ok!=FALSE,(int)(length>0 && wcscmp(stored,jp)==0),
            cpSize,loss!=FALSE);
        log_message(report);
        if(index==0)log_font(dc);
        seen[index]=TRUE;
    }
    RestoreDC(dc,state);
}

static LRESULT CALLBACK window_proc(HWND hwnd,UINT message,WPARAM wp,LPARAM lp) {
    switch(message) {
        case WM_MEASUREITEM: {
            MEASUREITEMSTRUCT *measure=(MEASUREITEMSTRUCT*)lp;
            if(measure && measure->CtlID==CONTROL) {
                measure->itemHeight=80;
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
        case WM_DESTROY:
            if(japanFont)DeleteObject(japanFont);
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
        L"Owner-drawn Japanese text - all five rows should match",
        WS_CHILD|WS_VISIBLE,14,15,780,25,window,NULL,app,NULL);
    CreateWindowExW(0,L"STATIC",jp,WS_CHILD|WS_VISIBLE,
        14,49,780,25,window,NULL,app,NULL);
    checklist=CreateWindowExW(WS_EX_CLIENTEDGE,L"LISTBOX",L"",
        WS_CHILD|WS_VISIBLE|WS_VSCROLL|LBS_OWNERDRAWFIXED|
        LBS_HASSTRINGS|LBS_NOTIFY|LBS_NOINTEGRALHEIGHT,
        14,90,780,440,window,(HMENU)(INT_PTR)CONTROL,app,NULL);
    if(!checklist) {
        log_message("ERROR: owner-drawn Win32 listbox creation failed");
        DestroyWindow(window);
        return 4;
    }
    for(int i=0;i<METHODS;i++)SendMessageW(checklist,LB_ADDSTRING,0,(LPARAM)jp);
    RECT bounds;
    GetClientRect(checklist,&bounds);
    InvalidateRect(checklist,&bounds,TRUE);
    ShowWindow(window,show);
    UpdateWindow(window);
    MSG event;
    while(GetMessageW(&event,NULL,0,0)>0) {
        TranslateMessage(&event);
        DispatchMessageW(&event);
    }
    return 0;
}
