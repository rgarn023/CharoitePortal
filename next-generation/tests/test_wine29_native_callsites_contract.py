"""Win29 read-only native call-site audit and preserved v1 trace contract."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "audit_wine29_07_native_callsites.py"
SOURCE = (ROOT / "CharoiteWine29V1Forensics.java").read_text(encoding="utf-8")
WORKFLOW = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("wine29_callsites", SCRIPT)
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)


class CallsiteContract(unittest.TestCase):
    def test_source_audit_is_pinned_and_executed_before_apk(self):
        self.assertEqual(len(AUDIT.ARCHIVE_SHA256), 64)
        self.assertEqual(len(AUDIT.PATCH_SHA256), 64)
        self.assertEqual(AUDIT.SOURCE_COMMIT, "c74acb09d51b447f5d5ac56c87608d3ec565a767")
        self.assertIn("audit_wine29_07_native_callsites.py", WORKFLOW)
        self.assertIn("wine29-native-callsite-audit.json", WORKFLOW)
        self.assertIn("Charoite-Wine29-Native-Callsite-Audit-Read-Only", WORKFLOW)
        self.assertLess(WORKFLOW.index("Audit exact Wine29 native source selector call sites"),
                        WORKFLOW.index("Stage independent Wine29 0.12 111-file sealed DATA-only assets"))
        self.assertIn("versionCode='115' versionName='11.2-next.0.84'", WORKFLOW)
        self.assertIn("versionCode 115", PREP)
        self.assertIn("11.2-next.0.84", PREP)

    def test_fails_on_incomplete_patch_without_faking_success(self):
        with self.assertRaisesRegex(ValueError, "loader source delta"):
            AUDIT.analyze_patch("unrelated patch content")
        with self.assertRaisesRegex(ValueError, "loader path expectation"):
            AUDIT.analyze_patch(
                "diff --git a/dlls/ntdll/unix/loader.c b/dlls/ntdll/unix/loader.c\n"
                "+some missing code\n")

    def test_read_only_v1_log_focus_without_new_execution(self):
        for mark in ("KERNEL32 FOCUSED TRACE", "kernelFind",
                     "lastKernelLine", "lastMissingLine",
                     "scrub(lines[i], rootPath)", "mappedKernel32",
                     "dependencies, PE machine acceptance",
                     "v1-wine-pe-help.log", "v1-foreground-wineserver.log"):
            self.assertIn(mark, SOURCE)
        for forbidden in ("new ProcessBuilder(", "FileOutputStream",
                          ".delete(", ".mkdirs(", "getFilesDir(",
                          "Runtime.getRuntime(", "CharoiteWine29V1PeHelpProbe.run("):
            self.assertNotIn(forbidden, SOURCE)


if __name__ == "__main__":
    unittest.main()
