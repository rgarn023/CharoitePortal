"""Wine29 v1 kernel32 postmortem: immutable old scratch, no execution."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "CharoiteWine29V1Forensics.java"
UI = ROOT / "prepare_next.py"
WF = ROOT.parent / ".github/workflows/charoite-next.yml"

class Wine29V1ReadOnlyForensicContract(unittest.TestCase):
    def test_v1_only_no_execution_writes_cleanup_or_old_storage(self):
        s = JAVA.read_text(encoding="utf-8")
        for token in (
          'charoite-next-wine29-pe-help-v1',
          'v1-wine-pe-help.log',
          'v1-foreground-wineserver.log',
          'No Wine/Wineboot/wineserver execution',
          'getNoBackupFilesDir()',
          'MAX_PE = 2 * 1024 * 1024',
          'MAX_SERVER = 256 * 1024',
          'env=[redacted]',
          'v1 copied ',
          'pe/arm64ec/kernel32.dll',
          'pe/arm64ec/kernelbase.dll',
          'pe/arm64ec/ntdll.dll',
          'pe/arm64ec/apisetschema.dll',
          'pe/arm64/wineboot.exe',
          'MessageDigest.getInstance("SHA-256")',
          'context.getAssets().open(INDEX)',
          'status(out, scratch, "prefix/system.reg")',
          'status(out, scratch, "prefix/drive_c")',
          's.contains("load_dll")',
          's.contains("get_load_order")',
          's.contains("load_apiset_dll loaded")',
          'Wine29 PE-help remains FAILED at kernel32 c0000135'):
            with self.subTest(token=token): self.assertIn(token, s)
        for forbidden in (
          'new ProcessBuilder(', 'Runtime.getRuntime(', '.exec(', 'mkdir(',
          'mkdirs(', 'createNewFile(', '.delete(', 'deleteOnExit(',
          'FileOutputStream', 'FileWriter', '.renameTo(', 'getFilesDir(',
          'CharoiteWine29V1PeHelpProbe.run(', 'charoite-next-wine28-',
          'charoite-next-wine29-07-pe-nls', 'clearApplicationUserData'):
            self.assertNotIn(forbidden, s)

    def test_manual_button_and_apk_version(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('"CharoiteWine29V1Forensics.java"', ui)
        self.assertIn('wine29V1Forensics.setText("Inspect preserved Wine29 v1 kernel32 failure (read-only)")', ui)
        self.assertIn('CharoiteWine29V1Forensics.run(this)', ui)
        self.assertIn('nextCoreCard.addView(wine29V1Forensics);', ui)
        self.assertIn('versionCode 125', ui)
        self.assertIn('11.2-next.0.94', ui)
        before = ui.split('wine29V1Forensics.setOnClickListener(v ->', 1)[0]
        self.assertNotIn('CharoiteWine29V1Forensics.run(this)', before)

    def test_ci_attribution_and_signature_contract(self):
        wf = WF.read_text(encoding="utf-8")
        self.assertIn("test_wine29_v1_forensics_contract.py", wf)
        self.assertIn("WINE29_V1_FORENSICS_EXISTING_SCRATCH_READ_ONLY=PASS", wf)
        self.assertIn("cp next-generation/CharoiteWine29V1Forensics.java legal-bundle/CharoiteWine29V1Forensics.java", wf)
        self.assertIn("versionCode='124' versionName='11.2-next.0.94'", wf)

if __name__ == "__main__":
    unittest.main()
