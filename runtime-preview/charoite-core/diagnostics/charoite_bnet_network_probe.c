/*
 * Charoite Core / Battle.net: read-only Wine guest network+process probe.
 * Never uses Blizzard credentials or session cookies and does not read
 * Blizzard files. Ordinary monitoring is read-only; only the separate
 * confirmed /try-rpcss-start mode temporarily modifies RpcSs startup type.
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
#include <winsvc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <io.h>

typedef struct {
    int agents;
    int clients;
    int launchers;
    int rpcss;
    int services;
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
            else if (!_wcsicmp(proc.szExeFile, L"rpcss.exe")) counts.rpcss++;
            else if (!_wcsicmp(proc.szExeFile, L"services.exe")) counts.services++;
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


/* Query the Wine service manager without starting, stopping, or changing a
 * service. The process name alone cannot establish whether RpcSs is running.
 * All results are fixed numeric Win32 status/error codes, not account data.
 */
typedef struct {
    DWORD scm_error;
    DWORD open_error;
    DWORD query_error;
    DWORD state;
    DWORD config_error;
    DWORD start_type;
} RpcServiceStatus;

static int query_rpc_config(SC_HANDLE service, DWORD *startType, DWORD *error) {
    DWORD needed=0;
    QueryServiceConfigW(service,NULL,0,&needed);
    if (!needed || needed>8192) {
        *error=GetLastError();
        if (!*error) *error=ERROR_INSUFFICIENT_BUFFER;
        return 0;
    }
    QUERY_SERVICE_CONFIGW *config=(QUERY_SERVICE_CONFIGW*)malloc(needed);
    if (!config) { *error=ERROR_NOT_ENOUGH_MEMORY; return 0; }
    int ok=QueryServiceConfigW(service,config,needed,&needed);
    if (ok) *startType=config->dwStartType;
    else *error=GetLastError();
    free(config);
    return ok;
}

static RpcServiceStatus inspect_rpc_service(void) {
    RpcServiceStatus result;
    ZeroMemory(&result, sizeof(result));
    SC_HANDLE scm = OpenSCManagerW(NULL, NULL, SC_MANAGER_CONNECT);
    if (!scm) {
        result.scm_error = GetLastError();
        return result;
    }
    SC_HANDLE service = OpenServiceW(scm, L"RpcSs",
            SERVICE_QUERY_STATUS | SERVICE_QUERY_CONFIG);
    if (!service) {
        result.open_error = GetLastError();
        CloseServiceHandle(scm);
        return result;
    }
    SERVICE_STATUS_PROCESS status;
    DWORD required = 0;
    ZeroMemory(&status, sizeof(status));
    if (!QueryServiceStatusEx(service, SC_STATUS_PROCESS_INFO,
            (LPBYTE)&status, sizeof(status), &required))
        result.query_error = GetLastError();
    else result.state = status.dwCurrentState;
    query_rpc_config(service,&result.start_type,&result.config_error);
    CloseServiceHandle(service);
    CloseServiceHandle(scm);
    return result;
}


/*
 * Opt-in, temporary Battle.net RpcSs startup experiment.
 * Microsoft ERROR_SERVICE_DISABLED (1058) means StartService alone cannot
 * start the service. We change SERVICE_DISABLED -> SERVICE_DEMAND_START only
 * with explicit Portal confirmation, then restore SERVICE_DISABLED after the
 * bounded start attempt, including after a failure.
 *
 * A small, fixed-format Charoite-only recovery marker is fsynced BEFORE
 * changing the Wine SCM setting. If interrupted, the next explicit repair
 * attempt restores the original disabled configuration before any retry.
 * The normal /monitor path never changes SCM values.
 */
#define RPC_MARKER_CONTENT "CHAROITE_RPCSS_START_DISABLED=4\n"

