"""Fail-closed preparation for a FUTURE, separately pinned 26-component Wine APK.

These tests do not require source compilation, download an archive, or touch
existing Android apps, games or prefixes.
"""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"prepare_security_expansion.py").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("wine_security_expand",ROOT/"prepare_security_expansion.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def inventory():
    old={}
    for name in ("wine","wineserver","ntdll_unix"):
        old[name]={"path":f"runtime/bin/{name}","format":"ELF","sha256":"a"*64,"size":128}
    for i in range(18):
        name=f"pe{i:02d}"
        old[name]={"path":f"runtime/pe/arm64ec/{name}.dll","format":"PE",
                   "machine":"0xA641","sha256":"b"*64,"size":100}
    old["wineboot"]={"path":"runtime/pe/arm64/wineboot.exe",
                     "format":"PE","machine":"0xAA64","sha256":"c"*64,"size":101}
    assert len(old)==22
    added={n:{"path":f"runtime/pe/arm64ec/{n}.dll","format":"PE",
              "machine":"0xA641","sha256":"d"*64,"size":200}
           for n in m.NAMES}
    base={"version":m.BASE_VERSION,"source_commit":m.SOURCE,
          "android_package":"com.charoitx","component_count":22,"nls_count":76,
          "components":old,"source_files":{"COPYING.LIB":{"sha256":"e"*64}},
          "nls_files":{"c_932.nls":{"sha256":"f"*64}},
          "startup_dependency_manifest_sha256":"1"*64,
          "com_dependency_manifest_sha256":"2"*64,
          "launch_ready":False,"installable":False,"prefix_created":False,
          "device_tested":False,"anti_cheat_supported":False}
    new={**copy.deepcopy(base),"version":m.NEW_VERSION,"component_count":26,
         "components":{**copy.deepcopy(old),**added},
         "services_dependency_manifest_sha256":"3"*64,
         "window_imports_unresolved_count":2}
    return base,new,{"windows_imports_not_bundled":["dnsapi.dll","wintrust.dll"]}

class SecurityExpansionContract(unittest.TestCase):
    def test_only_four_same_source_arm64ec_pe_files(self):
        old,new,review=inventory()
        idx=m.make_index(old,new,review,b"old pinned archive",
                         b"new source archive",41122222222,13009999999)
        self.assertEqual((idx["base_components"],idx["extended_components"],idx["nls_count"]),(22,26,76))
        self.assertEqual(idx["added_pe_count"],4)
        self.assertEqual([f["name"] for f in idx["added_files"]],list(m.NAMES))
        self.assertEqual(idx["remaining_observed_pe_imports_count"],2)
        self.assertEqual(idx["base_archive_sha256"],m.digest(b"old pinned archive"))
        self.assertEqual(idx["source_run"],41122222222)
        self.assertEqual(idx["source_artifact"],13009999999)
        for flag in ("launch_ready","prefix_created","wineboot_tested","native_elf_added",
                     "fex_installed","graphics_verified","anti_cheat_supported"):
            self.assertIs(idx[flag],False)

    def test_mixed_or_replaced_baseline_refused(self):
        for kind in ("ntdll-change","nls-change","source-change","extra-pe",
                     "missing-pe","wrong-abi","forged-ready","wrong-source",
                     "missing-source-audit","wrong-import-count"):
            old,new,report=inventory()
            if kind=="ntdll-change":new["components"]["ntdll_unix"]["sha256"]="0"*64
            if kind=="nls-change":new["nls_files"]={}
            if kind=="source-change":new["source_files"]={}
            if kind=="extra-pe":new["components"]["fake"]={"sha256":"1"*64}
            if kind=="missing-pe":new["components"].pop("bcrypt")
            if kind=="wrong-abi":new["components"]["secur32"]["machine"]="0x8664"
            if kind=="forged-ready":new["launch_ready"]=True
            if kind=="wrong-source":new["source_commit"]="not the pinned Wine source"
            if kind=="missing-source-audit":new["services_dependency_manifest_sha256"]=None
            if kind=="wrong-import-count":new["window_imports_unresolved_count"]=3
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                m.make_index(old,new,report,b"old",b"new",41122222222,13009999999)

    def test_device_data_never_mutated_or_executed(self):
        for token in ("verifier()","v.verify(old_archive)","v.verify(new_archive)",
                      'digest(existing.read_bytes())',
                      "Refusing to overwrite Wine extension assets",
                      "getmember(entry[\"source\"])",
                      "CHAROITE_NEXT_SECURITY_ADDON_SOURCE_MATCH_VERIFIED=PASS"):
            self.assertIn(token,SOURCE)
        for forbidden in ("subprocess","adb install","ProcessBuilder","wineboot --init",
                          "WINEPREFIX=","getFilesDir", "deleteRecursively"):
            self.assertNotIn(forbidden,SOURCE)

if __name__=="__main__":
    unittest.main()
