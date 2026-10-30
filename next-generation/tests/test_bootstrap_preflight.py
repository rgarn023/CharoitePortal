"""Source-provenance preflight: inform about bootstrap gaps without executable launch."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
STAGER=(ROOT/"stage_native_wine_loader.py").read_text()
JAVA=(ROOT/"CharoiteWineBootstrapPreflight.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
spec=importlib.util.spec_from_file_location("stager",ROOT/"stage_native_wine_loader.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample():
    return ({
        "version":"wine10-arm64ec-bootstrap.0.4",
        "source_commit":mod.WINE_SHA, "android_package":"com.charoitx",
        "component_count":22,"nls_count":76,
        "launch_ready":False,"installable":False,
        "prefix_created":False,"device_tested":False,"anti_cheat_supported":False,
        "window_imports_unresolved_count":2,
    }, {
        "windows_imports_not_bundled":["a.dll","z.dll"],
        "android_elf_needed":["libc.so","libm.so"],
    })


class BootstrapPreflightTest(unittest.TestCase):
    def test_audited_inventory_never_claims_launch_ready(self):
        m,r=sample()
        p=mod.make_preflight(m,r,b"manifest",b"review")
        self.assertEqual(p["component_count"],22)
        self.assertEqual(p["nls_count"],76)
        self.assertEqual(p["pe_imports_not_bundled"],["a.dll","z.dll"])
        self.assertEqual(p["bundle_manifest_sha256"],mod.digest(b"manifest"))
        for k in ("launch_ready","installable_as_runtime","prefix_created",
                  "fex_installed","graphics_verified","device_boot_tested",
                  "anti_cheat_supported"):
            self.assertIs(p[k],False)

    def test_rejects_unsafe_metadata_and_inconsistent_import_lists(self):
        for key,val in (("component_count",21),("nls_count",75),
                        ("source_commit","forged"),("installable",True),
                        ("launch_ready",True),("prefix_created",True)):
            m,r=sample()
            m[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):
                mod.make_preflight(m,r,b"a",b"b")
        for bad in (["z.dll","a.dll"],["a.dll","a.dll"],"a.dll"):
            m,r=sample()
            r["windows_imports_not_bundled"]=bad
            with self.subTest(value=bad),self.assertRaises(ValueError):
                mod.make_preflight(m,r,b"a",b"b")

    def test_android_report_only_and_no_prefix_side_effects(self):
        for needle in ('PACKAGE="com.charoitx"',
                       'private static final String ASSET="charoite-next/wine-bootstrap-preflight.json"',
                       'getBoolean("launch_ready")','getBoolean("fex_installed")',
                       'getBoolean("prefix_created")','NOT INSTALLED',
                       'wineboot/Windows EXE: NOT EXECUTED',
                       'Modern runner: NOT READY; launch blocked'):
            self.assertIn(needle,JAVA)
        for bad in ("ProcessBuilder", "Runtime.getRuntime()", "getFilesDir()",
                    "mkdirs(", "deleteRecursively","setExecutable(", "clearApplicationUserData"):
            self.assertNotIn(bad,JAVA)
        self.assertIn("CharoiteWineBootstrapPreflight.java",PREP)
        self.assertIn("Audit modern Wine bootstrap prerequisites",PREP)

    def test_apk_has_readonly_source_verified_evidence(self):
        self.assertIn("verifier.verify(artifact)",STAGER)
        self.assertIn("preflight_dest.exists()",STAGER)
        self.assertIn("CHAROITE_NEXT_WINE_BOOTSTRAP_PREFLIGHT_STAGED=PASS",STAGER)
        self.assertIn("wine-bootstrap-preflight.json",WF)
        self.assertIn("CHAROITE_NEXT_BOOTSTRAP_PREFLIGHT_ASSET_VERIFIED=PASS",WF)
        self.assertIn("versionCode='78' versionName='11.2-next.0.47'",WF)


if __name__=="__main__":
    unittest.main()
