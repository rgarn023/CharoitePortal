"""Source-only user-initiated copy of a full, bounded Wine29 window report."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WINE = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")
SCREEN = (ROOT / "next-generation/prepare_next.py").read_text(encoding="utf-8")


class Wine29CopyReportContract(unittest.TestCase):
    def test_result_dialog_has_direct_copy_action(self):
        start = WINE.index("public static void showLastCheck(Activity portal)")
        end = WINE.index("private static String describeExit(", start)
        dialog = WINE[start:end]
        self.assertIn("report += exitDescription;", dialog)
        self.assertIn("saveLastWindowReport(portal, report);", dialog)
        self.assertLess(dialog.index("saveLastWindowReport("), dialog.index("file.delete();"))
        self.assertIn('.setPositiveButton("Copy report", (dialog, which) ->', dialog)
        self.assertIn("copyCompleteWindowReport(portal, displayedReport)", dialog)
        self.assertIn('.setNegativeButton("Close", null)', dialog)
        self.assertIn('report.startsWith("Interrupted during Wine29 x64 window test;")', dialog)
        self.assertIn('report = "Wine29 x64 window test ended; Android frame checkpoints:', dialog)

    def test_system_copy_is_available_after_dialog_closes(self):
        self.assertIn('copyWindowReport.setText("Copy last Wine29 test report")', SCREEN)
        self.assertIn("org.winehq.wine.WineActivity.copyLastWindowReport(this)", SCREEN)
        self.assertIn('new File(context.getFilesDir(), "wine29-display-last-report.txt")', WINE)
        self.assertIn("return new String(file.readFully(), StandardCharsets.UTF_8);", WINE)
        self.assertIn("saveLastWindowReport(portal, report);", WINE)
        self.assertIn("String report = loadLastWindowReport(portal);", WINE)
        self.assertIn("Do not rerun consumed one-shot tests.", WINE)
        self.assertIn("file.delete();", WINE)

    def test_full_report_contains_result_exits_frame_and_bounded_native_log(self):
        self.assertIn("Display result and Android frame checkpoints:", WINE)
        self.assertIn("report.append(displayResult).append(", WINE)
        self.assertIn("Bounded native Wine29 window log (last 16 KiB, paths redacted):", WINE)
        self.assertIn("report.append(readWindowLog(portal));", WINE)
        self.assertIn("long size = input.length();", WINE)
        self.assertIn("Math.min(size, 16384L)", WINE)
        self.assertIn("input.seek(size - tail.length);", WINE)
        self.assertIn('for (int version = 23; version >= 1; version--)', WINE)
        self.assertIn("if (!log.isFile() || !log.getCanonicalFile().equals(log.getAbsoluteFile()))", WINE)
        self.assertIn('new File(portal.getNoBackupFilesDir(),', WINE)
        for status in (15, 16, 17, 42):
            self.assertIn(f"case {status}: return report", WINE)
        self.assertIn("Android presentation VERIFIED:", WINE)
        self.assertIn("Win32 screen-DC readback is a separate gate.", WINE)

    def test_bounded_storage_and_no_automatic_clipboard_mutations(self):
        self.assertIn("if (bytes.length > 32768)", WINE)
        self.assertIn("file.getBaseFile().length() > 32768", WINE)
        self.assertIn("file.startWrite()", WINE)
        self.assertIn("file.finishWrite(output);", WINE)
        self.assertIn("file.failWrite(output);", WINE)
        self.assertIn("clipboard.setPrimaryClip(", WINE)
        self.assertIn('"Wine29 complete display report"', WINE)
        self.assertIn('android.widget.Toast.makeText(portal, "Wine29 report copied"', WINE)
        # New complete clipboard write is triggered only by a real user control.
        start = WINE.index("private static void copyCompleteWindowReport(")
        end = WINE.index("public static void copyLastWindowReport(", start)
        copy = WINE[start:end]
        self.assertIn("clipboard.setPrimaryClip", copy)
        self.assertNotIn("copyCompleteWindowReport(portal", WINE[:start])
        self.assertNotIn("MediaStore.", WINE)
        self.assertNotIn("bitmap.compress(", WINE)
        self.assertNotIn("getExternalStorageDirectory(", WINE)


if __name__ == "__main__":
    unittest.main()
