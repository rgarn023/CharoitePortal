"""Wine29 v8 short postmortem may read retained evidence but NEVER execute Wine."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V8ReadOnlyForensics.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class V8ShortReadOnlyForensics(unittest.TestCase):
    def test_only_v8_named_logs_and_metadata(self):
        for token in (
            'charoite-next-wine29-userenv-v8',
            'v8-wine-direct-init.log', 'v8-foreground-wineserver.log',
            'getNoBackupFilesDir()', 'MAX_PE_LOG = 8L * 1024L * 1024L',
            'MAX_SERVER_LOG = 8L * 1024L * 1024L',
            'MAX_REPORT_CHARS = 9000', 'MAX_LINES = 100000',
            'MAX_LINE = 16384', 'MAX_PROCESSES = 48',
            'Os.lstat(link.getAbsolutePath())', 'Os.readlink(link.getAbsolutePath())',
            'prefix/system.reg', 'prefix/user.reg', 'prefix/userdef.reg',
            'prefix/drive_c/windows', 'prefix/drive_c/users',
            'runtime/lib/wine/aarch64-windows/services.exe',
            'runtime/lib/wine/aarch64-windows/userenv.dll',
            'RESULT: READ-ONLY V8 AUDIT COMPLETE',
            'END OF SHORT V8 REPORT',
            'safeNames(String line)', 'PRESERVED REGISTRY SIZES',
            'SERVICES PE LIFECYCLE:', 'registryBytes(File scratch, String relative)',
        ):
            with self.subTest(token=token): self.assertIn(token,JAVA)

    def test_no_execution_file_writes_or_raw_trace_in_clipboard(self):
        for forbidden in (
            'new ProcessBuilder(', 'Runtime.getRuntime(', 'FileOutputStream',
            'FileWriter(', 'mkdir(', 'mkdirs(', 'delete(', 'renameTo(',
            'createNewFile(', 'getFilesDir(', 'System.load(', 'getSharedPreferences(',
            'openFileOutput(', 'clearApplicationUserData(',
            'charoite-next-wine29-services-v7',
            'charoite-next-wine29-child-loader-v6',
            'charoite-next-wine29-bootstrap-v2',
            'out.append(line)', 'out.append(peText)', 'readAllBytes()',
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,JAVA)
        self.assertNotIn('out.append(serverText)',JAVA)
        self.assertIn('contents NOT read',JAVA)
        self.assertIn('no raw log text/paths',JAVA)

    def test_current_system_only_short_readonly(self):
        for token in (
            '"CharoiteWine29V8ReadOnlyForensics.java"',
            'final boolean showArchivedWine29V8Execution = false;',
            'Inspect Wine29 v8 registry + services (read-only)',
            'CharoiteWine29V8ReadOnlyForensics.run(this)',
            'nextCoreCard.addView(wine29V8Audit);',
            'Copy short report',
            'versionCode 124', '11.2-next.0.93',
        ):
            with self.subTest(token=token): self.assertIn(token,UI)
        self.assertLess(UI.index('final boolean showArchivedWine29V8Execution = false;'),
                        UI.index('CharoiteWine29V8UserenvProbe.run(this)'))

    def test_ci_contract(self):
        for token in (
            'test_wine29_v8_short_forensics_contract.py',
            'WINE29_V8_PRESERVED_SHORT_READONLY_POSTMORTEM=PASS',
            'cp next-generation/CharoiteWine29V8ReadOnlyForensics.java legal-bundle/CharoiteWine29V8ReadOnlyForensics.java',
            "versionCode='124' versionName='11.2-next.0.93'",
        ):
            with self.subTest(token=token): self.assertIn(token,WF)

if __name__=="__main__": unittest.main()
