"""Next v0.37: PE/NLS staging has strict provenance and no runnable native binaries."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEXER = (ROOT/"stage_bootstrap_payload.py").read_text(encoding="utf-8")
ANDROID = (ROOT/"CharoiteWineIsolatedStage.java").read_text(encoding="utf-8")
PREP = (ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("stage_index", ROOT/"stage_bootstrap_payload.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def audited():
    components = {}
    for i in range(18):
        name=f"pe{i:02d}"
        components[name] = {
            "path": f"runtime/pe/arm64ec/{name}.dll", "format": "PE",
            "size": 101+i, "sha256": "a"*64
        }
    components["wineboot"] = {"path":"runtime/pe/arm64/wineboot.exe",
                               "format":"PE","size":400,"sha256":"b"*64}
    components["wine"] = {"path":"runtime/bin/wine","format":"ELF",
                           "size":100,"sha256":"c"*64}
    nls = {f"n{i:02d}.nls":{"path":f"runtime/nls/n{i:02d}.nls",
                            "size":10+i,"sha256":"d"*64} for i in range(76)}
    return {"components":components,"nls_files":nls}

class IsolatedStagingContract(unittest.TestCase):
    def test_only_19_windows_pe_and_76_nls_files_staged(self):
        idx = mod.make_module_index(audited(), "e"*64)
        self.assertEqual(idx["file_count"],95)
        self.assertEqual(len(idx["files"]),95)
        self.assertEqual((idx["pe_count"],idx["nls_count"]),(19,76))
        self.assertNotIn("runtime/bin/wine", [f["source"] for f in idx["files"]])
        self.assertEqual(idx["files"],sorted(idx["files"],key=lambda f:f["path"]))
        self.assertTrue(all(f["asset"].endswith(".bin") for f in idx["files"]))
        self.assertFalse(any(f["path"].startswith("../") for f in idx["files"]))
        for flag in ("launch_ready","native_elf_installed","prefix_created",
                     "wineboot_tested","anti_cheat_supported"):
            self.assertIs(idx[flag],False)

    def test_rejects_renamed_traversal_duplicated_or_oversized_entries(self):
        for invalid in ("runtime/pe/arm64ec/../../escape.dll",
                        "runtime/pe/x86_64/ntdll.dll",
                        "runtime/bin/wine",
                        "runtime/nls/evil.dll"):
            m=audited()
            m["components"]["pe00"]["path"]=invalid
            with self.subTest(path=invalid),self.assertRaises(ValueError):
                mod.make_module_index(m,"e"*64)
        m=audited()
        m["components"]["pe01"]["path"]=m["components"]["pe00"]["path"]
        with self.assertRaises(ValueError):
            mod.make_module_index(m,"e"*64)
        m=audited()
        m["nls_files"]["n00.nls"]["size"]=mod.MAX_MODULE_BYTES+1
        with self.assertRaises(ValueError):
            mod.make_module_index(m,"e"*64)

    def test_android_stage_is_opt_in_atomic_and_never_executes(self):
        for x in ('"com.charoitx"','getNoBackupFilesDir()',
                  'CharoiteWinePayloadAudit.report(context)',
                  'verifiedPath(String relative)','getCanonicalFile()',
                  'MessageDigest.getInstance("SHA-256")',
                  'pending.renameTo(complete)',
                  'hashMatches(target, entry.getLong("size")',
                  'if (pending.exists())',
                  'getBoolean("launch_ready")',
                  'getBoolean("native_elf_installed")',
                  "RESULT: PASS — isolated source-built data staged; NOT runnable"):
            self.assertIn(x,ANDROID)
        for forbidden in ("ProcessBuilder","Runtime.getRuntime()",
                          "deleteRecursively","clearApplicationUserData",
                          "rootfs/","WINEPREFIX=","setExecutable(true)"):
            self.assertNotIn(forbidden,ANDROID)
        self.assertIn("CharoiteWineIsolatedStage.java",PREP)
        self.assertIn("Stage isolated modern Wine PE/NLS modules",PREP)
        self.assertIn('.setPositiveButton("Stage / Verify"',PREP)
        self.assertIn("versionCode 75",PREP)
        self.assertIn("11.2-next.0.44",PREP)
        self.assertIn("CHAROITE_NEXT_95_ISOLATED_PE_NLS_ASSETS_VERIFIED=PASS",WF)
        self.assertIn("versionCode='75' versionName='11.2-next.0.44'",WF)

if __name__=="__main__":
    unittest.main()
