"""Isolated Wine29 MPR source-only continuation safety contracts."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SHELL=(ROOT/"wine29-direct/build-mpr.sh").read_text()
CHECK=(ROOT/"wine29-direct/verify-mpr.py").read_text()
spec=importlib.util.spec_from_file_location("wine29_mpr",ROOT/"wine29-direct/verify-mpr.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Wine29MPRContracts(unittest.TestCase):
    def test_source_only_direct_import_target(self):
        self.assertEqual(mod.GENERATION,"wine10-arm64ec-dependencies.0.11-mpr-candidate")
        for marker in ("dlls/mpr/Makefile.in","make -j2","--file-headers",
                       "--coff-imports","verify-direct.py","verify-mpr.py",
                       "WINE29_07_SOURCE_ONLY_MPR_CANDIDATE_BUILD=PASS"):
            self.assertIn(marker,SHELL)
        for marker in ('"first_33_regular_gap":["mpr.dll"]',
                       '["mpr.dll"]','source_only','"launch_ready":False',
                       '"installed":False','"wineboot_executed":False',
                       '"device_tested":False'):
            self.assertIn(marker,CHECK)

    def test_fail_closed_and_no_phone_touch(self):
        for unsafe in ("wineboot -i","WINEPREFIX=","adb install","rm -rf"):
            self.assertNotIn(unsafe,SHELL+CHECK)
        for forbidden in ("/data/data/","/data/user/","/storage/emulated/","/sdcard/"):
            self.assertIn(forbidden,SHELL)
        with self.assertRaises(ValueError):
            mod.verify("unsupported",Path("/a"),Path("/b"),Path("/c"),
                       Path("/d"),Path("/e"),Path("/f"))


if __name__=="__main__":
    unittest.main()
