/*
 * Charoite Core / Battle.net: read-only Wine guest network+process probe.
 * Never uses Blizzard credentials or session cookies and does not read
 * Blizzard files. The output contains only boolean/status/error codes.
 *
 * Standalone 32-bit Win32 executable, bundled by Charoite Portal and launched
 * on the user's request in the selected Battle.net Wine container.
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <winhttp.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <wchar.h>

static void process_status(FILE *report) {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    int agents=0, clients=0, launchers=0;
    DWORD error=0;
    if (snapshot == INVALID_HANDLE_VALUE) {
        error = GetLastError();
    } else {
        PROCESSENTRY32W proc;
        ZeroMemory(&proc, sizeof(proc));
        proc.dwSize = sizeof(proc);
        if (Process32FirstW(snapshot, &proc)) do {
            if (!_wcsicmp(proc.szExeFile, L"Agent.exe")) agents++;
            else if (!_wcsicmp(proc.szExeFile, L"Battle.net.exe")) clients++;
            else if (!_wcsicmp(proc.szExeFile, L"Battle.net Launcher.exe"))
                launchers++;
        } while (Process32NextW(snapshot, &proc));
        CloseHandle(snapshot);
    }
    fprintf(report,"guest_process_enumeration_error=%lu\n", (unsigned long)error);
    fprintf(report,"guest_agent_process_count=%d\n", agents);
    fprintf(report,"guest_battlenet_client_process_count=%d\n", clients);
    fprintf(report,"guest_battlenet_launcher_process_count=%d\n", launchers);
}

static void test_endpoint(FILE *report, const wchar_t *host, const char *label) {
    WSADATA ws;
    int startup = WSAStartup(MAKEWORD(2,2), &ws);
    int dns=0;
    if (!startup) {
        struct addrinfoW hints;
        struct addrinfoW *result=NULL;
        ZeroMemory(&hints,sizeof(hints));
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_family = AF_UNSPEC;
        dns = GetAddrInfoW(host,L"443",&hints,&result);
        if (result) FreeAddrInfoW(result);
        WSACleanup();
    } else dns=startup;
    fprintf(report,"%s_dns_status=%d\n", label,dns);

    DWORD phase=0, error=0, code=0;
    // A response of ANY HTTP status demonstrates transport/handshake worked.
    // 403/404 may be normal for HEAD / on a Blizzard CDN; not application errors.
    HINTERNET session=WinHttpOpen(L"CharoitePortal Network Probe/1.0",
            WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
            WINHTTP_NO_PROXY_NAME,WINHTTP_NO_PROXY_BYPASS,0);
    if (!session) {phase=1; error=GetLastError(); goto done;}
    WinHttpSetTimeouts(session,2500,2500,3000,3000);
    HINTERNET connection=WinHttpConnect(session,host,INTERNET_DEFAULT_HTTPS_PORT,0);
    if (!connection) {phase=2; error=GetLastError(); goto close_session;}
    HINTERNET request=WinHttpOpenRequest(connection,L"HEAD",L"/",NULL,
            WINHTTP_NO_REFERER,WINHTTP_DEFAULT_ACCEPT_TYPES,WINHTTP_FLAG_SECURE);
    if (!request) {phase=3; error=GetLastError(); goto close_connection;}
    if (!WinHttpSendRequest(request,WINHTTP_NO_ADDITIONAL_HEADERS,0,
            WINHTTP_NO_REQUEST_DATA,0,0,0)) {
        phase=4; error=GetLastError(); goto close_request;
    }
    if (!WinHttpReceiveResponse(request,NULL)) {
        phase=5; error=GetLastError(); goto close_request;
    }
    DWORD size=sizeof(code);
    if (!WinHttpQueryHeaders(request,WINHTTP_QUERY_STATUS_CODE |
            WINHTTP_QUERY_FLAG_NUMBER,WINHTTP_HEADER_NAME_BY_INDEX,
            &code,&size,WINHTTP_NO_HEADER_INDEX)) {
        phase=6; error=GetLastError();
    } else phase=7;
close_request:
    WinHttpCloseHandle(request);
close_connection:
    WinHttpCloseHandle(connection);
close_session:
    WinHttpCloseHandle(session);
done:
    fprintf(report,"%s_https_phase=%lu\n",label,(unsigned long)phase);
    fprintf(report,"%s_https_win32_error=%lu\n",label,(unsigned long)error);
    fprintf(report,"%s_http_status=%lu\n",label,(unsigned long)code);
}

int WINAPI WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR args,int show) {
    (void)instance; (void)previous; (void)args; (void)show;
    wchar_t path[MAX_PATH];
    DWORD length=GetModuleFileNameW(NULL,path,MAX_PATH);
    if (!length || length>=MAX_PATH) return 2;
    wchar_t *slash=wcsrchr(path,L'\\');
    if (!slash) return 3;
    wcscpy(slash+1,L"charoite_bnet_network_report.txt");
    FILE *report=_wfopen(path,L"w");
    if (!report) return 4;
    fprintf(report,"Charoite Battle.net Wine guest diagnostic v1\n");
    fprintf(report,"phase_7_means_http_response_received=1\n");
    fprintf(report,"not_a_test_of_blizzard_login_or_authentication=1\n");
    process_status(report);
    test_endpoint(report,L"us.battle.net","battle_net");
    test_endpoint(report,L"downloader.battle.net","downloader");
    fclose(report);
    return 0;
}
