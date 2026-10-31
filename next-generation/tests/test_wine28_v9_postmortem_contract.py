"""Read-only v9 postmortem contract; no new Wine or prefix execution."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
F=(ROOT/"CharoiteWine28V9Forensics.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class Wine28V9PostmortemContract(unittest.TestCase):
    def test_reads_only_retained_v9_logs(self):
        for marker in (
            'charoite-next-wine28-pe-help-v9-builtin-boot',
            'v9-wine-pe-help.log', 'v9-foreground-wineserver.log',
            'getNoBackupFilesDir()', 'MAX_PE = 2 * 1024 * 1024',
            'MAX_SERVER = 256 * 1024',
            'No Wine/Wineboot/wineserver execution',
            'env=[redacted]', 'read-only', 'new_process()',
            'kernel32.dll', 'apisetschema.dll',
            'Wineboot remains unproven'):
            self.assertIn(marker.lower(), F.lower())
        for forbidden in (
            'new ProcessBuilder(', 'Runtime.getRuntime(', '.exec(',
            'createNewFile(', '.mkdir(', '.mkdirs(', '.delete(',
            'FileOutputStream', 'FileWriter', 'clearApplicationUserData',
            'charoite-next-wine28-pe-help-v8-layout',
            'charoite-next-wine28-pe-help-v7',
            'getFilesDir()', 'com.touhoudr'):
            self.assertNotIn(forbidden, F)
    def test_apk_hook_and_provenance(self):
        for marker in (
            '"CharoiteWine28V9Forensics.java"',
            'Inspect preserved Wine28 v9 logs (read-only)',
            'CharoiteWine28V9Forensics.run(this)',
            'versionCode 84',
            '11.2-next.0.53'):
            self.assertIn(marker, PREP)
        self.assertIn('cp next-generation/CharoiteWine28V9Forensics.java legal-bundle/CharoiteWine28V9Forensics.java', WF)
        self.assertIn("versionCode='84' versionName='11.2-next.0.53'", WF)

if __name__=="__main__":
    unittest.main()
