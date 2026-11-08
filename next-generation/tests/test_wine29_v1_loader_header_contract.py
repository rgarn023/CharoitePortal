"""V0.73: bounded, source-gated PE metadata inspection of existing Wine29 v1 only."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "CharoiteWine29V1Forensics.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
DOC = (ROOT.parent / "docs/CHAROITE_PORTAL_UNIFICATION.md").read_text(encoding="utf-8")
AUDIT = (ROOT.parent / "docs/WINE29_KERNEL32_LOADER_AUDIT.md").read_text(encoding="utf-8")

class Wine29V1LoaderHeaderContract(unittest.TestCase):
    def test_bounded_read_only_hash_gate(self):
        for value in (
            'private static void inspectPeHeader(',
            'new RandomAccessFile(file, "r")',
            'Math.min(4096, file.length())',
            'if (verified) inspectPeHeader(copy, label, out);',
            'boolean verified = hex.toString().equals(record.getString("sha256"))',
            'mappedKernel32=',
            'Expected v1 WINEDLLPATH root: runtime/lib/wine',
            'ARM64EC hybrid support, or a successful Wineboot',
            'v1-wine-pe-help.log', 'v1-foreground-wineserver.log'
        ):
            with self.subTest(value=value):
                self.assertIn(value, SRC)
        for unsafe in ('new ProcessBuilder(', '.exec(', 'FileOutputStream',
                       '.mkdir(', '.mkdirs(', '.delete(', '.renameTo(',
                       'Runtime.getRuntime(', 'getFilesDir('):
            self.assertNotIn(unsafe, SRC)

    def test_future_portal_roadmap_and_separate_package_id(self):
        self.assertIn('Charoite Portal', DOC)
        self.assertIn('com.charoite', DOC)
        self.assertIn('com.charoitx', DOC)
        self.assertIn('user-initiated', DOC)
        self.assertIn('root cause unresolved', AUDIT)
        self.assertIn('versionCode 134', PREP)
        self.assertIn('11.2-next.0.103', PREP)

if __name__ == "__main__":
    unittest.main()
