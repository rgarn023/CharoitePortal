"""Preserved Wine29 v6 postmortem must never execute, create or modify a prefix."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V6ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V6PreservedReadOnly(unittest.TestCase):
    def test_only_used_v6_scratch_and_known_logs(self):
        expected = (
            'charoite-next-wine29-child-loader-v6',
            'v6-wine-direct-init.log',
            'v6-foreground-wineserver.log',
            'getNoBackupFilesDir()', 'MAX_PE_LOG = 2L * 1024L * 1024L',
            'MAX_SERVER_LOG = 512L * 1024L', 'MAX_PROCESSES = 24',
            'ntcreateuserprocess', 'run_wineboot failed to start wineboot',
            'charoite_wine29_v6_child_execv_failure',
            'mapping pe file', 'load_apiset_dll loaded',
            'NtTerminateProcess', 'wineboot.exe', 'ntdll.dll',
            'apisetschema.dll', 'kernel32.dll',
            'prefix/drive_c/windows', 'prefix/drive_c/Program Files',
            'prefix/system.reg', 'prefix/user.reg', 'prefix/userdef.reg',
            'Os.lstat(link.getAbsolutePath())',
            'Os.readlink(link.getAbsolutePath())',
            'Only TWO named v6 logs and named v6 metadata paths',
            'RESULT: READ-ONLY POSTMORTEM FINISHED',
        )
        for q in expected:
            with self.subTest(required=q):
                self.assertIn(q, JAVA)

        forbidden = (
            'new ProcessBuilder(', 'Runtime.getRuntime(', 'FileOutputStream',
            'FileWriter(', 'FileChannel.open(', 'mkdir(', 'mkdirs(',
            'delete(', 'renameTo(', 'createNewFile(', 'getFilesDir(',
            'System.load(', 'getSharedPreferences(', 'openFileOutput(',
            'charoite-next-wine29-c-drive-v5',
            'charoite-next-wine29-direct-init-v4',
            'charoite-next-wine29-pe-dir-v3',
            'charoite-next-wine29-bootstrap-v2',
            'charoite-next-wine29-pe-help-v1',
            'clearApplicationUserData(',
        )
        for q in forbidden:
            with self.subTest(forbidden=q):
                self.assertNotIn(q, JAVA)

    def test_verdict_never_promotes_to_runnable_engine(self):
        self.assertIn('CHILD STARTUP CONFIRMED', JAVA)
        self.assertIn('NOT completed prefix setup or verified Windows runtime', JAVA)
        self.assertIn('exit=0 or mapping alone', JAVA)
        self.assertIn('REGISTRY', JAVA.upper())

    def test_new_helper_failure_and_long_server_line_diagnostics(self):
        for source in (
            'AUDIT_REVISION = "v3-0034-correlated-pe-server-evidence"',
            'auditNonzeroProcesses(scratch,out)',
            'STATUS_DLL_NOT_FOUND',
            '0xC0000135',
            'Nonzero exit process 0x',
            'first exit=',
            'Earliest module/load error:',
            'oversizedLines++;continue;',
            'SERVER AUDIT ONLY BLOCKED:',
            'reason: ',
            'contents NOT READ; PE audit preserved',
            'PE chronological process-create clues:',
            'PE process 0034 trace lines:',
            'Server 0034 text mentions:',
            'At most 16 bounded server clue lines',
            'Chronological clues only:',
            'explicit v3 512 KiB whole-file cap',
        ):
            with self.subTest(source=source):
                self.assertIn(source, JAVA)
        self.assertLess(JAVA.index('auditPe(scratch,out);'), JAVA.index('auditNonzeroProcesses(scratch,out);'))
        self.assertLess(JAVA.index('auditNonzeroProcesses(scratch,out);'), JAVA.index('auditServer(scratch,out);'))

    def test_old_v6_execution_archived_and_new_readonly_button(self):
        for q in (
            '"CharoiteWine29V6ReadOnlyForensics.java"',
            'final boolean showArchivedWine29V6Execution = false;',
            'wine29V6Forensics.setText("Inspect Wine29 v6 helper causal trace (read-only)")',
            'CharoiteWine29V6ReadOnlyForensics.run(this)',
            'nextCoreCard.addView(wine29V6Forensics);',
            'versionCode 118', '11.2-next.0.87',
        ):
            with self.subTest(required=q):
                self.assertIn(q, UI)
        before=UI.split('wine29V6Forensics.setOnClickListener(v ->',1)[0]
        self.assertNotIn('CharoiteWine29V6ReadOnlyForensics.run(this)',before)

    def test_workflow_and_attribution(self):
        for q in (
            'test_wine29_v6_readonly_forensics_contract.py',
            'WINE29_V6_PRESERVED_READONLY_FORENSICS=PASS',
            'cp next-generation/CharoiteWine29V6ReadOnlyForensics.java legal-bundle/CharoiteWine29V6ReadOnlyForensics.java',
            "versionCode='118' versionName='11.2-next.0.87'",
        ):
            self.assertIn(q, WF)

if __name__ == "__main__":
    unittest.main()
