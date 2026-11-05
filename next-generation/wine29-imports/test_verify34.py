"""34-DLL source-only regular PE import closure audit contracts."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
SCRIPT=ROOT/"verify34.py"
spec=importlib.util.spec_from_file_location("wine29_verify34",SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


class Wine29FullRegularClosureContracts(unittest.TestCase):
    def test_expected_static_cohort_and_runtime_disclaimer(self):
        s=SCRIPT.read_text()
        for marker in (
            "len(providers)!=34","len(images)!=35",
            "mpr.dll", "propsys", "wininet",
            "regular_unbundled_import_names", "winspool.drv",
            "cryptui.dll", "dhcpcsvc.dll",
            '"runtime_loader_closure_proven":False',
            '"wineboot_executed":False', '"launch_ready":False',
            "WINE29_07_34_DLL_PE_REGULAR_IMPORT_GRAPH_ZERO_UNBUNDLED=PASS",
        ):
            self.assertIn(marker,s)
        for bad in ("WINEPREFIX=", "wineboot -i", "adb install",
                    "rm -rf", "os.system", "Popen("):
            self.assertNotIn(bad,s)
        self.assertEqual(mod.prior.SOURCE_SHA,
                         "c74acb09d51b447f5d5ac56c87608d3ec565a767")

    def test_refuse_missing_inputs(self):
        with self.assertRaises(Exception):
            mod.inspect(Path("/wrong"),Path("/wrong"),Path("/wrong"),Path("/wrong"),Path("/wrong"))


if __name__=="__main__":
    unittest.main()
