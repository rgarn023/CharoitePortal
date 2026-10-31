"""Read-only PE machine/import audit of previously failed v3 files."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PE=(ROOT/"CharoiteWine27PEAudit.java").read_text()
FORENSICS=(ROOT/"CharoiteWine27V3Forensics.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()

class Wine27PEImportAuditTest(unittest.TestCase):
    def test_read_only_pe_structure_and_input_bounds(self):
        for marker in ('RandomAccessFile(file,"r")','MAX_PE = 32L * 1024 * 1024',
                       'PE32+','Raw COFF machine:', '0xa641','0xaa64',
                       'Unmapped PE import directory','Direct PE DLL import names',
                       'not in this 23-PE scratch cohort'):
            self.assertIn(marker,PE)
        for forbidden in ("ProcessBuilder", "FileOutputStream", ".delete(",
                          ".mkdir(", ".mkdirs(", "Runtime.getRuntime()",
                          "getFilesDir()", "com.touhoudr"):
            self.assertNotIn(forbidden,PE)
    def test_only_previous_v3_scratch_and_explicit_ui(self):
        self.assertIn('CharoiteWine27PEAudit.inspect(',FORENSICS)
        self.assertIn('"prefix/.wineserver"',FORENSICS)
        self.assertIn('charoite-next-wine27-first-prefix-v3',FORENSICS)
        self.assertNotIn('new ProcessBuilder(',FORENSICS)
        self.assertIn('CharoiteWine27PEAudit.java',PREP)
        self.assertIn('versionCode 79',PREP)
        self.assertIn('11.2-next.0.48',PREP)
if __name__=="__main__":
    unittest.main()
