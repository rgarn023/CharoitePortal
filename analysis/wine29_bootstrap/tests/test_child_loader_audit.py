"""Fail-closed Wine29 child native loader source audit contract."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit_child_loader.py"
WORKFLOW = ROOT.parents[1] / ".github/workflows/wine29-bootstrap-source-audit.yml"

spec=importlib.util.spec_from_file_location("audit_child_loader", AUDIT)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class ChildLoaderSourceTests(unittest.TestCase):
    def test_pinned_immutable_source_identity(self):
        self.assertEqual(audit.PROCESS_SHA, "01286e119067567d1a8c7d3c8d5d61407ab43750")
        self.assertEqual(audit.PIN, "c74acb09d51b447f5d5ac56c87608d3ec565a767")
        self.assertEqual(audit.NATIVE_LOADER, "libcharoite_wine29_loader.so")
        s=AUDIT.read_text(encoding="utf-8")
        for token in ('get_new_process_info', 'WINEDLLPATH',
                      'wineloader = build_path( bin_dir, basename );',
                      'child_exec_failure_can_exit_one', 'Exact on-phone exec path',
                      'WINELOADERNOEXEC_skips_only_early_preexec_branch'):
            if token == 'WINEDLLPATH':
                # The source audit must not pretend this DLL selector also sets the executable path.
                self.assertNotIn('env.put("WINEDLLPATH",', s)
            else:
                self.assertIn(token, s)

    def test_pinned_anchors_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            audit.required('no child spawning here', {'child': 'exec_wineloader( argv, socketfd, pe_info );'})
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            audit.required('name name', {'one': 'name'})

    def test_ci_no_native_execution_or_on_phone_data_access(self):
        wf=WORKFLOW.read_text(encoding="utf-8")
        for token in ('dlls/ntdll/unix/process.c',
                      'analysis/wine29_bootstrap/audit_child_loader.py',
                      'wine29-child-loader-source-evidence.json',
                      'Wine29-Child-Native-Loader-Source-Audit-Read-Only'):
            self.assertIn(token, wf)
        s=AUDIT.read_text(encoding="utf-8")
        for forbidden in ('ProcessBuilder', 'subprocess', 'os.system',
                          'getNoBackupFilesDir', 'shutil.rmtree', 'chmod(',
                          'unlink(', 'write_text(', 'write_bytes(', 'execv('):
            # Native execv must only be inspected as a string, not called.
            if forbidden=='execv(':
                self.assertNotIn('\n    execv(',s)
            else:self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()
