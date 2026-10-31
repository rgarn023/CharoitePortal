"""Wine26 native ELF source-coherent, version-only user opt-in guardrails."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"stage_wine26_native.py").read_text(encoding="utf-8")
JAVA=(ROOT/"CharoiteWine26NativeGate.java").read_text(encoding="utf-8")
STAGE=(ROOT/"CharoiteWine26Stage.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
ENGINE=(ROOT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("wine26_native",ROOT/"stage_wine26_native.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fixtures():
    names={
        "wine":("runtime/bin/wine","libcharoite_wine26_loader.so"),
        "wineserver":("runtime/bin/wineserver","libcharoite_wine26_wineserver.so"),
        "ntdll_unix":("runtime/lib/ntdll.so","libcharoite_wine26_ntdll.so")
    }
    comps={key:{"path":source,"format":"ELF","machine":"AArch64",
                "needed":["libc.so"],"load_alignments":[16384],
                "sha256":"a"*64,"size":1024} for key,(source,_) in names.items()}
    manifest={"version":mod.ARCHIVE_VERSION,"source_commit":mod.SOURCE_COMMIT,
              "android_package":"com.charoitx","component_count":26,"nls_count":76,
              "components":comps,"launch_ready":False,"installable":False,
              "prefix_created":False,"device_tested":False,"anti_cheat_supported":False}
    raw=b"pinned entire Wine26 archive"
    index={"source_run":mod.SOURCE_RUN,"source_artifact":mod.SOURCE_ARTIFACT,
           "wine_source_sha":mod.SOURCE_COMMIT,"archive_sha256":mod.sha(raw),
           "bundle_version":mod.ARCHIVE_VERSION,"native_elf_in_archive":3}
    return manifest,index,raw

class Wine26NativeGateTests(unittest.TestCase):
    def test_evidence_requires_source_identical_three_native_elf(self):
        manifest,index,raw=fixtures()
        out=mod.validate_evidence(manifest,index,raw)
        self.assertEqual(out["archive_sha256"],mod.sha(raw))
        self.assertEqual(set(out["native_components"]),{"wine","wineserver","ntdll_unix"})
        self.assertEqual(out["stage_version"],"wine10-arm64ec-bootstrap-0.5-staged")
        for flag in ("launch_ready","wineboot_tested","prefix_created",
                     "windows_exe_executed","fex_installed","graphics_verified",
                     "anti_cheat_supported"):
            self.assertIs(out[flag],False)

    def test_mismatched_source_hashs_or_runtime_claims_are_refused(self):
        for choice in ("wrong_archive","source","run","wrong_abi","page",
                       "missing_native","deps","too_many","faked_ready"):
            manifest,index,raw=fixtures()
            if choice=="wrong_archive":index["archive_sha256"]="b"*64
            elif choice=="source":manifest["source_commit"]="wrong"
            elif choice=="run":index["source_run"]=1
            elif choice=="wrong_abi":manifest["components"]["wine"]["machine"]="x86-64"
            elif choice=="page":manifest["components"]["wine"]["load_alignments"]=[4096]
            elif choice=="missing_native":manifest["components"].pop("ntdll_unix")
            elif choice=="deps":manifest["components"]["wineserver"]["needed"]=["libwine.so"]
            elif choice=="too_many":manifest["component_count"]=22
            elif choice=="faked_ready":manifest["launch_ready"]=True
            with self.subTest(choice=choice),self.assertRaises(ValueError):
                mod.validate_evidence(manifest,index,raw)

    def test_99_file_stage_is_verified_read_only_before_native_execution(self):
        start=STAGE.index("public static String verifyOnly(Context context)")
        end=STAGE.index("public static String run(Context context)",start)
        read_only=STAGE[start:end]
        for required in ("validatedInventory(context)","if (pending.exists())",
                         "verify(complete, index.getJSONArray(\"module_files\"))",
                         "RESULT: PASS — Wine26 99-file data gate; NOT runnable"):
            self.assertIn(required,read_only)
        for forbidden in ("mkdir(","mkdirs(","renameTo(","FileOutputStream","delete(",
                          "ProcessBuilder","setExecutable("):
            self.assertNotIn(forbidden,read_only)
        first=JAVA.index("CharoiteWine26Stage.verifyOnly(context)")
        loader=JAVA.index("version(loader,nativeDir,\"wine-10.0\")")
        server=JAVA.index("version(server,nativeDir,\"Wine 10.0\")")
        self.assertLess(first,loader)
        self.assertLess(loader,server)
        for required in ("verifiedELF(nativeDir,components,\"ntdll_unix\"",
                         "source-built Wine26 and wineserver --version ONLY",
                         "new ProcessBuilder(nativeBinary.getAbsolutePath(),\"--version\")",
                         "env.clear()","TIMEOUT_SECONDS = 7L","getApplicationInfo().nativeLibraryDir",
                         "RESULT: PASS — matched Wine26 native --version gate; NOT runnable",
                         "wineboot_tested","WINE26 NATIVE"):
            if required=="WINE26 NATIVE":
                self.assertIn("WINE26 NATIVE BOOTSTRAP GATE",JAVA)
            else:self.assertIn(required,JAVA)
        for forbidden in ("deleteRecursively","clearApplicationUserData",
                          "Runtime.getRuntime().exec","ProcessBuilder(\"sh\"",
                          "new File(context.getFilesDir()","new ProcessBuilder(\"wineboot\""):
            self.assertNotIn(forbidden,JAVA)

    def test_apk_preserves_both_native_cohorts_and_provenance(self):
        for token in ("ver.verify(archive)","stage_wine26.py", "stage_native_wine_loader.py"):
            self.assertTrue(token in SCRIPT or token in WORKFLOW)
        for token in ("libcharoite_wine26_loader.so","libcharoite_wine26_ntdll.so",
                      "libcharoite_wine26_wineserver.so", "wine26-native-probe.json",
                      "doNotStrip", "CHAROITE_NEXT_WINE26_NATIVE_SOURCE_COHORT_VERIFIED=PASS"):
            self.assertIn(token,SCRIPT)
        self.assertIn("CharoiteWine26NativeGate.java",PREP)
        self.assertIn("Test matched Wine26 native startup",PREP)
        self.assertIn("versionCode 84",PREP)
        self.assertIn("11.2-next.0.53",PREP)
        self.assertIn("0.52 (Wine28 first-run builtin wineboot v9",ENGINE)
        for token in ("stage_wine26_native.py","CHAROITE_NEXT_WINE26_THREE_MATCHED_NATIVE_APK_ELF_HASHES=PASS",
                      "CHAROITE_NEXT_WINE26_NATIVE_ELF_VERSION_EXECUTION_DEVICE_ONLY=PASS",
                      "versionCode='83' versionName='11.2-next.0.53'"):
            self.assertIn(token,WORKFLOW)
if __name__=="__main__":
    unittest.main()
