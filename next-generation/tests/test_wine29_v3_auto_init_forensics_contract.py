"""Read-only v3 auto-init postmortem must never trigger Wine or touch existing data."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V3AutoInitForensics.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V3AutoInitReadOnlyContracts(unittest.TestCase):
    def test_preserved_v3_only_no_execution_mutation_or_other_scratch(self):
        required=(
            'charoite-next-wine29-pe-dir-v3',
            'v3-wine-pe-help.log',
            'v3-foreground-wineserver.log',
            'No Wine/Wineboot/wineserver execution',
            'getNoBackupFilesDir()',
            'MAX_PE = 2 * 1024 * 1024',
            'MAX_SERVER = 256 * 1024',
            'NtCreateUserProcess',
            'run_wineboot',
            'process-CREATION',
            'NOT a confirmed Wineboot process exit code',
            'run_wineboot reports the NTSTATUS',
            'status(out, scratch, "prefix/drive_c")',
            'status(out, scratch, "prefix/system.reg")',
            'status(out, scratch, "prefix/user.reg")',
            'context.getAssets().open(INDEX)',
            'MessageDigest.getInstance("SHA-256")',
            'lower.contains("env=")',
            'sanitize',
            'RESULT: PASS — v3 read-only postmortem finished; --help PASSED',
            'NEVER rerun v3'
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token if token!='sanitize' else 'scrub(', JAVA)
        for forbidden in (
            'new ProcessBuilder(', 'Runtime.getRuntime(', 'FileOutputStream',
            'FileWriter', '.exec(', 'mkdir(', 'mkdirs(', 'createNewFile(',
            'deleteOnExit(', '.delete(', '.renameTo(', 'getFilesDir(',
            'charoite-next-wine29-bootstrap-v2',
            'charoite-next-wine29-pe-help-v1',
            'CharoiteWine29V3LayoutProbe.run(',
            'clearApplicationUserData'
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,JAVA)
        self.assertNotIn('new File("/sdcard"',JAVA)
        self.assertNotIn('context.getFilesDir()',JAVA)

    def test_current_readonly_button_archives_one_shot_execution(self):
        for token in (
            '"CharoiteWine29V3AutoInitForensics.java"',
            'final boolean showArchivedWine29V3Execution = false;',
            'wine29V3Forensics.setText("Inspect preserved Wine29 v3 auto-init failure (read-only)")',
            'CharoiteWine29V3AutoInitForensics.run(this)',
            'nextCoreCard.addView(wine29V3Forensics);',
            'versionCode 116','11.2-next.0.85',
            '0xC0000135',
        ):
            with self.subTest(token=token):self.assertIn(token,UI)
        before=UI.split('wine29V3Forensics.setOnClickListener(v ->',1)[0]
        self.assertNotIn('CharoiteWine29V3AutoInitForensics.run(this)', before)

    def test_ci_identity_and_source_attribution(self):
        self.assertIn('test_wine29_v3_auto_init_forensics_contract.py',WF)
        self.assertIn('WINE29_V3_POSTMORTEM_NO_EXECUTION_OR_WRITES=PASS',WF)
        self.assertIn('cp next-generation/CharoiteWine29V3AutoInitForensics.java legal-bundle/CharoiteWine29V3AutoInitForensics.java',WF)
        self.assertIn("versionCode='116' versionName='11.2-next.0.85'", WF)

if __name__=="__main__":
    unittest.main()
