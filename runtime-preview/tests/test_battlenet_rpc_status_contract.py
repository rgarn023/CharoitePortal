"""Read-only RpcSs/CEF diagnostics for Battle.net's spinning login window."""
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
NATIVE = (BASE / "charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
SUPPORT = (BASE / "charoite-core/CharoiteBattleNetSupport.java").read_text()
WORKFLOW = (BASE.parent / ".github/workflows/runtime-preview.yml").read_text()

class BattleNetRpcServiceContract(unittest.TestCase):
    def test_scm_query_is_read_only_and_same_session(self):
        for token in ('OpenSCManagerW(NULL, NULL, SC_MANAGER_CONNECT)',
                      'OpenServiceW(scm, L"RpcSs", SERVICE_QUERY_STATUS)',
                      'QueryServiceStatusEx(', 'SC_STATUS_PROCESS_INFO',
                      'SERVICE_RUNNING', 'SERVICE_STOPPED',
                      'monitor_rpc_service_running_samples=%d',
                      'monitor_rpc_service_stopped_samples=%d',
                      'monitor_rpc_service_query_failed_samples=%d',
                      'monitor_rpc_scm_error_last=%lu',
                      'monitor_rpc_open_error_last=%lu',
                      'monitor_rpc_query_error_last=%lu',
                      'monitor_rpc_service_state_last=%lu',
                      'monitor_rpc_scm_connect_success_samples=%d',
                      'monitor_same_session=1', 'Sleep(1800)',
                      'monitor_complete=1'):
            self.assertIn(token, NATIVE)
        for forbidden in ('StartServiceW(', 'ControlService(', 'DeleteService(',
                          'ChangeServiceConfig', 'RegSetValue', 'DeleteFileW(',
                          'TerminateProcess('):
            self.assertNotIn(forbidden, NATIVE)
        self.assertIn('-lwinhttp -lws2_32 -luser32 -ladvapi32', WORKFLOW)

    def test_bounded_report_identifies_service_state_not_process_guess(self):
        self.assertIn('private static int monitorNumber(', SUPPORT)
        self.assertIn('java.util.LinkedHashMap<String, String> fields', SUPPORT)
        self.assertIn('monitor_rpc_service_running_samples', SUPPORT)
        self.assertIn('monitor_rpc_service_stopped_samples', SUPPORT)
        self.assertIn('monitor_rpc_service_query_failed_samples', SUPPORT)
        self.assertIn('reported RpcSs RUNNING', SUPPORT)
        self.assertIn('RpcSs was reported STOPPED', SUPPORT)
        self.assertIn('an absent rpcss.exe name', SUPPORT.lower().replace("the wine service control manager ", ""))
        self.assertIn('No Service Control Manager query recorded', SUPPORT)
        self.assertIn('Process existence does not prove IPC or login works.', SUPPORT)
        self.assertIn('line.startsWith("monitor_sample_")', SUPPORT)
        self.assertIn('fields.put(line.substring(0, separator)', SUPPORT)
        self.assertIn('No Blizzard files, process logs or personal data', SUPPORT)

    def test_finer_cef_categories_only_count_error_lines(self):
        for key in ('GPU-process references:', 'Device-lost/removed references:',
                    'Memory-protection references:', 'RPC/service-manager references:'):
            self.assertIn(key, SUPPORT)
        self.assertIn('if(!(line.contains("error") || line.contains("fail") ||', SUPPORT)
        self.assertIn('new java.io.RandomAccessFile(file,"r")', SUPPORT)
        self.assertNotIn('out.append(line)', SUPPORT)

if __name__ == "__main__":
    unittest.main()
