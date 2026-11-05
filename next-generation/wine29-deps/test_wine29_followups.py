"""Source-isolated Wine29 urlmon/windowscodecs followup PE validation."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
SHELL=(ROOT/"build-wine29-followups.sh").read_text()
CHECK=(ROOT/"verify-wine29-followups.py").read_text()
FLOW=(ROOT.parent.parent/".github/workflows/wine29-07-dependency-candidates.yml").read_text()
spec=importlib.util.spec_from_file_location("wine29_next_two",ROOT/"verify-wine29-followups.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class SourceMatchedFollowups(unittest.TestCase):
    def test_modules_source_and_abi_gate(self):
        self.assertEqual(module.MODULES,("urlmon","windowscodecs"))
        self.assertEqual(module.SIX,("coml2","imm32","oleacc","oleaut32","shcore","newdev"))
        self.assertEqual(module.SOURCE,"c74acb09d51b447f5d5ac56c87608d3ec565a767")
        for s in ("urlmon windowscodecs",
                  "dlls/$name/Makefile.in",
                  "dlls/$name/aarch64-windows/$name.dll",
                  "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)",
                  "verify-wine29-deps.py", "verify-wine29-followups.py",
                  "verify-bootstrap-bundle.py",
                  "WINE29_07_NO_PHONE_STAGING_OR_WINDOWS_EXECUTION=PASS"):
            self.assertIn(s,SHELL)
    def test_static_verifier_guards_and_closure_counts(self):
        for s in ("sm.run(\"verify\",six,readobj)", "vm.verify(archive)",
                  "two_new_direct_imports_not_in_31_known_pe_files",
                  "combined_source_imports_not_in_31_known_pe_files",
                  "source_only", "Unexpected files in two-module sealed artifact",
                  "WINE29_TWO_PE_HEADERS_HASHES_AND_IMPORTS=PASS"):
            self.assertIn(s,CHECK)
        for s in ('"launch_ready":False','"phone_staged":False',
                  '"wineboot_executed":False','"windows_executed":False',
                  '"prefix_created":False'):
            self.assertIn(s,CHECK)
        for item in ("urlmon","windowscodecs"):
            self.assertIn(item,SHELL)
        self.assertIn("no Wine, Wineboot or target Windows executable is run",SHELL)
    def test_ci_separate_artifact_and_unaltered_original(self):
        self.assertIn("build-wine29-followups.sh",FLOW)
        self.assertIn("verify-wine29-followups.py",FLOW)
        self.assertIn("wine29-07-two-followups.json",FLOW)
        self.assertIn("Wine29-07-Source-Built-Urlmon-Windowscodecs-PE-Candidates",FLOW)
        self.assertIn("Wine29-07-Source-Built-Six-PE-Dependency-Candidates",FLOW)
    def test_no_phone_mutation_early_fail(self):
        for text in (SHELL,CHECK):
            for p in ("/data/data/","/data/user/","/storage/emulated/","/sdcard/"):
                self.assertIn(p,text)
        for banned in ("wineboot -i","WINEPREFIX=", "adb install", "rm -rf",
                       "ProcessBuilder", "Runtime.getRuntime()"):
            self.assertNotIn(banned,SHELL+CHECK)

if __name__=="__main__":
    unittest.main()
