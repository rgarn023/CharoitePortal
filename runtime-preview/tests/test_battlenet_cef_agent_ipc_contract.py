"""Bounded read-only Battle.net CEF child and Agent loopback probe contracts."""
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
NATIVE=(BASE/"charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
SUPPORT=(BASE/"charoite-core/CharoiteBattleNetSupport.java").read_text()
WORKFLOW=(BASE.parent/".github/workflows/runtime-preview.yml").read_text()

class BattleNetCefAgentIPCContract(unittest.TestCase):
    def test_never_read_cef_command_lines_secrets_or_process_memory(self):
        self.assertIn('CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)',NATIVE)
        self.assertIn('proc.th32ParentProcessID',NATIVE)
        self.assertIn('monitor_max_client_children=%d',NATIVE)
        self.assertIn('monitor_client_child_present_samples=%d',NATIVE)
        for banned in ('ReadProcessMemory(', 'NtQueryInformationProcess(',
                       'GetCommandLineW(process', 'OpenProcess(',
                       'GetWindowTextW('):
            self.assertNotIn(banned,NATIVE)

    def test_historical_agent_loopback_1120_is_bounded_and_no_http(self):
        self.assertIn('probe_agent_loopback_1120(DWORD *lastError)',NATIVE)
        self.assertIn('endpoint.sin_addr.s_addr=htonl(INADDR_LOOPBACK)',NATIVE)
        self.assertIn('endpoint.sin_port=htons(1120)',NATIVE)
        self.assertIn('timeout.tv_usec=200000',NATIVE)
        self.assertIn('if ((i%4)==3)',NATIVE)
        self.assertIn('monitor_agent_loopback_1120_tests=%d',NATIVE)
        self.assertIn('monitor_agent_loopback_1120_connect_success=%d',NATIVE)
        self.assertIn('monitor_agent_loopback_1120_last_winsock_error=%lu',NATIVE)
        self.assertIn('closesocket(sock);',NATIVE)
        local_probe=NATIVE.split('static int probe_agent_loopback_1120(',1)[1].split(
            '/* Query the Wine service manager',1)[0]
        for banned in ('send(sock', 'recv(sock', 'HttpSendRequest(',
                       'WinHttpReadData(', 'getaddrinfo(', 'gethostbyname('):
            self.assertNotIn(banned,local_probe)
        self.assertIn('-lwinhttp -lws2_32 -luser32 -ladvapi32 -liphlpapi',WORKFLOW)

    def test_agent_owner_listener_lookup_is_read_only_and_pid_scoped(self):
        for token in ('#include <iphlpapi.h>',
                'TCP_TABLE_OWNER_PID_LISTENER', 'MIB_TCPTABLE_OWNER_PID',
                'MIB_TCP_STATE_LISTEN',
                'entry->dwOwningPid==counts->agent_pids[a]',
                'monitor_agent_tcp_ipv4_owner_queries=%d',
                'monitor_agent_tcp_ipv4_owner_query_success=%d',
                'monitor_agent_tcp_ipv4_listener_present_samples=%d',
                'monitor_agent_tcp_ipv4_max_listeners=%d',
                'monitor_agent_tcp_ipv4_max_loopback_listeners=%d',
                'monitor_agent_tcp_ipv4_example_loopback_port=%lu',
                'monitor_agent_tcp_ipv4_last_query_error=%lu'):
            self.assertIn(token,NATIVE)
        self.assertIn('required>512*1024',NATIVE)
        self.assertIn('if ((i%4)==3)',NATIVE)
        self.assertIn('if (!owned) continue;',NATIVE)
        query=NATIVE.split('static int inspect_agent_owned_ipv4_listeners(',1)[1].split(
            '/* Query the Wine service manager',1)[0]
        for forbidden in ('connect(', 'send(', 'recv(', 'ReadProcessMemory(',
                'WinHttpSendRequest(', 'fprintf(', 'RegSetValue'):
            self.assertNotIn(forbidden,query)
        self.assertIn('Read-only Agent.exe IPv4 TCP listener ownership query:',SUPPORT)
        self.assertIn('Do not interpret this as',SUPPORT)
        self.assertNotIn('entry->dwOwningPid)',NATIVE.split('monitor_battlenet(',1)[1])

    def test_passive_ipc_correlation_tracks_only_current_agent_and_client_pids(self):
        for token in ('TCP_TABLE_OWNER_PID_ALL',
                      'static int inspect_agent_client_ipv4_connections(',
                      'entry->dwOwningPid==counts->agent_pids[a]',
                      'entry->dwOwningPid==counts->client_pids[c]',
                      'entry->dwRemotePort==agentListenerPorts[a]',
                      'entry->dwRemoteAddr!=htonl(INADDR_LOOPBACK)',
                      'entry->dwState!=MIB_TCP_STATE_ESTAB',
                      'monitor_agent_ipc_tcp_connection_queries=%d',
                      'monitor_agent_ipc_tcp_connection_query_success=%d',
                      'monitor_agent_ipc_tcp_agent_established_max=%d',
                      'monitor_agent_ipc_tcp_client_established_max=%d',
                      'monitor_agent_ipc_tcp_client_to_agent_present_samples=%d',
                      'monitor_agent_ipc_tcp_client_to_agent_max=%d',
                      'monitor_agent_ipc_tcp_last_query_error=%lu'):
            self.assertIn(token,NATIVE)
        self.assertIn('required>512*1024',NATIVE)
        passive=NATIVE.split(
            'static int inspect_agent_client_ipv4_connections(',1)[1].split(
            '/* Query the Wine service manager',1)[0]
        for forbidden in ('connect(', 'send(', 'recv(', 'fprintf(',
                          'ReadProcessMemory(', 'GetCommandLineW(',
                          'WinHttpSendRequest(', 'RegSetValue('):
            self.assertNotIn(forbidden,passive)
        self.assertIn('Passive Battle.net-to-Agent IPv4 TCP correlation:',SUPPORT)
        self.assertIn('A zero match can miss short-lived connections',SUPPORT)
        self.assertIn('This does not read traffic',SUPPORT)
        self.assertNotIn('entry->dwRemoteAddr)',NATIVE.split('monitor_battlenet(',1)[1])

    def test_report_is_bounded_no_raw_logs_and_no_overconfidence(self):
        for token in ('monitor_max_client_children',
                      'monitor_agent_loopback_1120_tests',
                      'monitor_agent_loopback_1120_connect_success',
                      'historical port', 'cannot verify login/auth',
                      'Chromium subprocess type and',
                      'Sampled log files modified since RPC preflight:',
                      'Empty CEF/login URL references:',
                      'Browser/CEF subprocess exit references:',
                      'TLS/certificate references:',
                      'can still contain older lines; category counts overlap.'):
            self.assertIn(token,SUPPORT)
        self.assertIn('new java.io.RandomAccessFile(file,"r")',SUPPORT)
        self.assertIn('Math.min(logs.size(),6)',SUPPORT)
        self.assertIn('Math.max(0,input.length()-32768)',SUPPORT)
        self.assertNotIn('output.append(sample)',SUPPORT)
        self.assertNotIn('out.append(line)',SUPPORT)

if __name__=="__main__":
    unittest.main()
