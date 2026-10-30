"""Next v0.39 full 26-component source-coherent Wine data generation contract."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"stage_wine26.py").read_text(encoding="utf-8")
JAVA=(ROOT/"CharoiteWine26Stage.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
ENGINE=(ROOT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("stage_full26",ROOT/"stage_wine26.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sample():
    components={}
    for name in ("wine","wineserver","ntdll_unix"):
        components[name]={"path":f"runtime/bin/{name}",
                          "format":"ELF","size":256,"sha256":"a"*64}
    for i in range(18):
        name=f"p{i:02d}"
        components[name]={"path":f"runtime/pe/arm64ec/{name}.dll",
                          "format":"PE","machine":"0xA641",
                          "size":100+i,"sha256":"b"*64}
    for name in ("bcrypt","msvcrt","sechost","secur32"):
        components[name]={"path":f"runtime/pe/arm64ec/{name}.dll",
                          "format":"PE","machine":"0xA641",
                          "size":220,"sha256":"d"*64}
    components["wineboot"]={"path":"runtime/pe/arm64/wineboot.exe",
                             "format":"PE","size":102,"sha256":"c"*64}
    nls={f"n_{i:02d}.nls":{"path":f"runtime/nls/n_{i:02d}.nls",
                         "size":10+i,"sha256":"d"*64} for i in range(76)}
    source={"charoite-source-delta.patch":{"path":"source/charoite-source-delta.patch","sha256":"e"*64}}
    old={"version":"wine10-arm64ec-bootstrap.0.4",
         "source_commit":m.SOURCE,"source_files":source}
    new={"version":m.VERSION,"source_commit":m.SOURCE,"android_package":"com.charoitx",
         "component_count":26,"nls_count":76,"components":components,"nls_files":nls,
         "source_files":source,"window_imports_unresolved_count":20,
         "launch_ready":False,"installable":False,"prefix_created":False,
         "device_tested":False,"anti_cheat_supported":False}
    gaps=sorted(f"missing{i:02d}.dll" for i in range(20))
    return old,new,{"windows_imports_not_bundled":gaps}

class Wine26GenerationContract(unittest.TestCase):
    def test_full_generation_has_99_individually_source_hashed_windows_data_files(self):
        old,new,review=sample()
        idx=m.make_index(new,review,b"audited source archive",old)
        self.assertEqual((idx["component_count"],idx["pe_count"],idx["nls_count"]),(26,23,76))
        self.assertEqual(len(idx["module_files"]),99)
        self.assertEqual(len({x["asset"] for x in idx["module_files"]}),99)
        self.assertEqual(idx["source_run"],41121328663)
        self.assertEqual(idx["source_artifact"],13009171257)
        self.assertEqual(idx["archive_sha256"],m.sha(b"audited source archive"))
        self.assertEqual(idx["remaining_observed_pe_imports_count"],20)
        self.assertFalse(any(item["source"].startswith("runtime/bin/") for item in idx["module_files"]))
        for flag in ("launch_ready","installable_as_runtime","native_elf_installed",
                     "prefix_created","wineboot_tested","fex_installed",
                     "graphics_verified","anti_cheat_supported"):
            self.assertIs(idx[flag],False)

    def test_rejects_wrong_source_invalid_imports_or_forged_readiness(self):
        for kind in ("source","version","sourcefiles","added","elf","exe","num","gap",
                     "ready","dup","oversize"):
            old,new,review=sample()
            if kind=="source":new["source_commit"]="wrong"
            if kind=="version":new["version"]="wine10-arm64ec-bootstrap.0.4"
            if kind=="sourcefiles":new["source_files"]={}
            if kind=="added":new["components"].pop("p17")
            if kind=="elf":new["components"]["p17"]["format"]="ELF"
            if kind=="exe":new["components"]["p17"]["path"]="runtime/bin/evil.exe"
            if kind=="num":new["component_count"]=22
            if kind=="gap":new["window_imports_unresolved_count"]=19
            if kind=="ready":new["launch_ready"]=True
            if kind=="dup":new["components"]["p17"]["path"]=new["components"]["p16"]["path"]
            if kind=="oversize":new["components"]["p17"]["size"]=m.MAX_MODULE+1
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                m.make_index(new,review,b"audited source archive",old)

    def test_isolated_device_data_uses_no_executable_files_or_previous_game_storage(self):
        for must in ("ver.verify(archive)","ver.verify(old_archive)",
                     "old_manifest.get(\"source_files\")!=manifest.get(\"source_files\")",
                     "wine-bootstrap-26.bundle","Refusing to overwrite an existing Wine generation",
                     "CHAROITE_NEXT_WINE26_99_PE_NLS_DATA_FILES=PASS"):
            self.assertIn(must,SCRIPT)
        for must in ('"com.charoitx"',"getNoBackupFilesDir()",
                     "wine10-arm64ec-bootstrap-0.5-staged",
                     "Wine26 full source archive SHA-256 mismatch",
                     "archiveAudit(context,index)","pending.renameTo(complete)",
                     "Windows PE data: 23/23 staged and verified",
                     "Wine NLS data: 76/76 staged and verified",
                     "RESULT: PASS — source-coherent Wine26 data staged; NOT runnable"):
            self.assertIn(must,JAVA)
        for forbidden in ("ProcessBuilder","Runtime.getRuntime()","deleteRecursively",
                          "clearApplicationUserData","WINEPREFIX=","setExecutable(true)"):
            self.assertNotIn(forbidden,JAVA)
        self.assertIn("CharoiteWine26Stage.java",PREP)
        self.assertIn("Stage expanded Wine 26-module data",PREP)
        self.assertIn("versionCode 70",PREP)
        self.assertIn("11.2-next.0.39",PREP)
        self.assertIn("0.39 (separate source-coherent Wine26 PE/NLS data",ENGINE)
        self.assertIn("stage_wine26.py",WORKFLOW)
        self.assertIn("CHAROITE_NEXT_WINE26_99_PE_NLS_APK_ASSETS_VERIFIED=PASS",WORKFLOW)
        self.assertIn("versionCode='70' versionName='11.2-next.0.39'",WORKFLOW)

if __name__=="__main__":
    unittest.main()
