/*
 * Win32 thread-specific Japanese font compatibility shim loader.
 * Never patches executable code, registry, files or the installer path.
 * Targets only a caller-provided thread ID from a discovered TPDP TWizardForm.
 * 32 and 64 bit builds with matching DLLs are compiled by GitHub Actions.
 */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <stdlib.h>

static void report(const char *message) {
    HANDLE f=CreateFileW(L"C:\\touhou_font_helper.log",FILE_APPEND_DATA,
          FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_ALWAYS,
          FILE_ATTRIBUTE_NORMAL,NULL);
    if(f==INVALID_HANDLE_VALUE) return;
    DWORD wrote;
    WriteFile(f,message,(DWORD)lstrlenA(message),&wrote,NULL);
    WriteFile(f,"\r\n",2,&wrote,NULL);
    CloseHandle(f);
}
int WINAPI wWinMain(HINSTANCE current,HINSTANCE previous,PWSTR line,int show) {
    (void)current; (void)previous; (void)show;
    DWORD threadId=wcstoul(line,NULL,10);
    if(threadId==0) { report("helper-v1: invalid target thread"); return 2; }

    HDESK desktop=OpenDesktopW(L"nogui",0,FALSE,
                       DESKTOP_READOBJECTS|DESKTOP_HOOKCONTROL|DESKTOP_WRITEOBJECTS);
    if(desktop) {
        if(!SetThreadDesktop(desktop)) {
            char msg[120];
            snprintf(msg,sizeof(msg),"helper-v1: cannot select nogui desktop (error=%lu)",
                    (unsigned long)GetLastError());
            report(msg);
        } else report("helper-v1: selected Wine nogui desktop");
    } else {
        char msg[120];
        snprintf(msg,sizeof(msg),"helper-v1: OpenDesktop failed (error=%lu)",
                 (unsigned long)GetLastError());
        report(msg);
    }
#ifdef _WIN64
    const wchar_t *dllPath=L"C:\\touhou_font_hook64.dll";
    const char *exportName="TouhouFontHook";
#else
    const wchar_t *dllPath=L"C:\\touhou_font_hook32.dll";
    const char *exportName="_TouhouFontHook@12";
#endif
    HMODULE module=LoadLibraryW(dllPath);
    if(!module) { report("helper-v1: unable to load matching hook DLL"); return 3; }
    HOOKPROC callback=(HOOKPROC)GetProcAddress(module,exportName);
    if(!callback) {
        callback=(HOOKPROC)GetProcAddress(module,"TouhouFontHook@12");
    }
    if(!callback) {
        callback=(HOOKPROC)GetProcAddress(module,"TouhouFontHook");
    }
    if(!callback) {
        report("helper-v1: hook DLL missing expected export");
        FreeLibrary(module);
        return 4;
    }
    HHOOK hook=SetWindowsHookExW(WH_GETMESSAGE,callback,module,threadId);
    if(!hook) {
        char msg[160];
        snprintf(msg,sizeof(msg),
             "helper-v1: thread-specific hook could not attach (error=%lu)",
             (unsigned long)GetLastError());
        report(msg);
        FreeLibrary(module);
        return 5;
    }
    /*
     * Verified v4 DLL PE exports: 32-bit LLVM-MinGW exports
     * "TouhouDrawHook@12", not "_TouhouDrawHook@12"; 64-bit exports
     * "TouhouDrawHook". The previous loader did not try the actual
     * 32-bit name, so the paint hook could never attach on this installer.
     */
#ifdef _WIN64
    const char *drawExport="TouhouDrawHook";
#else
    const char *drawExport="TouhouDrawHook@12";
#endif
    HOOKPROC drawCallback=(HOOKPROC)GetProcAddress(module,drawExport);
    if(!drawCallback) {
        DWORD error=GetLastError();
        char msg[220];
        snprintf(msg,sizeof(msg),
            "helper-v8: draw export not found name=%s error=%lu",
            drawExport,(unsigned long)error);
        report(msg);
        // Compatibility aliases for other MinGW linkers.
        drawCallback=(HOOKPROC)GetProcAddress(module,"_TouhouDrawHook@12");
        if(!drawCallback)
            drawCallback=(HOOKPROC)GetProcAddress(module,"TouhouDrawHook");
    }

    HHOOK drawHook=NULL;
    if(drawCallback) {
        drawHook=SetWindowsHookExW(WH_CALLWNDPROCRET,drawCallback,module,threadId);
        if(!drawHook) {
            char msg[160];
            snprintf(msg,sizeof(msg),
                "helper-v8: post-draw hook attach failed win32_error=%lu",
                (unsigned long)GetLastError());
            report(msg);
        }
    }
    /*
     * Observe the same TWizardForm WM_DRAWITEM boundary BEFORE its WndProc.
     * For validated Japanese task captions, it temporarily selects a Shift-JIS
     * font in the GDI DC and restores it via the paired post-draw hook.
     * Retain the separate Unicode repaint fallback.
     */
#ifdef _WIN64
    const char *auditExport="TouhouAuditHook";
#else
    const char *auditExport="TouhouAuditHook@12";
#endif
    HOOKPROC auditCallback=(HOOKPROC)GetProcAddress(module,auditExport);
    HHOOK auditHook=NULL;
    if(drawHook && auditCallback) {
        auditHook=SetWindowsHookExW(WH_CALLWNDPROC,auditCallback,module,threadId);
        if(!auditHook) {
            char errorLine[160];
            snprintf(errorLine,sizeof(errorLine),
                "helper-v8: pre-draw audit hook attach failed win32_error=%lu",
                (unsigned long)GetLastError());
            report(errorLine);
        } else report("helper-v8: pre-draw installer charset audit attached (read-only)");
    } else report("helper-v8: pre-draw font correction unavailable without both pre- and post-draw hooks");
    if(drawHook) report("helper-v8: Unicode checklist post-draw hook installed");
    else report("helper-v8: post-draw hook unavailable; Unicode checklist remains unmodified");
    report("helper-v8: thread-local font hook installed; keeping later wizard pages active");
    // An Inno Setup user can spend much longer than 18 seconds on the path,
    // shortcuts and optional-task pages. Continue checking the same installer
    // GUI thread without rewriting its strings or touching other processes.
    // Stop automatically when the target Windows thread exits or after 5 min.
    HANDLE targetThread=OpenThread(SYNCHRONIZE | THREAD_QUERY_INFORMATION,
                                  FALSE,threadId);
    for(int count=0;count<1500;count++) {
        if(targetThread && WaitForSingleObject(targetThread,0)==WAIT_OBJECT_0) {
            report("helper-v8: installer GUI thread exited");
            break;
        }
        if(!PostThreadMessageW(threadId,WM_NULL,0,0)) {
            report("helper-v8: installer thread no longer accepts messages");
            break;
        }
        Sleep(200);
    }
    if(targetThread) CloseHandle(targetThread);
    if(auditHook) UnhookWindowsHookEx(auditHook);
    if(drawHook) UnhookWindowsHookEx(drawHook);
    UnhookWindowsHookEx(hook);
    report("helper-v8: scoped hooks uninstalled after installer session");
    FreeLibrary(module);
    if(desktop) CloseDesktop(desktop);
    return 0;
}
