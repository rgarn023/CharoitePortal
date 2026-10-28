"""Battle.net run-specific, privacy-preserving renderer and GPU flag evidence."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OVERLAY=(ROOT/"overlay.py").read_text()
SUPPORT=(ROOT/"charoite-core/CharoiteBattleNetSupport.java").read_text()
SESSIONS=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
UI=(ROOT/"TouhouEntryActivity.java").read_text()

class BattleNetFingerprintContracts(unittest.TestCase):
    def test_requested_and_resolved_modes_are_distinct_and_scoped(self):
        self.assertIn('charoite_bnet_monitor", false)',OVERLAY)
        self.assertIn('"battle-net-gaming".equals(',OVERLAY)
        self.assertIn('recordBattleNetLaunchCommand(',OVERLAY)
        self.assertIn('charoiteNormalWinHandler.contains(" --disable-gpu")',OVERLAY)
        self.assertIn('GraphicsDrivers.VIRGL.equals(this.graphicsDriver[1])',OVERLAY)
        self.assertIn('DXWrappers.WINED3D.equals(this.dxwrapper)',OVERLAY)
        self.assertIn('recordBattleNetRuntimeEnv(',OVERLAY)
        self.assertIn('"0".equals(envVars.get("WINEESYNC"))',OVERLAY)
        self.assertIn('"0".equals(envVars.get("WINEFSYNC"))',OVERLAY)
        self.assertIn('locationapi=',OVERLAY)
        self.assertIn('getIntent().getBooleanExtra("charoite_bnet_rpc_preflight", false)',OVERLAY)
        self.assertIn('getIntent().getBooleanExtra("charoite_bnet_agent_compatibility", false)',OVERLAY)
        self.assertIn('getIntent().getBooleanExtra("charoite_bnet_disable_gpu", false)',OVERLAY)
        self.assertIn('tryStartBattleNetRpc && !installer',SESSIONS)
        self.assertIn('launchBattleNetRpcTest(true)',UI)
        self.assertIn('launchBattleNetRpcTest(false)',UI)

    def test_fingerprint_has_numeric_only_fields_and_no_program_data_mutation(self):
        for field in ('launch_rpc_requested', 'launch_compatibility_requested',
            'launch_disable_gpu_requested', 'launch_disable_gpu_command_present',
            'launch_renderer_virgl_resolved', 'launch_dxwrapper_wined3d_resolved',
            'launch_env_esync_off','launch_env_fsync_off',
            'launch_env_locationapi_rule_present'):
            self.assertIn(field,SUPPORT)
        self.assertIn('System.currentTimeMillis()',SUPPORT)
        self.assertIn('charoite_bnet_launch_command.txt',SUPPORT)
        self.assertIn('charoite_bnet_launch_env.txt',SUPPORT)
        self.assertIn('if (found>0 && System.currentTimeMillis()-newest>3600000)',SUPPORT)
        self.assertIn('newest-oldest>10000',SUPPORT)
        method=SUPPORT.split('private static void writeBnetLaunchFingerprint(',1)[1].split(
            'public static String inspectBattleNetLaunchFingerprint(',1)[0]
        self.assertIn('CharoitePortal/Diagnostics',method)
        self.assertIn('Files.write(file.toPath()',method)
        for forbidden in ('ProgramData/', 'AppData/', 'delete(', 'renameTo(',
            'Agent.exe', 'WinHttp', 'getWineStartCommand()', 'getIntent()'):
            self.assertNotIn(forbidden,method)

    def test_login_report_includes_fingerprint_even_when_monitor_missing(self):
        self.assertIn('inspectBattleNetLaunchFingerprint(root)',SUPPORT)
        self.assertIn('inspectGuestRpcPreflight(root) + "\\n" +',SUPPORT)
        self.assertIn('out.toString() + "\\n" + inspectGuestRpcPreflight(root) +',SUPPORT)
        self.assertIn('BATTLE.NET LAUNCH FINGERPRINT',SUPPORT)
        self.assertIn('not proof CEF honored them',SUPPORT)
        self.assertIn('WARNING: snapshots more than 10 seconds apart;',SUPPORT)
        self.assertIn('WARNING: launch fingerprint older than one hour.',SUPPORT)
        self.assertIn('VIEW BATTLE.NET LOGIN / CEF REPORT',UI)

if __name__=="__main__":
    unittest.main()
