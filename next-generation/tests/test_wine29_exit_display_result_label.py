"""One-shot Wine29 result header must distinguish self-exit from interruption."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class DisplayExitLabelContract(unittest.TestCase):
    def test_self_exit_is_not_mislabeled_interrupted(self):
        self.assertIn('String exitDescription = describeExit(portal, recordedAt);', HOST)
        self.assertIn('exitDescription.startsWith("\\nAndroid reports process exit (status ")', HOST)
        self.assertIn('report.startsWith("Interrupted during Wine29 x64 window test;")', HOST)
        self.assertIn('report = "Wine29 x64 window test ended; Android frame checkpoints:\\n"', HOST)
        self.assertIn("report.substring(report.indexOf('\\n') + 1)", HOST)
        self.assertIn("report += exitDescription;", HOST)

    def test_missing_exit_crash_and_no_fake_success_remain_distinct(self):
        self.assertIn('"Interrupted during Wine29 x64 window test; Android frame checkpoints:\\n"', HOST)
        self.assertIn('return "\\nAndroid has no matching process-exit record yet.";', HOST)
        self.assertIn('case ApplicationExitInfo.REASON_CRASH_NATIVE: reason = "native crash";', HOST)
        for exit_code in (15, 16, 17, 42):
            self.assertIn(f'case {exit_code}: return report', HOST)
        self.assertIn("Windows dual-pixel fixture passed; Android visible frame still separate.", HOST)
        self.assertIn("file.delete();", HOST)
        self.assertNotIn("report = \"Graphics rendering successful", HOST)

if __name__ == "__main__":
    unittest.main()
