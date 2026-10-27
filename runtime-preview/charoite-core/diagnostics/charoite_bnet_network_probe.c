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

typedef struct {
    int agents;
    int clients;
    int launchers;
    DWORD error;
} ProcessCounts;

static ProcessCounts get_process_counts(void) {
    ProcessCounts counts;
    ZeroMemory(&counts, sizeof(counts));
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        counts.error = GetLastError();
    } else {
        PROCESSENTRY32W proc;
        ZeroMemory(&proc, sizeof(proc));
        proc.dwSize = sizeof(proc);
        if (Process32FirstW(snapshot, &proc)) do {
            if (!_wcsicmp(proc.szExeFile, L"Agent.exe")) counts.agents++;
            else if (!_wcsicmp(proc.szExeFile, L"Battle.net.exe")) counts.clients++;
            else if (!_wcsicmp(proc.szExeFile, L"Battle.net Launcher.exe"))
                counts.launchers++;
        } while (Process32NextW(snapshot, &proc));
        CloseHandle(snapshot);
    }
    return counts;
}

static void process_status(FILE *report) {
    ProcessCounts counts = get_process_counts();
    fprintf(report,"guest_process_enumeration_error=%lu\n",
            (unsigned long)counts.error);
    fprintf(report,"guest_agent_process_count=%d\n", counts.agents);
    fprintf(report,"guest_battlenet_client_process_count=%d\n", counts.clients);
    fprintf(report,"guest_battlenet_launcher_process_count=%d\n", counts.launchers);
}

/*
 * This mode MUST run inside the same Wine session as the Battle.net launcher.
 * Independent Portal diagnostics start a separate Wine desktop, so their
 * zero-process snapshot cannot be used to infer the launcher's Agent status.
 *
 * Report fixed numeric samples only. Each file is Charoite-owned and small;
 * flush immediately so a crashed Wine session leaves actionable data.
 */
static void monitor_battlenet(FILE *report) {
    int seenAgent=0, seenClient=0, seenLauncher=0;
    int maxAgent=0, maxClient=0, maxLauncher=0, everEnumError=0;
    fprintf(report,"monitor_same_session=1\n");
    fprintf(report,"monitor_sample_interval_ms=1800\n");
    fprintf(report,"monitor_expected_samples=16\n");
    fflush(report);
    for (int i=0; i<16; i++) {
        ProcessCounts c=get_process_counts();
        if (c.agents > maxAgent) maxAgent = c.agents;
        if (c.clients > maxClient) maxClient = c.clients;
        if (c.launchers > maxLauncher) maxLauncher = c.launchers;
        if (c.agents) seenAgent++;
        if (c.clients) seenClient++;
        if (c.launchers) seenLauncher++;
        if (c.error) everEnumError++;
        fprintf(report,"monitor_sample_%02d_agent=%d\n",i,c.agents);
        fprintf(report,"monitor_sample_%02d_client=%d\n",i,c.clients);
        fprintf(report,"monitor_sample_%02d_launcher=%d\n",i,c.launchers);
        fprintf(report,"monitor_samples_completed=%d\n",i+1);
        fflush(report);
        if(i<15) Sleep(1800);
    }
    fprintf(report,"monitor_agent_present_samples=%d\n",seenAgent);
    fprintf(report,"monitor_client_present_samples=%d\n",seenClient);
    fprintf(report,"monitor_launcher_present_samples=%d\n",seenLauncher);
    fprintf(report,"monitor_max_agent=%d\n",maxAgent);
    fprintf(report,"monitor_max_client=%d\n",maxClient);
    fprintf(report,"monitor_max_launcher=%d\n",maxLauncher);
    fprintf(report,"monitor_process_enumeration_error_samples=%d\n",everEnumError);
    fprintf(report,"monitor_complete=1\n");
    fflush(report);
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
    const wchar_t *cmd=GetCommandLineW();
    int monitor = cmd && wcsstr(cmd,L"/monitor") != NULL;
    wcscpy(slash+1, monitor ?
            L"charoite_bnet_launch_monitor.txt" :
            L"charoite_bnet_network_report.txt");
    FILE *report=_wfopen(path,L"w");
    if (!report) return 4;
    if (monitor) {
        fprintf(report,"Charoite in-session Battle.net process monitor v2\n");
        monitor_battlenet(report);
        fclose(report);
        return 0;
    }
    fprintf(report,"Charoite Battle.net Wine guest diagnostic v2\n");
    fprintf(report,"phase_7_means_http_response_received=1\n");
    fprintf(report,"not_a_test_of_blizzard_login_or_authentication=1\n");
    process_status(report);
    test_endpoint(report,L"us.battle.net","battle_net");
    test_endpoint(report,L"downloader.battle.net","downloader");
    fclose(report);
    return 0;
}
