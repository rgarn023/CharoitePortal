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
        for banned in ('send(sock', 'recv(sock', 'HttpSendRequest(',
                       'WinHttpReadData(', 'getaddrinfo(', 'gethostbyname('):
            self.assertNotIn(banned,NATIVE)
        self.assertIn('-lwinhttp -lws2_32 -luser32 -ladvapi32',WORKFLOW)

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
