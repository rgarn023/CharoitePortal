"""Battle.net environment is additive and downloads only official PC installers."""
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
ENV = (BASE/"charoite-core/CharoiteEnvironments.java").read_text()
CORE = (BASE/"charoite-core/CharoiteBattleNetSupport.java").read_text()
UI = (BASE/"TouhouEntryActivity.java").read_text()
SESSIONS = (BASE/"charoite-core/CharoiteGameSessions.java").read_text()

class BattleNetEnvironmentContract(unittest.TestCase):
    def test_third_realm_is_added_without_legacy_mutation(self):
        self.assertIn('public static final String BATTLE_NET = "battle-net-gaming";', ENV)
        self.assertIn('make(BATTLE_NET, "Battle.net Gaming", "battlenet", 0)', ENV)
        upgrade = ENV.split('if (p.contains(KEY)) {',1)[1].split('int legacyId',1)[0]
        self.assertIn('if (hasGeneral && hasTouhou && hasBattleNet) return;', upgrade)
        self.assertIn('if (!hasBattleNet)', upgrade)
        self.assertNotIn('putString(ACTIVE,', upgrade)
        self.assertNotIn('delete(', upgrade)
        self.assertIn('return TOUHOU.equals(id) ? "game_library" : "charoite_library_" + id;', ENV)
        self.assertIn('legacy == null ? 0 : legacy.id', ENV)

    def test_blizzard_official_live_redirect_and_validated_pe(self):
        self.assertIn('https://downloader.battle.net/download/getInstallerForGame', CORE)
        self.assertIn('gameProgram=BATTLENET_APP&version=Live', CORE)
        self.assertIn('connection.setInstanceFollowRedirects(false)', CORE)
        self.assertIn('trustedWindowsDownload(url)', CORE)
        self.assertIn('!"https".equalsIgnoreCase(target.getProtocol())', CORE)
        self.assertIn('!validPe(part)', CORE)
        self.assertIn('StandardCopyOption.ATOMIC_MOVE', CORE)
        self.assertIn('StandardCopyOption.REPLACE_EXISTING', CORE)
        self.assertIn('CharoiteEnvironments.storageFolder(', CORE)
        self.assertIn('CharoiteEnvironments.BATTLE_NET, "Installers"', CORE)
        # An older downloaded installer remains available without migration.
        self.assertIn('"CharoitePortal/BattleNet/Installer/" + FILENAME', CORE)
        self.assertIn('if (part.exists()) part.delete();', CORE)
        self.assertIn('File installedLauncher(File root)', CORE)
        self.assertNotIn('System.load(', CORE)
        self.assertNotIn('Runtime.getRuntime().exec(', CORE)
        self.assertNotIn('container.saveData(', CORE)

    def test_download_never_executes_and_ui_requires_confirmed_run(self):
        self.assertIn('if (CharoiteEnvironments.isBattleNet(this))', UI)
        self.assertIn('this::downloadBattleNetInstaller', UI)
        self.assertIn('this::installBattleNet', UI)
        self.assertIn('this::openBattleNet', UI)
        self.assertIn('CharoiteBattleNetSupport.downloadLatestInstaller(root)', UI)
        self.assertIn('CharoiteBattleNetSupport.downloadedInstaller(battleNetRoot())', UI)
        self.assertIn('CharoiteBattleNetSupport.installedLauncher(battleNetRoot())', UI)
        self.assertIn('containerId, exe.getAbsolutePath(), true, false)', UI)
        self.assertIn('containerId, exe.getAbsolutePath(), false, false)', UI)
        self.assertIn('CharoiteGameSessions.launch(', UI)
        self.assertIn('play.putExtra("charoite_handheld_game", !installer && gamePresentation &&', SESSIONS)
        self.assertIn('boolean disableBattleNetBrowserGpu', SESSIONS)
        self.assertIn('play.putExtra("charoite_bnet_disable_gpu"', SESSIONS)
        self.assertIn('disableBattleNetBrowserGpu && !installer &&', SESSIONS)
        self.assertIn('installedBattleNetLauncher', SESSIONS)
        self.assertIn('OPEN BATTLE.NET (SAFE BROWSER)', UI)
        self.assertIn('OPEN BATTLE.NET (ORIGINAL)', UI)
        self.assertIn('this::openBattleNetOriginal', UI)
        self.assertIn('false, false,\n                    false, true)', UI)
        self.assertIn('CharoiteBattleNetSupport.inspectLauncherStartup(root)', UI)
        self.assertIn('public static String inspectLauncherStartup(File root)', CORE)
        self.assertIn('No game files, logs or Agent state have been changed.', CORE)

    def test_blizzard_browser_args_applied_only_to_launcher(self):
        overlay = (BASE/"overlay.py").read_text()
        self.assertIn('bnet_cmd_anchor =', overlay)
        self.assertIn('charoite_bnet_disable_gpu', overlay)
        self.assertIn('battle-net-gaming', overlay)
        self.assertIn('filename.equalsIgnoreCase("Battle.net Launcher.exe")', overlay)
        self.assertIn('cmdArgs += " --disable-gpu";', overlay)
        self.assertIn('assert code.count(bnet_cmd_anchor) == 1', overlay)
        self.assertNotIn('root.delete()', CORE)


    def test_live_monitor_uses_same_wine_session_as_battlenet(self):
        native = (BASE/"charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
        overlay = (BASE/"overlay.py").read_text()
        sessions = (BASE/"charoite-core/CharoiteGameSessions.java").read_text()
        for token in (
            'monitor_same_session=1', 'monitor_samples_completed=%d',
            'monitor_agent_present_samples=%d', 'monitor_max_agent=%d',
            'charoite_bnet_launch_monitor.txt', 'Sleep(1800)',
            'GetCommandLineW()', 'monitor_complete=1'
        ):
            self.assertIn(token, native)
        for token in (
            'charoite_bnet_monitor', 'startCharoiteBattleNetMonitor()',
            'isCharoiteKeyboardReady()', '"/monitor"',
            'CharoiteBattleNetSupport.prepareGuestNetworkProbe('
        ):
            self.assertIn(token, overlay)
        self.assertIn('play.putExtra("charoite_bnet_monitor"', sessions)
        self.assertIn('!installer && CharoiteEnvironments.isBattleNet(host)', sessions)
        self.assertIn('inspectInSessionAgentMonitor(File root)', CORE)
        self.assertIn('CharoiteBattleNetSupport.inspectInSessionAgentMonitor(root)', UI)

    def test_windows_guest_probe_is_opt_in_and_report_is_bounded(self):
        from pathlib import Path
        native=(BASE/"charoite-core/diagnostics/charoite_bnet_network_probe.c").read_text()
        workflow=(BASE.parent/".github/workflows/runtime-preview.yml").read_text()
        overlay=(BASE/"overlay.py").read_text()
        for token in ("WinHttpOpen(", "WinHttpSendRequest(", "WinHttpReceiveResponse(",
                      "GetAddrInfoW(", "Process32FirstW(", "Agent.exe",
                      "phase_7_means_http_response_received"):
            self.assertIn(token, native)
        for token in ("charoite_bnet_network_probe.c",
                      "charoite_bnet_network_probe.exe", "-lwinhttp"):
            self.assertIn(token, workflow)
        self.assertIn('assets/diagnostics/charoite_bnet_network_probe.exe', overlay)
        self.assertIn('TEST WINE DNS / HTTPS / AGENT', UI)
        self.assertIn('this::runBattleNetWineNetworkProbe', UI)
        self.assertIn('public static File prepareGuestNetworkProbe(', CORE)
        self.assertIn('public static String inspectGuestNetworkProbe(', CORE)
        self.assertIn('line.matches("[a-z_0-9]{3,60}=[0-9]{1,12}")', CORE)
        self.assertIn('CharoiteBattleNetSupport.inspectGuestNetworkProbe(root)', UI)
        self.assertNotIn('Blizzard account token', native)

    def test_new_battlenet_recovery_paths(self):
        overlay = (BASE/"overlay.py").read_text()
        for token in ("locationapi=d", "WINE_SIMULATE_WRITECOPY",
                      "WINEDLLOVERRIDES"):
            self.assertIn(token, overlay)
        self.assertIn("installedDirectClient(File root)", CORE)
        self.assertIn("OPEN BATTLE.NET.EXE (DIRECT)", UI)
        self.assertIn("APPLY BROWSER ACCELERATION FIX (BACKUP)", UI)
        self.assertIn("Battle.net.config.charoite-backup-v1", CORE)
        self.assertIn('client.put("HardwareAcceleration", "false")', CORE)
        self.assertIn("inspectRecentAgentErrors(programData)", CORE)

    def test_no_false_diablo_four_dx12_guarantee(self):
        self.assertIn('Diablo IV requires DirectX 12', UI)
        self.assertIn('does not yet have verified', UI)
        self.assertIn('VKD3D', UI)
        self.assertIn('BLIZZARD', UI.upper())

if __name__ == "__main__":
    unittest.main()
