"""V7 services.exe preserved audit must be strictly read-only and bounded."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V7ReadOnlyForensics.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class V7PreservedServicesAudit(unittest.TestCase):
    def test_only_fixed_v7_files_and_metadata(self):
        for required in (
            'charoite-next-wine29-services-v7',
            'v7-wine-direct-init.log', 'v7-foreground-wineserver.log',
            'getNoBackupFilesDir()', 'MAX_PE_LOG = 2L * 1024L * 1024L',
            'MAX_SERVER_LOG = 2L * 1024L * 1024L',
            'MAX_LINE = 16384', 'MAX_PROCESSES = 48',
            'prefix/dosdevices/c:', 'Os.lstat(f.getAbsolutePath())',
            'Os.readlink(f.getAbsolutePath())',
            'prefix/drive_c/windows', 'prefix/drive_c/users',
            'prefix/drive_c/Program Files',
            'prefix/system.reg', 'prefix/user.reg', 'prefix/userdef.reg',
            'runtime/lib/wine/aarch64-windows/services.exe',
            'runtime/lib/wine/aarch64-windows/wineboot.exe',
            'Only TWO fixed v7 log names',
            'RESULT: READ-ONLY V7 AUDIT FINISHED',
        ):
            with self.subTest(required=required):
                self.assertIn(required, JAVA)

    def test_no_process_io_writes_old_generations_or_dump_raw_logs(self):
        for forbidden in (
            'new ProcessBuilder(', 'Runtime.getRuntime(', 'FileOutputStream',
            'FileWriter(', 'FileChannel.open(', 'mkdir(', 'mkdirs(',
            'delete(', 'renameTo(', 'createNewFile(', 'getFilesDir(',
            'System.load(', 'getSharedPreferences(', 'openFileOutput(',
            'charoite-next-wine29-child-loader-v6',
            'charoite-next-wine29-c-drive-v5',
            'charoite-next-wine29-direct-init-v4',
            'charoite-next-wine29-pe-dir-v3',
            'charoite-next-wine29-bootstrap-v2',
            'clearApplicationUserData(',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, JAVA)
        self.assertNotIn('out.append(line)', JAVA)
        self.assertNotIn('out.append(s)', JAVA)
        self.assertNotIn('readAllBytes()', JAVA)

    def test_service_process_correlation_is_careful(self):
        for required in (
            'PID 0x0034 DLL failure focus:',
            'PID 0x0034 failure event TYPES',
            'PID 0x0034 last DLL lookup/load TYPES',
            'safeModuleNames(String line)',
            'NOT proven missing modules',
            'services.exe process-create requests=',
            'services.exe mapped PE images=',
            'services builtin lookup failures=',
            'PE PID 0x',
            'first_exit=', 'last_exit=',
            'DLL_NOT_FOUND status mentions=',
            'Server process chronology',
            'process handshake text alone does NOT identify a services.exe child',
            'Wineboot exit 0 does NOT verify service initialization',
            'services.exe execution, ',
            'prefix initialization, graphics and Windows runtime NOT yet verified',
            'OUTSIDE 2 MiB read-only bound; contents NOT READ',
            'oversized lines skipped=',
        ):
            with self.subTest(required=required):
                self.assertIn(required, JAVA)

    def test_archive_one_shot_and_expose_current_readonly_test(self):
        for required in (
            '"CharoiteWine29V7ReadOnlyForensics.java"',
            'final boolean showArchivedWine29V7Execution = false;',
            'Inspect Wine29 v7 DLL failure (read-only)',
            'CharoiteWine29V7ReadOnlyForensics.run(this)',
            'nextCoreCard.addView(wine29V7Audit);',
            'versionCode 124', '11.2-next.0.93',
        ):
            with self.subTest(required=required):
                self.assertIn(required, UI)
        self.assertLess(UI.index('final boolean showArchivedWine29V7Execution = false;'),
                        UI.index('CharoiteWine29V7ServicesProbe.run(this)'))
        self.assertLess(UI.index('nextCoreCard.addView(wine29V7Services);'),
                        UI.index('CharoiteWine29V7ReadOnlyForensics.run(this)'))

    def test_ci_contract_signing_and_attribution(self):
        for required in (
            'test_wine29_v7_readonly_forensics_contract.py',
            'WINE29_V7_PRESERVED_READONLY_SERVICE_CORRELATION=PASS',
            'WINE29_V7_PRESERVED_DLL_FAILURE_TRIAGE=PASS',
            'cp next-generation/CharoiteWine29V7ReadOnlyForensics.java legal-bundle/CharoiteWine29V7ReadOnlyForensics.java',
            "versionCode='124' versionName='11.2-next.0.93'",
        ):
            self.assertIn(required, WF)

if __name__=="__main__":
    unittest.main()
