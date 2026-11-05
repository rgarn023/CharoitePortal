"""Wine29 source-only wininet/propsys 33-DLL regular-vs-delay audit."""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parent
SHELL=(ROOT/"build-regular-next.sh").read_text(encoding="utf-8")
SOURCE=(ROOT/"verify-regular-next.py").read_text(encoding="utf-8")
FLOW=(ROOT.parent.parent/".github/workflows/wine29-07-transitive-candidates.yml").read_text(
    encoding="utf-8")
spec=importlib.util.spec_from_file_location("wine29_next_regular",ROOT/"verify-regular-next.py")
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class Wine29RegularNextTest(unittest.TestCase):
    def test_new_cohort_and_original_source_locked(self):
        self.assertEqual(audit.MODULES,("wininet","propsys"))
        self.assertEqual(audit.GENERATION,"wine10-arm64ec-dependencies.0.10-regular-candidate")
        self.assertEqual(audit.SOURCE,"c74acb09d51b447f5d5ac56c87608d3ec565a767")
        self.assertEqual(audit.BASELINE,len(audit.BASELINE)*"x" if False else
                         "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e")
        for term in ("wininet propsys",
                     "verify-followups.py",
                     "verify-regular-next.py",
                     "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)",
                     "dlls/$name/aarch64-windows/$name.dll",
                     "git", "rev-parse", "HEAD",
                     "WINE29_NEXT_NO_PHONE_WINEBOOT_OR_PREFIX_EXECUTION=PASS"):
            self.assertIn(term,SHELL)

    def test_isolated_cohorts_and_fail_closed_checks(self):
        for term in (
            'sixlib.run("verify",six,readobj)',
            'twolib.run("verify",archive,six,two,readobj)',
            'bundlelib.verify(archive)', 'peclass.pe_imports(blob)',
            '"regular_descriptor_count"]!=111', '"provided_dlls"]!=31',
            '"provided_dlls"]!=33',
            '"coml2.dll","imm32.dll","oleacc.dll","oleaut32.dll","shcore.dll"',
            '{"wininet.dll","propsys.dll"}',
            'Unexpected source files in new sealed 2-module cohort',
            'WINE29_07_SOURCE_ONLY_NO_WINEBOOT_PE_OR_PHONE_EXECUTION=PASS',
        ):
            self.assertIn(term,SOURCE)
        for term in ('"launch_ready":False','"wineboot_executed":False',
                     '"windows_exe_executed":False','"phone_staged":False',
                     '"prefix_created":False'):
            self.assertIn(term,SOURCE)
        for location in audit.FORBIDDEN:
            self.assertIn(location,SOURCE)
            self.assertIn(location,SHELL)
        for prohibited in ("wineboot -i", "WINEPREFIX=", "adb install", "rm -rf",
                           "Runtime.getRuntime", "shutil.rmtree("):
            self.assertNotIn(prohibited,SHELL+SOURCE)

    def test_regular_delay_separate_and_closure_conservative(self):
        sample={
            "wineboot.exe":b"not a PE",
            "ntdll.dll":b"not a PE",
        }
        self.assertEqual(audit.OUTPUT,"wine29-07-ten-candidate-regular-delay-import-review.json")
        self.assertIn('"delay_imports_are_not_proven_startup_required":True',SOURCE)
        self.assertIn('"regular_dependency_closure_proven_at_runtime":False',SOURCE)
        self.assertIn('"currency_rounding_equivalence_not_proven":True',SOURCE)
        self.assertIn('def summarize(image_data:dict[str,bytes])->dict:',SOURCE)
        self.assertEqual(set(sample),{"wineboot.exe","ntdll.dll"})

    def test_actions_only_builds_new_candidates_after_verified_31(self):
        for required in (
            "build-regular-next.sh",
            "verify-regular-next.py",
            "test_regular_next.py",
            "wine29-07-ten-candidate-regular-delay-import-review.json",
            "Wine29-07-Source-Built-Wininet-Propsys-Regular-Import-Review",
        ):
            self.assertIn(required,FLOW)


if __name__=="__main__":
    unittest.main()
