"""Pre-client Battle.net RPC initialization and privacy rollback contracts."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NATIVE=(ROOT/"charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
SESSIONS=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
SUPPORT=(ROOT/"charoite-core/CharoiteBattleNetSupport.java").read_text()
UI=(ROOT/"TouhouEntryActivity.java").read_text()

class BattleNetPreClientRpcContract(unittest.TestCase):
    def test_only_battlenet_confirmed_opt_in_sets_preflight_flag(self):
        self.assertIn('play.putExtra("charoite_bnet_rpc_preflight",',SESSIONS)
        self.assertIn('tryStartBattleNetRpc && !installer &&',SESSIONS)
        self.assertIn('installedBattleNetLauncher);',SESSIONS)
        self.assertIn('CharoiteEnvironments.isBattleNet(host)',SESSIONS)
        self.assertIn('setPositiveButton("Try once"',UI)
        self.assertIn('TRY BATTLE.NET (START WINE RPC SERVICE)',UI)

    def test_first_wine_guest_program_is_preflight_not_battle_net(self):
        self.assertIn('bnet_prelaunch_anchor',OVERLAY)
        self.assertIn('assert code.count(bnet_prelaunch_anchor) == 1',OVERLAY)
        self.assertIn('String charoiteNormalWinHandler = getWineStartCommand();',OVERLAY)
        self.assertIn('getBooleanExtra("charoite_bnet_rpc_preflight", false)',OVERLAY)
        self.assertIn('"battle-net-gaming".equals(',OVERLAY)
        self.assertIn('prepareGuestNetworkProbe(',OVERLAY)
        self.assertIn('charoite_bnet_network_probe.exe /preflight-launch ',OVERLAY)
        self.assertIn('charoiteNormalWinHandler.substring(winHandlerPrefix.length())',OVERLAY)
        self.assertIn('RPC_PREFLIGHT_ARMED',OVERLAY)
        self.assertIn('RPC_PREFLIGHT_PREPARE_FAILED',OVERLAY)
        # Live monitor remains separate and does not run the second opt-in start.
        self.assertIn('!getIntent().getBooleanExtra("charoite_bnet_rpc_preflight", false)',OVERLAY)

    def test_preflight_requires_rpc_ready_and_verified_rollback_before_client(self):
        self.assertIn('wcsstr(cmd,L"/preflight-launch ")',NATIVE)
        self.assertIn('L"charoite_bnet_rpc_preflight.txt"',NATIVE)
        self.assertIn('static int prelaunch_battlenet(FILE *report, const wchar_t *args)',NATIVE)
        self.assertIn('int rpcReady=try_start_rpc_service(report);',NATIVE)
        self.assertIn('if (!rpcReady)',NATIVE)
        self.assertIn('preflight_client_spawn_attempted=%d',NATIVE)
        self.assertIn('preflight_launch_ready=%d',NATIVE)
        self.assertIn('CreateProcessW(executable,command,NULL,NULL,FALSE,',NATIVE)
        self.assertIn('WaitForSingleObject(process.hProcess,INFINITE)',NATIVE)
        self.assertIn('afterState == SERVICE_RUNNING',NATIVE)
        self.assertIn('restoreConfirmed',NATIVE)
        self.assertIn('rpc_recover_pending(service,path,',NATIVE)
        self.assertIn('!startError && !enableError && !restoreError && !recoveryError',NATIVE)
        self.assertNotIn('system(',NATIVE)
        self.assertNotIn('WinExec(',NATIVE)
        self.assertNotIn('ShellExecuteW(',NATIVE)

    def test_preflight_readout_is_numeric_only(self):
        self.assertIn('public static String inspectGuestRpcPreflight(File root)',SUPPORT)
        self.assertIn('inspectGuestRpcPreflight(root)',SUPPORT)
        # The early exit is important: preflight may abort BEFORE there is any
        # renderable window, so the ordinary live monitor file won't exist.
        self.assertIn('briefly, then return to this dedicated monitor view.\\n\\n" +',SUPPORT)
        self.assertIn('preflight_rpc_ready',SUPPORT)
        self.assertIn('preflight_launch_ready',SUPPORT)
        self.assertIn('BATTLE.NET BEFORE-CLIENT RPC PREFLIGHT',SUPPORT)
        self.assertIn('line.matches("(monitor_rpc_[a-z_0-9]{3,55}|preflight_[a-z_0-9]{3,55})=',SUPPORT)
        self.assertNotIn('out.append(raw)',SUPPORT)

if __name__=="__main__":
    unittest.main()
