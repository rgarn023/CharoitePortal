"""New pinned Wine29 two direct-import source candidates: safety contracts."""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"wine29-direct/build-direct.sh"
VERIFY=ROOT/"wine29-direct/verify-direct.py"
spec=importlib.util.spec_from_file_location("wine29_direct",VERIFY)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class DirectCandidates(unittest.TestCase):
    def test_pinned_targets(self):
        self.assertEqual(mod.NAMES,("propsys","wininet"))
        self.assertEqual(mod.SOURCE,mod.static.SOURCE_SHA)
        self.assertEqual(mod.GENERATION,"wine10-arm64ec-dependencies.0.10-direct-candidate")
        text=SCRIPT.read_text()
        for marker in ("propsys wininet","make -j2","--coff-imports",
                       "verify-direct.py","charoite-wine29-native-source-validation.json",
                       "WINE29_07_REAL_PE_REGULAR_IMPORT_GAP_ONLY_PROPSYS_WININET=PASS"):
            self.assertIn(marker,text)

    def test_no_phone_or_windows_exec(self):
        s=SCRIPT.read_text()
        v=VERIFY.read_text()
        for bad in ("rm -rf", "wineboot -i", "WINEPREFIX=", "adb install",
                    "shutil.rmtree"):
            self.assertNotIn(bad,s+v)
        for path in mod.FORBIDDEN:
            self.assertIn(path,s)
            self.assertIn(path,v)
        for marker in ('"launch_ready":False','"installed":False',
                       '"wineboot_executed":False','"device_tested":False',
                       '"portable_currency_equivalence_proven":False'):
            self.assertIn(marker,v)

    def test_false_runtime_claim_and_old_corpus_guards(self):
        v=VERIFY.read_text()
        for marker in ("static.analyze(archive, six, two)",
                       "hybrid.raw_coff_machine", "static.pe_imports(content)",
                       "original Wine29", "Unexpected candidate artifact entry",
                       "new_regular_import_names_not_in_33_providers",
                       "subprocess.run", "fresh_h!=h"):
            if marker!="original Wine29":
                self.assertIn(marker,v)
        with self.assertRaises(ValueError):
            mod.run("unsafe",Path("/x"),Path("/y"),Path("/z"),Path("/a"),Path("/b"))


if __name__=="__main__":
    unittest.main()
