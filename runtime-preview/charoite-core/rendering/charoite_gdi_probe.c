/*
 * Charoite Core Windows GDI diagnostic, revision 1.
 *
 * Read-only, opt-in test of Unicode/ANSI text drawing, font mapping and glyph
 * coverage under the CURRENT Wine installation. It never injects hooks,
 * rewrites games, updates registry data or changes the Wine prefix.
 * LGPL Wine remains completely unmodified.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <string.h>

#define LOGFILE L"C:\\charoite_gdi_render.log"
#define FONT_COUNT 4
#define LINE_HEIGHT 108

static const wchar_t jp[] =
    L"\x30A2\x30A4\x30B3\x30F3\x3092\x8FFD\x52A0\x3059\x308B: "
    L"\x30C7\x30B9\x30AF\x30C8\x30C3\x30D7\x306B\x30A2\x30A4\x30B3\x30F3\x3092\x4F5C\x6210";
static const wchar_t *faces[FONT_COUNT] = {
    L"MS UI Gothic", L"IPAPGothic", L"Noto Sans CJK JP", L"Tahoma"
};
static BOOL reported=FALSE;

static void log_message(const char *message) {
    HANDLE f=CreateFileW(LOGFILE,FILE_APPEND_DATA,
                        FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_ALWAYS,
                        FILE_ATTRIBUTE_NORMAL,NULL);
    if(f==INVALID_HANDLE_VALUE) return;
    DWORD written=0;
    WriteFile(f,message,(DWORD)strlen(message),&written,NULL);
    WriteFile(f,"\r\n",2,&written,NULL);
    CloseHandle(f);
}

static void log_fonts(HDC dc, int slot, HFONT font) {
    if(!font) { log_message("font creation failed"); return; }
    HGDIOBJ previous=SelectObject(dc,font);
    if(previous==HGDI_ERROR || !previous) {
        log_message("font selection failed");
        return;
    }
    wchar_t face[LF_FACESIZE]={0};
    GetTextFaceW(dc,LF_FACESIZE,face);
    char mapped[160]={0};
    WideCharToMultiByte(CP_UTF8,0,face,-1,mapped,sizeof(mapped),NULL,NULL);
    WORD glyphs[32]={0};
    const wchar_t sample[]=L"\x65E5\x672C\x8A9E\x30C6\x30B9\x30C8";
    DWORD result=GetGlyphIndicesW(dc,sample,6,glyphs,GGI_MARK_NONEXISTING_GLYPHS);
    int missing=0;
    for(int i=0;i<6;i++)if(glyphs[i]==0xffff)missing++;
    char line[400];
    snprintf(line,sizeof(line),
      "font[%d] mapped=%s glyphs_missing=%d glyph_query_error=%d",
      slot,mapped,missing,(int)(result==GDI_ERROR));
    log_message(line);
    SelectObject(dc,previous);
}

static void log_environment(void) {
    HANDLE log=CreateFileW(LOGFILE,GENERIC_WRITE,FILE_SHARE_READ,
            NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
    if(log!=INVALID_HANDLE_VALUE)CloseHandle(log);
    char header[220];
    snprintf(header,sizeof(header),
      "Charoite Core GDI read-only diagnostic v1 ACP=%u OEMCP=%u user_language=%04x",
      GetACP(),GetOEMCP(),(unsigned)GetUserDefaultUILanguage());
    log_message(header);
    char units[320]="known_unicode_utf16=";
    size_t pos=strlen(units);
    for(int i=0;jp[i] && i<28 && pos+7<sizeof(units);i++)
        pos+=(size_t)snprintf(units+pos,sizeof(units)-pos,"%04x ",(unsigned)jp[i]);
    log_message(units);
}

static HFONT make_font(const wchar_t *name) {
    LOGFONTW description;
    ZeroMemory(&description,sizeof(description));
    description.lfHeight=-19;
    description.lfWeight=FW_NORMAL;
    description.lfCharSet=SHIFTJIS_CHARSET;
    description.lfQuality=DEFAULT_QUALITY;
    lstrcpynW(description.lfFaceName,name,LF_FACESIZE);
    return CreateFontIndirectW(&description);
}

static void write_label(HDC dc,const wchar_t *label,int y) {
    RECT rect={15,y,745,y+26};
    DrawTextW(dc,label,-1,&rect,DT_SINGLELINE|DT_NOPREFIX|DT_END_ELLIPSIS);
}

static void draw_all(HWND hwnd,HDC dc) {
    RECT canvas;
    GetClientRect(hwnd,&canvas);
    HBRUSH background=CreateSolidBrush(RGB(247,247,252));
    FillRect(dc,&canvas,background);
    DeleteObject(background);
    SetBkMode(dc,TRANSPARENT);
    SetTextColor(dc,RGB(31,26,53));

    HFONT ui=(HFONT)GetStockObject(DEFAULT_GUI_FONT);
    HGDIOBJ original=SelectObject(dc,ui);
    write_label(dc,L"CHAROITE CORE - Windows GDI Japanese Text Test",8);
    write_label(dc,L"Compare Unicode W and codepage ANSI A samples. Both should be legible.",35);

    char cp932[256]={0};
    BOOL defaulted=FALSE;
    int cpLength=WideCharToMultiByte(932,WC_NO_BEST_FIT_CHARS,
                            jp,-1,cp932,sizeof(cp932),NULL,&defaulted);
    if(!reported) {
        char report[200];
        snprintf(report,sizeof(report),
          "cp932_conversion bytes=%d substitutions=%d (not a Wine rendering result)",
          cpLength,defaulted!=FALSE);
        log_message(report);
    }
    for(int i=0;i<FONT_COUNT;i++) {
        int y=74+i*LINE_HEIGHT;
        HFONT font=make_font(faces[i]);
        if(!reported) log_fonts(dc,i,font);
        wchar_t caption[160]={0};
        swprintf(caption,160,L"Font %d: %ls",i+1,faces[i]);
        SelectObject(dc,ui);
        write_label(dc,caption,y);
        if(font) SelectObject(dc,font);
        RECT unicodeRect={18,y+26,740,y+52};
        DrawTextW(dc,jp,-1,&unicodeRect,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX|DT_END_ELLIPSIS);
        SelectObject(dc,ui);
        RECT ansiTag={15,y+58,145,y+83};
        DrawTextW(dc,L"CP932 ANSI A:",-1,&ansiTag,DT_SINGLELINE|DT_NOPREFIX);
        if(font) SelectObject(dc,font);
        RECT ansiRect={160,y+58,745,y+84};
        if(cpLength>0 && !defaulted)
            DrawTextA(dc,cp932,-1,&ansiRect,DT_LEFT|DT_SINGLELINE|DT_NOPREFIX|DT_END_ELLIPSIS);
        if(font) {
            SelectObject(dc,ui);
            DeleteObject(font);
        }
    }
    SelectObject(dc,original);
    if(!reported) {
        log_message("Rendering calls completed; visual inspection of Unicode W vs ANSI A is required.");
        reported=TRUE;
    }
}

static LRESULT CALLBACK test_window(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp) {
    (void)wp;
    switch(msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC dc=BeginPaint(hwnd,&ps);
            draw_all(hwnd,dc);
            EndPaint(hwnd,&ps);
            return 0;
        }
        case WM_SIZE:
            InvalidateRect(hwnd,NULL,FALSE);
            return 0;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd,msg,wp,lp);
}

int WINAPI wWinMain(HINSTANCE app,HINSTANCE previous,PWSTR command,int mode) {
    (void)previous;(void)command;
    log_environment();
    WNDCLASSW type;
    ZeroMemory(&type,sizeof(type));
    type.lpfnWndProc=test_window;
    type.hInstance=app;
    type.lpszClassName=L"CharoiteCoreGdiProbe";
    type.hCursor=LoadCursorW(NULL,IDC_ARROW);
    type.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
    if(!RegisterClassW(&type)) {
        log_message("Could not register test window");
        return 2;
    }
    HWND window=CreateWindowW(type.lpszClassName,
           L"Charoite Core - Japanese Text Diagnostics",
           WS_OVERLAPPEDWINDOW|WS_VISIBLE,
           CW_USEDEFAULT,CW_USEDEFAULT,780,610,
           NULL,NULL,app,NULL);
    if(!window) {
        log_message("Could not create test window");
        return 3;
    }
    ShowWindow(window,mode);
    UpdateWindow(window);
    MSG message;
    while(GetMessageW(&message,NULL,0,0)>0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    return 0;
}
