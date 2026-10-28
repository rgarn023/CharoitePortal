"""Safety and evidence contracts for opt-in Battle.net RpcSs start experiment."""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
NATIVE=(BASE/"charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
CORE=(BASE/"charoite-core/CharoiteGameSessions.java").read_text()
OVERLAY=(BASE/"overlay.py").read_text()
PORTAL=(BASE/"TouhouEntryActivity.java").read_text()
REPORT=(BASE/"charoite-core/CharoiteBattleNetSupport.java").read_text()

class BattleNetRpcOptInContract(unittest.TestCase):
    def test_explicit_user_confirmation_before_same_session_service_start(self):
        self.assertIn('TRY BATTLE.NET (START WINE RPC SERVICE)',PORTAL)
        self.assertIn('this::confirmBattleNetRpcStartup',PORTAL)
        method=PORTAL.split('private void confirmBattleNetRpcStartup()',1)[1].split(
            '/** Explicitly requested browser preference change;',1)[0]
        self.assertIn('setPositiveButton("Try once"',method)
        self.assertIn('setNegativeButton("Cancel", null)',method)
        self.assertIn('setNeutralButton("RPC + graphics"',method)
        self.assertIn('launchBattleNetRpcTest(true)',method)
        self.assertIn('launchBattleNetRpcTest(false)',method)
        helper=PORTAL.split('private void launchBattleNetRpcTest(boolean compatibilityGraphics)',1)[1].split(
            'private void confirmBattleNetRpcStartup()',1)[0]
        self.assertIn('CharoiteGameSessions.launch(',helper)
        self.assertIn('compatibilityGraphics, true, false, true)',helper)
        self.assertIn('installedDirectClient(root)',helper)
        self.assertIn('installedLauncher(root)',helper)
        self.assertIn('if (busy) return;',helper)
        self.assertNotIn('.delete(',method)
        self.assertNotIn('backupAndResetBrowserCache',method)

    def test_flag_is_restricted_to_installed_blizzard_client_and_active_realm(self):
        self.assertIn('boolean tryStartBattleNetRpc)',CORE)
        self.assertIn('play.putExtra("charoite_bnet_try_start_rpc",',CORE)
        self.assertIn('tryStartBattleNetRpc && !installer &&',CORE)
        self.assertIn('CharoiteEnvironments.isBattleNet(host)',CORE)
        self.assertIn('installedBattleNetLauncher);',CORE)
        self.assertIn('getBooleanExtra("charoite_bnet_try_start_rpc", false)',OVERLAY)
        self.assertIn('? "/monitor /try-rpcss-start" : "/monitor"',OVERLAY)
        self.assertIn('winHandler.exec(',OVERLAY)
        self.assertIn('charoite_bnet_monitor',OVERLAY)

    def test_native_service_start_only_opt_in_and_no_persistent_changes(self):
        self.assertIn('wcsstr(cmd,L"/try-rpcss-start")',NATIVE)
        self.assertIn('monitor_battlenet(report,tryRpcStart);',NATIVE)
        self.assertIn('if (allowRpcStart) try_start_rpc_service(report);',NATIVE)
        self.assertIn('before.state==SERVICE_STOPPED',NATIVE)
        self.assertIn('StartServiceW(service,0,NULL)',NATIVE)
        self.assertIn('SERVICE_START |',NATIVE)
        self.assertIn('SERVICE_QUERY_STATUS | SERVICE_QUERY_CONFIG |',NATIVE)
        self.assertIn('SERVICE_CHANGE_CONFIG',NATIVE)
        self.assertIn('monitor_rpc_start_before_state=',NATIVE)
        self.assertIn('monitor_rpc_start_after_state=',NATIVE)
        self.assertIn('monitor_rpc_start_win32_error=',NATIVE)
        self.assertIn('monitor_rpc_opt_in_start_requested=',NATIVE)
        self.assertIn('if (!startError)',NATIVE)
        self.assertIn('ChangeServiceConfigW(service,SERVICE_NO_CHANGE,',NATIVE)
        self.assertIn('SERVICE_DEMAND_START,SERVICE_NO_CHANGE',NATIVE)
        self.assertIn('SERVICE_DISABLED,SERVICE_NO_CHANGE',NATIVE)
        self.assertIn('rpc_write_marker(path)',NATIVE)
        self.assertIn('rpc_recover_pending(service,path,',NATIVE)
        self.assertIn('monitor_rpc_restore_confirmed=',NATIVE)
        self.assertIn('monitor_rpc_recovery_error=',NATIVE)
        self.assertIn('monitor_rpc_start_before_type=',NATIVE)
        self.assertIn('if (i<15) Sleep(1800)',NATIVE.replace('if(i<15)', 'if (i<15)'))
        for forbidden in ('DeleteService(', 'RegSetValue',
                          'RegDeleteValue(', 'TerminateProcess(', 'DeleteFileW('):
            self.assertNotIn(forbidden,NATIVE)

    def test_readout_reports_results_and_preserves_other_game_paths(self):
        self.assertIn('monitor_rpc_start_attempted',REPORT)
        self.assertIn('monitor_rpc_start_after_state',REPORT)
        self.assertIn('OPT-IN RpcSs START:',REPORT)
        self.assertIn('start error:',REPORT)
        self.assertIn('STARTUP CONFIGURATION RESTORED:',REPORT)
        self.assertIn('RESTORATION NOT CONFIRMED:',REPORT)
        self.assertIn('restored afterward',PORTAL)
        self.assertIn('its original Disabled startup',PORTAL)
        self.assertIn('temporary WineD3D/',PORTAL)
        self.assertIn('VirGL rendering',PORTAL)
        self.assertIn('disables ESYNC/FSYNC',PORTAL)
        self.assertIn('The Wine Service Control Manager reported RpcSs RUNNING',REPORT)
        self.assertIn('CharoiteTpdpTouchControls.attach(',OVERLAY)
        self.assertIn('CharoiteLegacyKeyboard.sendScan(',OVERLAY)
        self.assertIn('cmdArgs += " --disable-gpu";',OVERLAY)

if __name__=="__main__":
    unittest.main()