static int rpc_recovery_path(wchar_t *path, DWORD cap) {
    DWORD length=GetModuleFileNameW(NULL,path,cap);
    if (!length || length>=cap) return 0;
    wchar_t *slash=wcsrchr(path,L'\\');
    if (!slash) return 0;
    const wchar_t *name=L"charoite_rpcss_recovery.txt";
    if ((size_t)(slash-path)+1+wcslen(name)>=cap) return 0;
    wcscpy(slash+1,name);
    return 1;
}

static int rpc_write_marker(const wchar_t *path) {
    FILE *file=_wfopen(path,L"wb");
    if (!file) return 0;
    const char *marker=RPC_MARKER_CONTENT;
    size_t size=strlen(marker);
    int ok=fwrite(marker,1,size,file)==size;
    if (ok) ok=fflush(file)==0;
    if (ok) ok=_commit(_fileno(file))==0;
    if (fclose(file)!=0) ok=0;
    return ok;
}

/* Returns 1 if no pending recovery or the saved disabled state was
 * restored. Any other marker contents or service state require investigation:
 * never overwrite a third party's SCM change. */
static int rpc_recover_pending(SC_HANDLE service, const wchar_t *path,
                               DWORD *error, DWORD *wasPending) {
    FILE *file=_wfopen(path,L"rb");
    if (!file) {
        if (GetLastError()!=ERROR_FILE_NOT_FOUND &&
                GetFileAttributesW(path)!=INVALID_FILE_ATTRIBUTES) {
            *error=ERROR_ACCESS_DENIED;
            return 0;
        }
        return 1;
    }
    *wasPending=1;
    char buffer[64];
    size_t size=fread(buffer,1,sizeof(buffer),file);
    int extra=fgetc(file);
    fclose(file);
    const char *expected=RPC_MARKER_CONTENT;
    if (size!=strlen(expected) || memcmp(buffer,expected,size)!=0 || extra!=EOF) {
        *error=ERROR_INVALID_DATA;
        return 0;
    }
    DWORD startType=0;
    if (!query_rpc_config(service,&startType,error)) return 0;
    if (startType==SERVICE_DEMAND_START) {
        if (!ChangeServiceConfigW(service,SERVICE_NO_CHANGE,
                SERVICE_DISABLED,SERVICE_NO_CHANGE,NULL,NULL,NULL,
                NULL,NULL,NULL,NULL)) {
            *error=GetLastError();
            return 0;
        }
        if (!query_rpc_config(service,&startType,error)) return 0;
    }
    if (startType!=SERVICE_DISABLED) {
        *error=ERROR_INVALID_DATA;
        return 0;
    }
    if (_wremove(path)!=0) {
        *error=ERROR_ACCESS_DENIED;
        return 0;
    }
    return 1;
}

