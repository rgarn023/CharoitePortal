"""Wine29 .0.7 APK-only integration: preserve old cohorts, never start Wine."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"stage_wine29_native07.py"
AUDIT=(ROOT/"CharoiteWine29Native07Audit.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("wine29_apk_stage",STAGE)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def specimen():
    manifest={
        "version":M.VERSION,"source_commit":M.SOURCE_SHA,"android_package":M.PACKAGE,
        "component_count":27,"nls_count":76,
        "wine29_native_source_delta_sha256":"a"*64,
        "wine29_native_source_proof_sha256":"b"*64,
        "launch_ready":False,"installable":False,"prefix_created":False,
        "device_tested":False,"anti_cheat_supported":False,
    }
    manifest["components"]={}
    for key,(source,_filename) in M.LIBRARIES.items():
        manifest["components"][key]={
            "path":source,"format":"ELF","machine":"AArch64",
            "load_alignments":[16384],"needed":["libc.so"],
            "size":500,"sha256":"c"*64,
        }
    for n in range(23):
        manifest["components"][f"dummy_{n}"]={
            "path":f"runtime/pe/arm64ec/dummy_{n}.dll",
            "format":"PE","machine":"0xA641","size":2048,"sha256":"d"*64
        }
    manifest["components"]["apisetschema"]={
        "path":"runtime/pe/arm64ec/apisetschema.dll","format":"PE",
        "api_set_namespace_version":6,"machine":"0xAA64","size":4096,"sha256":"e"*64
    }
    manifest["nls_files"]={f"c_{n}.nls":{} for n in range(76)}
    old={"bundle_version":"wine10-arm64ec-bootstrap.0.6",
         "source_run":41586391767,"source_artifact":13208541305,
         "module_count":100,"native_elf_installed":False,"archive_sha256":"f"*64}
    native={"source_native_cohort_verified":True,"source_generation":M.VERSION,
            "native_elf_count":3,"source_component_count":27,
            "apk_native_install_permitted":False,"wineboot_execution_permitted":False,
            "phone_runtime_verified":False}
    review={"windows_imports_not_bundled":["kernel32.dll"]}
    return manifest,review,b"verified source archive",old,native


class Wine29Native07ApkContract(unittest.TestCase):
    def test_complete_source_cohort_is_separate_from_old29(self):
        m,review,archive,older,native=specimen()
        output=M.index_for(m,review,archive,older,native)
        self.assertEqual(output["bundle_version"],M.VERSION)
        self.assertEqual(output["original_wine29_sha256"],older["archive_sha256"])
        self.assertEqual(output["component_count"],27)
        self.assertEqual(output["pe_count"],24)
        self.assertEqual(output["nls_count"],76)
        self.assertTrue(output["native_elf_installed_as_apk_libs"])
        self.assertEqual(set(output["native_components"]),set(M.LIBRARIES))
        for field in ("native_elf_executed","windows_exe_executed","wineboot_executed",
                      "launch_ready","device_tested","installable_as_runtime","prefix_created"):
            self.assertFalse(output[field])
        self.assertTrue(all("wine29_" in v["filename"] for v in output["native_components"].values()))

    def test_refuse_old_or_unverified_runtime_generation(self):
        m,review,archive,older,native=specimen()
        m["version"]="wine10-arm64ec-bootstrap.0.6"
        with self.assertRaisesRegex(ValueError,"generation"):
            M.index_for(m,review,archive,older,native)
        m["version"]=M.VERSION
        m["launch_ready"]=True
        with self.assertRaisesRegex(ValueError,"runtime readiness"):
            M.index_for(m,review,archive,older,native)
        m["launch_ready"]=False
        native["phone_runtime_verified"]=True
        with self.assertRaisesRegex(ValueError,"source-only"):
            M.index_for(m,review,archive,older,native)

    def test_reject_unsafe_native_machine_and_missing_apiset(self):
        m,review,archive,older,native=specimen()
        m["components"]["wine"]["machine"]="x86_64"
        with self.assertRaisesRegex(ValueError,"unsafe|Unsafe"):
            M.index_for(m,review,archive,older,native)
        m["components"]["wine"]["machine"]="AArch64"
        m["components"]["apisetschema"]["api_set_namespace_version"]=5
        with self.assertRaisesRegex(ValueError,"API-set"):
            M.index_for(m,review,archive,older,native)

    def test_only_read_only_java_audit_without_wine_process(self):
        self.assertIn("public final class CharoiteWine29Native07Audit",AUDIT)
        self.assertIn("Wine29 .0.7 27-component / 76-NLS",AUDIT)
        self.assertIn("original_wine29_sha256",AUDIT)
        self.assertIn("getApplicationInfo().nativeLibraryDir",AUDIT)
        for forbidden in ("ProcessBuilder(", "Runtime.getRuntime()", "FileOutputStream(",
                          "mkdirs(", "wineboot -i", "new Thread(", "exec(", "delete("):
            self.assertNotIn(forbidden,AUDIT)
        for forbidden in ("subprocess.run", "subprocess.Popen", "rm -rf", "shutil.rmtree",
                          ".unlink(", "os.system("):
            self.assertNotIn(forbidden,STAGE.read_text(encoding="utf-8"))

    def test_challenge_signed_apk_workflow_and_visible_ui(self):
        self.assertIn("41749167248",WF)
        self.assertIn("13284932342",WF)
        self.assertIn("stage_wine29_native07.py",WF)
        self.assertIn("libcharoite_wine29_",WF)
        self.assertIn("WINE29_07_PHONE_WINE_EXECUTION=NOT_ATTEMPTED",WF)
        self.assertIn("versionCode='101'",WF)
        self.assertIn("versionName='11.2-next.0.70'",WF)
        self.assertIn("CharoiteWine29Native07Audit.java",PREP)
        self.assertIn('wine29Audit.setText("Verify Wine29 0.7 package (read-only)")',PREP)
        self.assertIn('"versionCode 101"',PREP)
        self.assertIn('"11.2-next.0.70"',PREP)


if __name__=="__main__":
    unittest.main()
