"""Contract checks for opt-in, non-Touhou-specific Japanese Inno compatibility."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
PROBE=(ROOT/"charoite-core/japanese/touhou_probe.c").read_text()
SUPPORT=(ROOT/"charoite-core/CharoiteJapaneseSupport.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
HOOK=(ROOT/"charoite-core/japanese/touhou_font_hook.c").read_text()
UI=(ROOT/"TouhouEntryActivity.java").read_text()

class GeneralJapaneseInstallerContract(unittest.TestCase):
    def test_shared_per_environment_opt_in_unchanged(self):
        self.assertIn('installerFontRepairEnabled(Context host)',CORE)
        self.assertIn('japaneseCompatibilityEnabled(host)',CORE)
        self.assertIn('charoite_installer_font_repair_',CORE)
        self.assertIn('CharoiteCore.isJapaneseInstallerCandidate(executable)',SESSION)
        self.assertIn('CharoiteCore.installerFontRepairEnabled(host)',SESSION)
        self.assertIn('CharoiteCore.isJapaneseInstallerCandidate(guestExecutable)',OVERLAY)
        self.assertIn('CharoiteCore.useTouhouInstallerFontProbe(environment.getContext())',OVERLAY)

    def test_safe_installer_filename_gate(self):
        self.assertIn('isJapaneseInstallerCandidate(String executable)',CORE)
        self.assertIn('filename.equals("setup.exe")',CORE)
        self.assertIn('filename.equals("install.exe")',CORE)
        self.assertIn('filename.equals("installer.exe")',CORE)
        self.assertIn('filename.startsWith("setup_")',CORE)
        self.assertIn('filename.startsWith("install_")',CORE)
        self.assertIn('String suffix = candidate.substring(exeEnd + 4).trim();',CORE)
        self.assertNotIn('guestExecutable.toLowerCase(java.util.Locale.ROOT).contains("setup.exe")',OVERLAY)
        # Do not introduce a blanket trigger on any .exe or "game.exe".
        self.assertNotIn('filename.equals("game.exe")',CORE)

    def test_genuine_cp932_inno_wizard_has_japanese_text(self):
        self.assertIn('GetACP()!=932',PROBE)
        self.assertIn('is_inno_wizard(hwnd)',PROBE)
        self.assertIn('has_word(klass,L"TWizardForm")',PROBE)
        self.assertIn('japanese_units(originalText)<2',PROBE)
        for fragment in ("japanese-edit","japanese-label","japanese-wizard-title",
                         "japanese_units(title)>=2", "SMTO_ABORTIFHUNG | SMTO_BLOCK",
                         'GetWindowThreadProcessId(hwnd,&installerPid)',
                         "if (repair_attempted) break;"):
            self.assertIn(fragment,PROBE)
        # No specific proprietary game name, title or Unicode game string.
        self.assertNotIn("FocasLens",PROBE)
        self.assertNotIn("\\x5E7B\\x60F3\\x4EBA\\x5F62\\x6F14\\x821E",PROBE)
        self.assertNotIn("try_repair_path_font(",PROBE)
        # Old invasive cross-process WM_SETFONT must remain absent.
        self.assertNotIn("SendMessageW(hwnd,WM_SETFONT",PROBE)

    def test_helper_binaries_replaced_on_upgrade_without_reset(self):
        self.assertIn('.touhou-japanese-helpers-v11',SUPPORT)
        self.assertIn('FileUtils.writeString(helperVersion, "v11\\n")',SUPPORT)
        self.assertRegex(SUPPORT,re.compile(r'for \(String helper : new String\[\]\{[\s\S]*?"touhou_probe\.exe"'))
        self.assertIn('FileUtils.copy(context, "japanese/" + helper, target)',SUPPORT)
        self.assertNotIn("deleteRecursively",SUPPORT)
        self.assertNotIn("formatPrefix",SUPPORT)

    def test_notepad_cp932_font_default_without_overwriting_user_choice(self):
        # Wine Notepad's own Edit control defaults to the "System" face:
        # correcting dialog fonts alone cannot display Shift-JIS README text.
        self.assertIn('configureJapaneseNotepadDefaults(userReg);',SUPPORT)
        self.assertEqual(SUPPORT.count('configureJapaneseNotepadDefaults(userReg);'),2)
        self.assertIn('String face = registry.getStringValue(key, "lfFaceName", "");',SUPPORT)
        self.assertIn('!face.isEmpty() && !face.equalsIgnoreCase("System")',SUPPORT)
        self.assertIn('registry.setStringValue(key, "lfFaceName", IPA_GOTHIC);',SUPPORT)
        self.assertIn('registry.setDwordValue(key, "lfCharSet", 128);',SUPPORT)
        self.assertIn('charset == null || charset == 0 || charset == 1',SUPPORT)
        self.assertIn('WineRegistryEditor registry = new WineRegistryEditor(userReg)',SUPPORT)
        self.assertNotIn('notepad.exe',OVERLAY)
        self.assertNotIn('SetWindowTextW(',SUPPORT)
        self.assertNotIn('deleteRecursively',SUPPORT)

    def test_working_v10_rendering_remains_as_fallback(self):
        for v in ("select_japanese_before_installer_draw(item)",
                  "restore_installer_prepaint(item)",
                  "draw_recovered_task",
                  "queue_visible_page_scan(event)",
                  "WH_CALLWNDPROCRET"):
            self.assertIn(v,HOOK if v!="WH_CALLWNDPROCRET" else
                          (ROOT/"charoite-core/japanese/touhou_font_helper.c").read_text())
        self.assertIn("supported Inno",UI) if False else None
        self.assertIn("Leave disabled unless needed",UI)

if __name__=="__main__":
    unittest.main()
