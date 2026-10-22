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
    report("helper-v1: thread-specific hook installed; waking installer thread");
    for(int count=0;count<18;count++) {
        PostThreadMessageW(threadId,WM_NULL,0,0);
        Sleep(1000);
    }
    UnhookWindowsHookEx(hook);
    report("helper-v1: hook uninstalled (font stays assigned to live installer edit)");
    FreeLibrary(module);
    if(desktop) CloseDesktop(desktop);
    return 0;
}
