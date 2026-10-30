"""v0.36 full, inert Wine bootstrap archive: verify provenance and avoid prefix access."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
STAGER=(ROOT/"stage_bootstrap_payload.py").read_text(encoding="utf-8")
JAVA=(ROOT/"CharoiteWinePayloadAudit.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
ENGINE=(ROOT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("payload_stage",ROOT/"stage_bootstrap_payload.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sample():
    return ({
        "version":"wine10-arm64ec-bootstrap.0.4",
        "source_commit":m.WINE_SHA,"android_package":"com.charoitx",
        "component_count":22,"nls_count":76,
        "window_imports_unresolved_count":2,
        "launch_ready":False,"installable":False,"prefix_created":False,
        "device_tested":False,"anti_cheat_supported":False,
    }, {"windows_imports_not_bundled":["a.dll","z.dll"]})

class PackagedBootstrapTest(unittest.TestCase):
    def test_immutable_archive_has_complete_manifest_and_no_readiness_claims(self):
        manifest,report=sample()
        index=m.make_index(manifest,report,b"package",b"manifest",b"review")
        self.assertEqual((index["component_count"],index["pe_component_count"],
                          index["native_component_count"],index["nls_count"]),
                         (22,19,3,76))
        self.assertEqual(index["archive_sha256"],m.digest(b"package"))
        self.assertEqual(index["archive_size"],7)
        self.assertEqual(index["source_run"],40898982875)
        self.assertEqual(index["windows_imports_not_bundled_count"],2)
        self.assertEqual(index["archive_asset"],"charoite-next/wine-bootstrap-22.bundle")
        for key in ("launch_ready","installable_as_runtime","archive_extracted",
                    "prefix_created","fex_installed","graphics_verified",
                    "device_boot_tested","anti_cheat_supported"):
            self.assertIs(index[key],False)

    def test_untrusted_source_readiness_and_manifest_drift_fail_closed(self):
        for key,value in (("source_commit","wrong"),("component_count",21),
                          ("nls_count",75),("launch_ready",True),("installable",True),
                          ("prefix_created",True),("device_tested",True)):
            manifest,report=sample()
            manifest[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                m.make_index(manifest,report,b"payload",b"manifest",b"review")
        for bad in (["z.dll","a.dll"],["a.dll","a.dll"],"a.dll"):
            manifest,report=sample()
            report["windows_imports_not_bundled"]=bad
            with self.subTest(gaps=bad),self.assertRaises(ValueError):
                m.make_index(manifest,report,b"payload",b"manifest",b"review")
        manifest,report=sample()
        with self.assertRaises(ValueError):
            m.make_index(manifest,report,b"x"*(m.MAX_BYTES+1),b"m",b"r")

    def test_readonly_phone_audit_and_verified_ci_archive(self):
        for required in ("verify-bootstrap-bundle.py","module.verify(archive)",
                         "Refusing to overwrite bundled payload",
                         "Staged bootstrap archive hash mismatch",
                         "CHAROITE_NEXT_COHERENT_WINE_ARCHIVE_PACKAGED=PASS"):
            self.assertIn(required,STAGER)
        for required in ('PACKAGE = "com.charoitx"', "MessageDigest",
                         'getAssets().open(ASSET)', "archive_sha256",
                         "archive_size", "archive_extracted",
                         "FEX, graphics, fresh prefix: NOT READY",
                         "No modules extracted or executed"):
            self.assertIn(required,JAVA)
        for prohibited in ("ProcessBuilder","Runtime.getRuntime()", "getFilesDir(",
                           "mkdirs(", "deleteRecursively", "FileOutputStream",
                           "clearApplicationUserData", "WINEPREFIX="):
            self.assertNotIn(prohibited,JAVA)
        self.assertIn("CharoiteWinePayloadAudit.java",PREP)
        self.assertIn("Verify packaged modern Wine modules",PREP)
        self.assertIn("new Thread(() ->",PREP)
        self.assertIn("versionCode 72",PREP)
        self.assertIn("11.2-next.0.41",PREP)
        self.assertIn("0.41 (isolated first-prefix Wine26 probe",ENGINE)
        self.assertIn("stage_bootstrap_payload.py",WF)
        self.assertIn("CHAROITE_NEXT_WINE_ARCHIVE_APK_SHA256_VERIFIED=PASS",WF)
        self.assertIn("versionCode='72' versionName='11.2-next.0.41'",WF)

if __name__=="__main__":
    unittest.main()