static int try_start_rpc_service(FILE *report) {
    RpcServiceStatus before=inspect_rpc_service();
    DWORD startError=0, openError=0, queryError=0, afterState=before.state;
    DWORD attempt=0, alreadyRunning=0, enableAttempt=0, enableError=0;
    DWORD restoreAttempt=0, restoreError=0, restoreConfirmed=0;
    DWORD pendingRecovery=0, recoveryError=0, recoveryPathReady=0;
    DWORD typeAfter=before.start_type, recovered=0;
    wchar_t path[MAX_PATH];
    SC_HANDLE scm=NULL,service=NULL;

    if (before.state==SERVICE_RUNNING) alreadyRunning=1;
    recoveryPathReady=rpc_recovery_path(path,MAX_PATH);

    if (!before.scm_error && !before.open_error && !before.query_error &&
            !before.config_error && before.state==SERVICE_STOPPED) {
        scm=OpenSCManagerW(NULL,NULL,SC_MANAGER_CONNECT);
        if (!scm) openError=GetLastError();
        else {
            service=OpenServiceW(scm,L"RpcSs",SERVICE_START |
                    SERVICE_QUERY_STATUS | SERVICE_QUERY_CONFIG |
                    SERVICE_CHANGE_CONFIG);
            if (!service) openError=GetLastError();
            else if (!recoveryPathReady) recoveryError=ERROR_INVALID_NAME;
            else {
                /* Interrupted previous attempt: finish rollback BEFORE
                 * permitting another potentially mutating service start. */
                recovered=rpc_recover_pending(service,path,
                        &recoveryError,&pendingRecovery);
                if (recovered && query_rpc_config(service,&typeAfter,&queryError)) {
                    if (typeAfter==SERVICE_DISABLED) {
                        if (!rpc_write_marker(path)) {
                            recoveryError=ERROR_WRITE_FAULT;
                        } else {
                            enableAttempt=1;
                            if (!ChangeServiceConfigW(service,SERVICE_NO_CHANGE,
                                    SERVICE_DEMAND_START,SERVICE_NO_CHANGE,
                                    NULL,NULL,NULL,NULL,NULL,NULL,NULL)) {
                                enableError=GetLastError();
                            } else {
                                DWORD typeEnabled=0;
                                if (!query_rpc_config(service,&typeEnabled,&queryError) ||
                                        typeEnabled!=SERVICE_DEMAND_START) {
                                    if (!queryError) queryError=ERROR_INVALID_DATA;
                                } else {
                                    attempt=1;
                                    if (!StartServiceW(service,0,NULL)) {
                                        startError=GetLastError();
                                        if (startError==ERROR_SERVICE_ALREADY_RUNNING) {
                                            alreadyRunning=1;
                                            startError=0;
                                        }
                                    }
                                    if (!startError) {
                                        for (int i=0;i<40;i++) {
                                            RpcServiceStatus current=inspect_rpc_service();
                                            if (current.scm_error || current.open_error ||
                                                    current.query_error) {
                                                queryError=current.scm_error ? current.scm_error :
                                                        current.open_error ? current.open_error :
                                                        current.query_error;
                                                break;
                                            }
                                            afterState=current.state;
                                            if (afterState==SERVICE_RUNNING ||
                                                    (afterState==SERVICE_STOPPED && i>6))
                                                break;
                                            Sleep(200);
                                        }
                                    }
                                }
                            }
                            /* Undo the temporary Manual start setting even
                             * when Win32 startup or status probing failed. */
                            restoreAttempt=1;
                            if (!ChangeServiceConfigW(service,SERVICE_NO_CHANGE,
                                    SERVICE_DISABLED,SERVICE_NO_CHANGE,
                                    NULL,NULL,NULL,NULL,NULL,NULL,NULL)) {
                                restoreError=GetLastError();
                            } else {
                                DWORD checkedType=0;
                                if (!query_rpc_config(service,&checkedType,&restoreError) ||
                                        checkedType!=SERVICE_DISABLED) {
                                    if (!restoreError) restoreError=ERROR_INVALID_DATA;
                                } else {
                                    restoreConfirmed=1;
                                    typeAfter=checkedType;
                                    if (_wremove(path)!=0) {
                                        /* Still keep a marker if cleanup fails:
                                         * next opt-in can reconcile safely. */
                                        recoveryError=ERROR_ACCESS_DENIED;
                                    }
                                }
                            }
                        }
                    } else if (typeAfter==SERVICE_DEMAND_START) {
                        /* Another party may have changed configuration.
                         * Do not overwrite unknown/manual state. */
                        recoveryError=ERROR_INVALID_DATA;
                    }
                }
            }
        }
    }
    /* If original type wasn't disabled, never silently change it. */
    if (service) CloseServiceHandle(service);
    if (scm) CloseServiceHandle(scm);
    RpcServiceStatus after=inspect_rpc_service();
    if (!after.scm_error && !after.open_error && !after.query_error)
        afterState=after.state;
    if (!after.config_error) typeAfter=after.start_type;

    fprintf(report,"monitor_rpc_opt_in_start_requested=1\n");
    fprintf(report,"monitor_rpc_start_before_state=%lu\n",(unsigned long)before.state);
    fprintf(report,"monitor_rpc_start_before_type=%lu\n",(unsigned long)before.start_type);
    fprintf(report,"monitor_rpc_start_config_query_error=%lu\n",
            (unsigned long)before.config_error);
    fprintf(report,"monitor_rpc_start_attempted=%lu\n",(unsigned long)attempt);
    fprintf(report,"monitor_rpc_start_already_running=%lu\n",(unsigned long)alreadyRunning);
    fprintf(report,"monitor_rpc_start_scm_error=%lu\n",(unsigned long)before.scm_error);
    fprintf(report,"monitor_rpc_start_open_error=%lu\n",
            (unsigned long)(before.open_error ? before.open_error : openError));
    fprintf(report,"monitor_rpc_start_win32_error=%lu\n",(unsigned long)startError);
    fprintf(report,"monitor_rpc_start_query_error=%lu\n",
            (unsigned long)(before.query_error ? before.query_error : queryError));
    fprintf(report,"monitor_rpc_start_after_state=%lu\n",(unsigned long)afterState);
    fprintf(report,"monitor_rpc_temporary_enable_attempted=%lu\n",
            (unsigned long)enableAttempt);
    fprintf(report,"monitor_rpc_temporary_enable_error=%lu\n",(unsigned long)enableError);
    fprintf(report,"monitor_rpc_restore_attempted=%lu\n",(unsigned long)restoreAttempt);
    fprintf(report,"monitor_rpc_restore_error=%lu\n",(unsigned long)restoreError);
    fprintf(report,"monitor_rpc_restore_confirmed=%lu\n",(unsigned long)restoreConfirmed);
    fprintf(report,"monitor_rpc_start_type_after=%lu\n",(unsigned long)typeAfter);
    fprintf(report,"monitor_rpc_recovery_marker_pending=%lu\n",
            (unsigned long)pendingRecovery);
    fprintf(report,"monitor_rpc_recovery_error=%lu\n",(unsigned long)recoveryError);
    fflush(report);
    // The next Windows program may launch only after RPC is RUNNING and the
    // original service configuration has been verified/rolled back.
    return afterState == SERVICE_RUNNING &&
            typeAfter == before.start_type &&
            (restoreConfirmed || (before.state == SERVICE_RUNNING && !pendingRecovery)) &&
            !startError && !enableError && !restoreError && !recoveryError &&
            !queryError;
}

