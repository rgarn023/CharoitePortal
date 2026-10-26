"""Opt-in Library shortcuts with non-destructive reinstall-free recovery."""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
UI=(BASE/"TouhouEntryActivity.java").read_text()
LIB=(BASE/"charoite-core/CharoiteGameLibrary.java").read_text()
DISC=(BASE/"charoite-core/CharoiteGameDiscovery.java").read_text()
BATTLE=(BASE/"charoite-core/CharoiteBattleNetSupport.java").read_text()
SESS=(BASE/"charoite-core/CharoiteGameSessions.java").read_text()
OVERLAY=(BASE/"overlay.py").read_text()


class ShortcutConsentContract(unittest.TestCase):
    def test_scan_always_asks_before_adding(self):
        scan=UI.split('private void findInstalledGames(boolean afterInstaller)',1)[1].split('private void importGame(',1)[0]
        self.assertIn('showShortcutPicker(discovered);',scan)
        self.assertNotIn('CharoiteGameLibrary.mergeInstalled(this, discovered)',scan)
        self.assertIn('setMultiChoiceItems(labels, selected,',UI)
        self.assertIn('CharoiteGameLibrary.mergeInstalled(this, chosen)',UI)
        self.assertIn('final boolean[] selected = new boolean[available.size()]',UI)
        self.assertIn('existing.contains(path)',UI)
        self.assertIn('FIND GAMES / ADD SHORTCUTS',UI)
        self.assertIn('ADD INSTALLED GAME SHORTCUT',UI)
        self.assertIn('scan(File containerRoot,',DISC)

    def test_import_creates_game_shortcut_only_on_approval(self):
        start=UI.index('private void importGame(Uri uri')
        end=UI.index('/** All library metadata persistence lives in Core. */',start)
        import_code=UI[start:end]
        self.assertIn('if (imported.installer) saveEntry(entry);',import_code)
        self.assertIn('.setPositiveButton("Add shortcut"',import_code)
        self.assertIn('CharoiteGameLibrary.save(this, entry);',import_code)
        self.assertIn('.setNegativeButton("Not now", null)',import_code)

    def test_bulk_cleanup_only_removes_metadata(self):
        self.assertIn('public static synchronized int clearGameShortcuts(',LIB)
        portion=LIB.split('public static synchronized int clearGameShortcuts(',1)[1].split('public static JSONObject newestInstaller',1)[0]
        self.assertIn('if (entry.optBoolean("installer")) retained.put(entry)',portion)
        self.assertIn('persist(host, retained)',portion)
        self.assertNotIn('delete(',portion)
        self.assertIn('REMOVE ALL LIBRARY SHORTCUTS',UI)
        self.assertIn('this::confirmClearLibraryShortcuts',UI)
        self.assertIn('CharoiteGameLibrary.clearGameShortcuts(this)',UI)
        self.assertIn('CharoiteGameLibrary.remove(this, executable)',UI)

    def test_battlenet_agent_safe_diagnostics_and_retry(self):
        self.assertIn('public static String inspectAgent(File root)',BATTLE)
        report=BATTLE.split('public static String inspectAgent(File root)',1)[1].split('private static boolean trustedWindowsDownload',1)[0]
        self.assertIn('Agent.exe copies detected:',report)
        self.assertIn('Agent log files:',report)
        self.assertNotIn('.delete()',report)
        self.assertNotIn('Files.move(',report)
        self.assertIn('CHECK UPDATE AGENT DIAGNOSTICS',UI)
        self.assertIn('RETRY SETUP: COMPATIBILITY MODE',UI)
        self.assertIn('true, false, true)',UI)
        self.assertIn('charoite_bnet_agent_compatibility',SESS)
        self.assertIn('getBooleanExtra("charoite_bnet_agent_compatibility", false)',OVERLAY)
        self.assertIn('envVars.put("WINEESYNC", "0");',OVERLAY)
        self.assertIn('envVars.put("WINEFSYNC", "0");',OVERLAY)
        self.assertIn('dxwrapper = DXWrappers.WINED3D;',OVERLAY)


if __name__=="__main__":
    unittest.main()
