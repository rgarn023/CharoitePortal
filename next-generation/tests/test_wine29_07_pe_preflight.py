"""Wine29 .0.7 read-only PE layout/import preflight safeguards.

This is a source contract; GitHub Actions additionally compiles the Java in the
signed Android APK. It does not claim Wineboot or PE execution on a phone.
"""
from pathlib import Path
import unittest

NEXT = Path(__file__).resolve().parents[1]
JAVA = (NEXT / "CharoiteWine29Native07PePreflight.java").read_text(encoding="utf-8")
PREP = (NEXT / "prepare_next.py").read_text(encoding="utf-8")
RUNTIME = (NEXT / "CharoiteNextRuntime.java").read_text(encoding="utf-8")
WORKFLOW = (NEXT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


class Wine29PePreflight(unittest.TestCase):
    def test_only_independently_sealed_source_may_be_inspected(self):
        for term in (
            'private static final String PACKAGE = "com.charoitx"',
            'private static final String ROOT = "charoite-next-wine29-07-pe-nls"',
            'private static final String SLOT = "wine10-arm64ec-bootstrap-0.7-pe-nls"',
            "CharoiteWine29Native07Stage.verifyOnly(context)",
            "RESULT: PASS — isolated Wine29 0.7 data-only stage; NOT RUNNABLE",
            "getNoBackupFilesDir().getCanonicalFile()",
            "getApplicationInfo().nativeLibraryDir",
            "slot.getCanonicalFile().equals(slot.getAbsoluteFile())",
            "Exactly 23",
        ):
            if term == "Exactly 23":
                self.assertIn("exactly 23 sealed ARM64EC DLLs", JAVA)
            else:
                self.assertIn(term, JAVA)

    def test_separate_source_coherent_selector_layout(self):
        for term in (
            'new File(new File(slot, "pe"), "arm64ec")',
            'new File(slot, "nls")',
            '"wineboot.exe"',
            "libcharoite_wine29_loader.so",
            "libcharoite_wine29_wineserver.so",
            "libcharoite_wine29_ntdll.so",
            '"ntdll.dll", "kernel32.dll", "apisetschema.dll"',
            "23 source-verified ARM64EC-view hybrid DLL headers PASS",
            "separate ARM64 PE32+ PASS",
            "Selectors proposed ONLY; environment variables NOT set or executed",
        ):
            self.assertIn(term, JAVA)

    def test_pe_header_and_static_import_parsing_is_bounded(self):
        for term in (
            "private static final int ARM64EC = 0xa641",
            "private static final int ARM64 = 0xaa64",
            "rawMachine == ARM64EC || rawMachine == ARM64",
            ": rawMachine == expectedMachine",
            "rawMachineCounts[rawMachine == ARM64 ? 0 : 1]++",
            "rawMachine=",
            "Raw COFF machines among 23 DLLs: AA64=",
            "ARM64EC-view hybrid (raw AA64/A641)",

            "private static final int MAX_PE = 32 * 1024 * 1024",
            "private static final int MAX_IMPORTS = 256",
            "u16(data, 0) != 0x5a4d",
            "signature != 0x00004550L",
            "optionalSize < 128",
            "u16(data, opt) != 0x20b",
            "u32(data, opt + 120)",
            "u32(data, opt + 124)",
            "rva(data, sections, sectionCount, name)",
            "Unbundled DLL names are diagnostic, not proven loader failures",
        ):
            self.assertIn(term, JAVA)

    def test_source_archive_verifier_allows_hybrid_raw_coff_header(self):
        verifier = (NEXT / "charoite-wine/verify-bootstrap-bundle.py").read_text(
            encoding="utf-8")
        assembler = (NEXT / "charoite-wine/assemble-bootstrap-bundle.py").read_text(
            encoding="utf-8")
        self.assertIn("machine not in (0xAA64,0xA641)", verifier)
        self.assertIn('entry.get("machine")!="0xA641"', verifier)
        self.assertIn('machine!=0xAA64 or entry.get("machine")!="0xAA64"', verifier)
        self.assertIn("raw DOS/COFF", assembler)
        self.assertIn("rawMachine == ARM64EC || rawMachine == ARM64", JAVA)
        self.assertIn("rawMachine == expectedMachine", JAVA)
        self.assertIn("file.getName()", JAVA)
        self.assertIn('String.format(Locale.US, "0x%04X", rawMachine)', JAVA)

    def test_no_execution_or_mutation_in_static_preflight(self):
        for forbidden in (
            "ProcessBuilder", "Runtime.getRuntime", "FileOutputStream",
            "FileWriter(", "mkdir(", "mkdirs(", ".delete(", "renameTo(",
            "WINEPREFIX", "env.put(", "System.getenv(", "setExecutable(",
            "new Thread(", "wineboot -i", "ProcessHandle",
        ):
            self.assertNotIn(forbidden, JAVA)
        self.assertIn("READ ONLY; no Wine/Wineboot/PE/wineserver execution", JAVA)
        self.assertIn("RESULT: PASS — static Wine29 PE layout/import audit; NOT RUNNABLE", JAVA)
        self.assertIn("RESULT: BLOCKED", JAVA)

    def test_manual_read_only_phone_button_and_ci_gate(self):
        self.assertIn("CharoiteWine29Native07PePreflight.java", PREP)
        self.assertIn("CharoiteWine29Native07PePreflight.run(this)", PREP)
        self.assertIn("Preflight Wine29 0.7 PE loader layout (read-only)", PREP)
        self.assertIn("setPositiveButton(\"Copy report\"", PREP)
        self.assertIn("CharoiteWine29Native07PePreflight.java", WORKFLOW)
        self.assertIn("test_wine29_07_pe_preflight.py", WORKFLOW)
        self.assertIn("WINE29_07_PE_STATIC_PREFLIGHT_NO_EXECUTION=PASS", WORKFLOW)
        self.assertIn("Experimental Wine29 v10 PE-entry diagnostic; SCM not verified", RUNTIME)
        self.assertIn("versionCode 141", PREP)
        self.assertIn("11.2-next.0.110", PREP)
        self.assertIn("versionCode='141' versionName='11.2-next.0.110'", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