/*
 * This mode MUST run inside the same Wine session as the Battle.net launcher.
 * Independent Portal diagnostics start a separate Wine desktop, so their
 * zero-process snapshot cannot be used to infer the launcher's Agent status.
 *
 * Report fixed numeric samples only. Each file is Charoite-owned and small;
 * flush immediately so a crashed Wine session leaves actionable data.
 */
static void monitor_battlenet(FILE *report, int allowRpcStart) {
    int seenAgent=0, seenClient=0, seenLauncher=0;
    int maxAgent=0, maxClient=0, maxLauncher=0, everEnumError=0;
    int seenRpcss=0, seenServices=0, maxRpcss=0, maxServices=0;
    int scmOk=0, rpcRunning=0, rpcStopped=0, rpcUnqueryable=0;
    int rpcDisabled=0, rpcManual=0, rpcConfigFailed=0;
    RpcServiceStatus lastRpc;
    ZeroMemory(&lastRpc, sizeof(lastRpc));
    fprintf(report,"monitor_same_session=1\n");
    fprintf(report,"monitor_rpc_opt_in_start_requested=%d\n",allowRpcStart ? 1:0);
    if (allowRpcStart) try_start_rpc_service(report);
    fprintf(report,"monitor_sample_interval_ms=1800\n");
    fprintf(report,"monitor_expected_samples=16\n");
    fflush(report);
    for (int i=0; i<16; i++) {
        ProcessCounts c=get_process_counts();
        RpcServiceStatus rpc=inspect_rpc_service();
        lastRpc=rpc;
        if (!rpc.scm_error) scmOk++;
        if (rpc.state==SERVICE_RUNNING) rpcRunning++;
        if (rpc.state==SERVICE_STOPPED) rpcStopped++;
        if (rpc.scm_error || rpc.open_error || rpc.query_error) rpcUnqueryable++;
        if (!rpc.config_error && rpc.start_type==SERVICE_DISABLED) rpcDisabled++;
        if (!rpc.config_error && rpc.start_type==SERVICE_DEMAND_START) rpcManual++;
        if (rpc.config_error) rpcConfigFailed++;
        if (c.agents > maxAgent) maxAgent = c.agents;
        if (c.clients > maxClient) maxClient = c.clients;
        if (c.launchers > maxLauncher) maxLauncher = c.launchers;
        if (c.rpcss > maxRpcss) maxRpcss = c.rpcss;
        if (c.services > maxServices) maxServices = c.services;
        if (c.agents) seenAgent++;
        if (c.clients) seenClient++;
        if (c.launchers) seenLauncher++;
        if (c.rpcss) seenRpcss++;
        if (c.services) seenServices++;
        if (c.error) everEnumError++;
        fprintf(report,"monitor_sample_%02d_agent=%d\n",i,c.agents);
        fprintf(report,"monitor_sample_%02d_client=%d\n",i,c.clients);
        fprintf(report,"monitor_sample_%02d_launcher=%d\n",i,c.launchers);
        fprintf(report,"monitor_sample_%02d_rpcss=%d\n",i,c.rpcss);
        fprintf(report,"monitor_sample_%02d_services=%d\n",i,c.services);
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
    fprintf(report,"monitor_rpcss_present_samples=%d\n",seenRpcss);
    fprintf(report,"monitor_services_present_samples=%d\n",seenServices);
    fprintf(report,"monitor_max_rpcss=%d\n",maxRpcss);
    fprintf(report,"monitor_max_services=%d\n",maxServices);
    fprintf(report,"monitor_rpc_scm_connect_success_samples=%d\n",scmOk);
    fprintf(report,"monitor_rpc_service_running_samples=%d\n",rpcRunning);
    fprintf(report,"monitor_rpc_service_stopped_samples=%d\n",rpcStopped);
    fprintf(report,"monitor_rpc_service_query_failed_samples=%d\n",rpcUnqueryable);
    fprintf(report,"monitor_rpc_service_state_last=%lu\n",(unsigned long)lastRpc.state);
    fprintf(report,"monitor_rpc_config_disabled_samples=%d\n",rpcDisabled);
    fprintf(report,"monitor_rpc_config_manual_samples=%d\n",rpcManual);
    fprintf(report,"monitor_rpc_config_query_failed_samples=%d\n",rpcConfigFailed);
    fprintf(report,"monitor_rpc_config_start_type_last=%lu\n",
            (unsigned long)lastRpc.start_type);
    fprintf(report,"monitor_rpc_config_win32_error_last=%lu\n",
            (unsigned long)lastRpc.config_error);
    fprintf(report,"monitor_rpc_scm_error_last=%lu\n",(unsigned long)lastRpc.scm_error);
    fprintf(report,"monitor_rpc_open_error_last=%lu\n",(unsigned long)lastRpc.open_error);
    fprintf(report,"monitor_rpc_query_error_last=%lu\n",(unsigned long)lastRpc.query_error);
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

/* Pre-client gate, invoked by Wine explorer as the FIRST Windows program.
 * Starts RpcSs and restores original Disabled startup mode before spawning
 * the original winhandler.exe and Battle.net client. No shell or batch file:
 * original arguments are forwarded unchanged to CreateProcessW.
 * The client is NOT started when the service fails or rollback is unverified.
 */
static int prelaunch_battlenet(FILE *report, const wchar_t *args) {
    fprintf(report,"preflight_attempted=1\n");
    fprintf(report,"preflight_before_client=1\n");
    fflush(report);
    int rpcReady=try_start_rpc_service(report);
    fprintf(report,"preflight_rpc_ready=%d\n",rpcReady);
    fprintf(report,"preflight_client_spawn_attempted=%d\n",rpcReady);
    fflush(report);
    if (!rpcReady) {
        fprintf(report,"preflight_client_spawn_error=%u\n",0u);
        fprintf(report,"preflight_launch_ready=0\n");
        fflush(report);
        return 51;
    }
    static const wchar_t executable[]=L"C:\\windows\\winhandler.exe";
    static const wchar_t prefix[]=L"\"C:\\windows\\winhandler.exe\" ";
    size_t tail=wcslen(args);
    size_t length=wcslen(prefix)+tail+1;
    if (!tail || length>8192) {
        fprintf(report,"preflight_client_spawn_error=%u\n",
                (unsigned)ERROR_INVALID_PARAMETER);
        fprintf(report,"preflight_launch_ready=0\n");
        fflush(report);
        return 52;
    }
    wchar_t *command=(wchar_t*)malloc(length*sizeof(wchar_t));
    if (!command) {
        fprintf(report,"preflight_client_spawn_error=%u\n",
                (unsigned)ERROR_NOT_ENOUGH_MEMORY);
        fprintf(report,"preflight_launch_ready=0\n");
        fflush(report);
        return 53;
    }
    wcscpy(command,prefix);
    wcscat(command,args);
    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup,sizeof(startup));
    ZeroMemory(&process,sizeof(process));
    startup.cb=sizeof(startup);
    BOOL started=CreateProcessW(executable,command,NULL,NULL,FALSE,
            0,NULL,NULL,&startup,&process);
    DWORD error=started ? 0 : GetLastError();
    free(command);
    fprintf(report,"preflight_client_spawn_error=%lu\n",(unsigned long)error);
    fprintf(report,"preflight_launch_ready=%d\n",started ? 1:0);
    fflush(report);
    if (!started) return 54;
    // Keep the parent Wine session alive while the original WinHandler runs.
    // Never log the command line or any Blizzard account information.
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess,INFINITE);
    CloseHandle(process.hProcess);
    return 0;
}

