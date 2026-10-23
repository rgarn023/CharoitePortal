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
    // Post-draw hook corrects only reversible task-label mojibake in memory.
    // The previous font hook remains active as a safe fallback.
#ifdef _WIN64
    const char *drawExport="TouhouDrawHook";
#else
    const char *drawExport="_TouhouDrawHook@12";
#endif
    HOOKPROC drawCallback=(HOOKPROC)GetProcAddress(module,drawExport);
    if(!drawCallback) drawCallback=(HOOKPROC)GetProcAddress(module,"TouhouDrawHook");
    HHOOK drawHook=drawCallback
            ? SetWindowsHookExW(WH_CALLWNDPROCRET,drawCallback,module,threadId) : NULL;
    if(drawHook) report("helper-v3: task-label post-draw hook installed");
    else report("helper-v3: post-draw hook unavailable; standard Japanese font hook remains active");
    report("helper-v3: thread-local font hook installed; keeping later wizard pages active");
    // An Inno Setup user can spend much longer than 18 seconds on the path,
    // shortcuts and optional-task pages. Continue checking the same installer
    // GUI thread without rewriting its strings or touching other processes.
    // Stop automatically when the target Windows thread exits or after 5 min.
    HANDLE targetThread=OpenThread(SYNCHRONIZE | THREAD_QUERY_INFORMATION,
                                  FALSE,threadId);
    for(int count=0;count<600;count++) {
        if(targetThread && WaitForSingleObject(targetThread,0)==WAIT_OBJECT_0) {
            report("helper-v2: installer GUI thread exited");
            break;
        }
        if(!PostThreadMessageW(threadId,WM_NULL,0,0)) {
            report("helper-v2: installer thread no longer accepts messages");
            break;
        }
        Sleep(500);
    }
    if(targetThread) CloseHandle(targetThread);
    if(drawHook) UnhookWindowsHookEx(drawHook);
    UnhookWindowsHookEx(hook);
    report("helper-v3: scoped hooks uninstalled after installer session");
    FreeLibrary(module);
    if(desktop) CloseDesktop(desktop);
    return 0;
}
