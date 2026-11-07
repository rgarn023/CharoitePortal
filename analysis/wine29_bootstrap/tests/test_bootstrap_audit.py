"""Source-only Wine29 bootstrap audit guard tests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "audit_bootstrap.py"
spec = importlib.util.spec_from_file_location("audit_bootstrap", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class BootstrapSourceAuditTest(unittest.TestCase):
    def test_revision_and_source_contract(self):
        self.assertEqual(m.PIN, "c74acb09d51b447f5d5ac56c87608d3ec565a767")
        self.assertEqual(len(m.BLOBS), 3)
        text = SRC.read_text()
        for phrase in ("WINEBOOTSTRAPMODE", "WINEDLLDIR%u",
                       "builtin_fallback_requires_bootstrap",
                       "automatic_init_restores_mode",
                       "startup_null_dll_loadpath_normal",
                       "new_v2_execution_authorized"):
            self.assertIn(phrase, text)

    def test_bad_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "loader.c"
            f.write_bytes(b"not verified source")
            with self.assertRaisesRegex(ValueError, "blob SHA1"):
                m.source_text(f, "0" * 40)
        with self.assertRaisesRegex(ValueError, "source contract"):
            m.require("unrelated code", {"guard": "expected source logic"})

    def test_ci_does_not_run_wine_or_touch_phone(self):
        wf = (ROOT.parents[1] / ".github/workflows/wine29-bootstrap-source-audit.yml").read_text()
        self.assertIn("wine29-bootstrap-source-evidence.json", wf)
        self.assertIn("test_*.py", wf)
        self.assertNotIn("gradle", wf)
        self.assertNotIn("next-generation/prepare_next.py upstream", wf)
        source = SRC.read_text()
        for forbidden in ("subprocess", "os.system", "getNoBackupFilesDir",
                          "clearApplicationUserData", "shutil.rmtree", "ProcessBuilder"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