int WINAPI WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR args,int show) {
    (void)instance; (void)previous; (void)args; (void)show;
    wchar_t path[MAX_PATH];
    DWORD length=GetModuleFileNameW(NULL,path,MAX_PATH);
    if (!length || length>=MAX_PATH) return 2;
    wchar_t *slash=wcsrchr(path,L'\\');
    if (!slash) return 3;
    const wchar_t *cmd=GetCommandLineW();
    const wchar_t *prelaunch=cmd ? wcsstr(cmd,L"/preflight-launch ") : NULL;
    int monitor = !prelaunch && cmd && wcsstr(cmd,L"/monitor") != NULL;
    int tryRpcStart = monitor && cmd && wcsstr(cmd,L"/try-rpcss-start") != NULL;
    wcscpy(slash+1, prelaunch ? L"charoite_bnet_rpc_preflight.txt" :
            monitor ? L"charoite_bnet_launch_monitor.txt" :
            L"charoite_bnet_network_report.txt");
    FILE *report=_wfopen(path,L"w");
    if (!report) return 4;
    if (prelaunch) {
        fprintf(report,"Charoite Battle.net before-client RpcSs preflight v1\n");
        int status=prelaunch_battlenet(report,
                prelaunch+wcslen(L"/preflight-launch "));
        fclose(report);
        return status;
    }
    if (monitor) {
        fprintf(report,"Charoite in-session Battle.net process monitor v6\n");
        monitor_battlenet(report,tryRpcStart);
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
