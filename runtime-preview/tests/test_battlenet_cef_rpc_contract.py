"""Regression contract for Battle.net CEF GPU-process experiment and RPC sampling."""
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
NATIVE = (BASE / "charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
SUPPORT = (BASE / "charoite-core/CharoiteBattleNetSupport.java").read_text()
SESSIONS = (BASE / "charoite-core/CharoiteGameSessions.java").read_text()
OVERLAY = (BASE / "overlay.py").read_text()
PORTAL = (BASE / "TouhouEntryActivity.java").read_text()


class BattleNetCefRpcContract(unittest.TestCase):
    def test_rpc_presence_is_monitored_inside_the_existing_wine_session(self):
        for token in ('L"rpcss.exe"', 'L"services.exe"', 'monitor_rpcss_present_samples=%d',
                      'monitor_services_present_samples=%d', 'monitor_max_rpcss=%d',
                      'monitor_max_services=%d', 'monitor_complete=1',
                      'monitor_same_session=1'):
            self.assertIn(token, NATIVE)
        self.assertIn('monitor_rpcss_present_samples=', SUPPORT)
        self.assertIn('can guide an IPC investigation', SUPPORT)
        self.assertIn('presence does not ', SUPPORT)
        self.assertIn('This sample predates Wine RPC service monitoring;', SUPPORT)
        self.assertIn('CharoiteBattleNetSupport.inspectInSessionAgentMonitor(root)', PORTAL)
        self.assertIn('VIEW LIVE AGENT MONITOR', PORTAL)

    def test_gpu_trial_is_scoped_to_one_opt_in_client_launch(self):
        self.assertIn('TRY BATTLE.NET (CEF GPU PROCESS TEST)', PORTAL)
        self.assertIn('this::openBattleNetGpuProcess', PORTAL)
        self.assertIn('private void openBattleNetGpuProcess()', PORTAL)
        start = PORTAL.index('private void openBattleNetGpuProcess()')
        end = PORTAL.index('private void applyBattleNetBrowserFix()', start)
        trial = PORTAL[start:end]
        self.assertIn('installedDirectClient(root)', trial)
        self.assertIn('installedLauncher(root)', trial)
        self.assertIn('false, false,\n                    false, false, true)', trial)
        self.assertNotIn('.delete(', trial)
        self.assertNotIn('backupAndResetBrowserCache(', trial)

        self.assertIn('boolean inProcessBrowserGpu)', SESSIONS)
        self.assertIn('play.putExtra("charoite_bnet_in_process_gpu",', SESSIONS)
        self.assertIn('inProcessBrowserGpu && !disableBattleNetBrowserGpu &&', SESSIONS)
        self.assertIn('!installer && CharoiteEnvironments.isBattleNet(host)', SESSIONS)
        self.assertIn('installedBattleNetLauncher);', SESSIONS)
        self.assertIn('getBooleanExtra("charoite_bnet_in_process_gpu", false)', OVERLAY)
        self.assertIn('filename.equalsIgnoreCase("Battle.net.exe")', OVERLAY)
        self.assertIn('filename.equalsIgnoreCase("Battle.net Launcher.exe")', OVERLAY)
        self.assertIn('cmdArgs += " --in-process-gpu";', OVERLAY)

    def test_previous_battlenet_and_touhou_behaviors_preserved(self):
        self.assertIn('cmdArgs += " --disable-gpu";', OVERLAY)
        self.assertIn('play.putExtra("charoite_bnet_monitor",', SESSIONS)
        self.assertIn('monitor_agent_present_samples=%d', NATIVE)
        self.assertIn('CharoiteLegacyKeyboard.sendScan(', OVERLAY)
        self.assertIn('CharoiteTpdpTouchControls.attach(', OVERLAY)
        self.assertNotIn('Files.delete(', SUPPORT.split('public static String inspectInSessionAgentMonitor', 1)[1].split('public static String inspectLauncherStartup', 1)[0])


if __name__ == "__main__":
    unittest.main()
